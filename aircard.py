#!/usr/bin/env python3
"""
AirCard — Apple Wallet Card Skinner (via airlift exploit).
Customizes Apple Pay and Wallet card skins without a jailbreak.
"""

from __future__ import annotations

import io
import json
import os
import posixpath
import re
import secrets
import shutil
import subprocess
import sys
import time
import tempfile
from pathlib import Path

# Ensure bundled and standard bin paths are in PATH
script_dir = Path(__file__).resolve().parent
for bin_path in [
    str(script_dir / "bin"),
    "/Applications/AirCard.app/Contents/Resources/bin",
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin"
]:
    if os.path.isdir(bin_path) and bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"

from apply_card_skin import (
    native,
    operation_ok,
    write_file,
    ROOT,
    DEVICE_HELPER,
)

TARGET_ASSETS = [
    "cardBackgroundCombined@3x.png",
    "cardBackgroundCombined@2x.png",
    "cardBackgroundCombined.pdf",
]

CACHE_FILES = ["FrontFace", "PlaceHolder", "Preview"]

CARDS_STORE_PATH = Path.home() / ".aircard_cards.json"
LEGACY_STORE_PATH = Path.home() / ".lumicards_cards.json"
PREDEFINED_CARDS = []

CARD_REGEXES = [
    re.compile(r"/(?:Cards|Passes/Cards)/([-A-Za-z0-9_+=]{20,44})(?:\.pkpass|\.cache|\.pkcache|/|\s|\"|\'|\)|,|$)"),
    re.compile(r"/([-A-Za-z0-9_+=]{20,44})\.(?:pkpass|cache|pkcache)"),
    re.compile(r"(?<![A-Za-z0-9+/_-])([A-Za-z0-9+/_-]{27}=)(?![A-Za-z0-9+/_-])"),
]


def load_saved_cards() -> list[str]:
    """Loads saved card hashes from local storage."""
    for store in [CARDS_STORE_PATH, LEGACY_STORE_PATH]:
        if store.is_file():
            try:
                data = json.loads(store.read_text("utf-8"))
                if isinstance(data, list) and data:
                    return data
            except Exception:
                pass
    return list(PREDEFINED_CARDS)


def save_cards(cards: list[str]):
    """Saves unique card hashes to local storage."""
    try:
        unique = list(dict.fromkeys(cards))
        CARDS_STORE_PATH.write_text(json.dumps(unique, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_connected_device() -> dict | None:
    """Finds connected iPhone via ideviceinfo."""
    candidates = [
        str(Path(__file__).resolve().parent / "bin" / "ideviceinfo"),
        "/Applications/AirCard.app/Contents/Resources/bin/ideviceinfo",
        shutil.which("ideviceinfo"),
        "/opt/homebrew/bin/ideviceinfo",
        "/usr/local/bin/ideviceinfo",
    ]
    bin_cmd = "ideviceinfo"
    for c in candidates:
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            bin_cmd = c
            break

    try:
        output = subprocess.check_output(
            [bin_cmd, "-s"], text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return None

    info = {}
    for line in output.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()

    udid = info.get("UniqueDeviceID")
    name = info.get("DeviceName", "iPhone")
    version = info.get("ProductVersion", "Unknown")
    product = info.get("ProductType", "iPhone")

    if not udid:
        return None

    return {
        "udid": udid,
        "name": name,
        "version": version,
        "product": product,
    }


def find_syslog_executable() -> str:
    """Finds path to idevicesyslog utility."""
    candidates = [
        str(Path(__file__).resolve().parent / "bin" / "idevicesyslog"),
        "/Applications/AirCard.app/Contents/Resources/bin/idevicesyslog",
        shutil.which("idevicesyslog"),
        "/opt/homebrew/bin/idevicesyslog",
        "/usr/local/bin/idevicesyslog",
        "/usr/bin/idevicesyslog",
    ]
    for c in candidates:
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    return "idevicesyslog"


def capture_card_hashes(udid: str, existing_cards: list[str] | None = None) -> list[str]:
    """Listens to syslog and collects card hashes while the user opens Apple Wallet."""
    print("\n" + "=" * 60)
    print("📡 CARD SCANNING MODE")
    print("=" * 60)
    print("To detect your cards:")
    print("  👉 1) Double-click Side (Power) button to open Apple Pay.")
    print("  👉 2) Authenticate with Face ID.")
    print("  👉 3) Tap your card to trigger instant detection!")
    print("Press ENTER when finished.")
    print("=" * 60 + "\n")

    syslog_bin = find_syslog_executable()
    cmd = [syslog_bin, "-u", udid, "--no-colors"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    found_hashes = set(existing_cards or [])
    initial_count = len(found_hashes)

    try:
        import select

        while True:
            rlist, _, _ = select.select([sys.stdin, process.stdout], [], [], 0.2)
            if sys.stdin in rlist:
                sys.stdin.readline()
                break

            if process.stdout in rlist:
                line = process.stdout.readline()
                if not line:
                    break

                lower = line.lower()
                is_wallet = (
                    "passd" in lower
                    or "passbook" in lower
                    or "passkit" in lower
                    or "stockholm" in lower
                    or "nanopassd" in lower
                    or "wallet" in lower
                    or "/cards/" in lower
                )
                if not is_wallet:
                    continue

                is_ctx = any(
                    w in lower
                    for w in [
                        "card",
                        "pass",
                        "payment",
                        "pkpass",
                        "uniqueid",
                        "identifier",
                        "face",
                        "cache",
                        "stockholm",
                        "/cards/",
                    ]
                )
                if not is_ctx:
                    continue

                for r in CARD_REGEXES:
                    m = r.search(line)
                    if m:
                        h = m.group(1).strip().strip("'\"").rstrip(".").rstrip(",")
                        if len(h) == 36 and "-" in h:
                            continue
                        if h in [
                            "M6nDwZrkYbFlsodLgCbvyFZQ1cc=",
                            "kJL-D0rr-SZhbj2c8nK-OQ9hCMY=",
                            "hwAtAmHKYwsQrJbT5cTNDsaxVME=",
                        ]:
                            continue
                        if h and h not in found_hashes:
                            found_hashes.add(h)
                            print(f"  ✨ Detected card [{len(found_hashes)}]: {h}")

    except KeyboardInterrupt:
        pass
    finally:
        process.terminate()
        process.wait()

    res = list(found_hashes)
    save_cards(res)
    return res


def prepare_card_image(input_path: str) -> bytes:
    """Scales image to Apple Wallet standard (1536x969 PNG)."""
    clean_path = input_path.strip().strip("'").strip('"')
    path = Path(clean_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        from PIL import Image, ImageOps
        with Image.open(path) as img:
            img = img.convert("RGBA")
            target_size = (1536, 969)
            fitted = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
            out_io = io.BytesIO()
            fitted.save(out_io, format="PNG")
            return out_io.getvalue()
    except Exception:
        pass

    # Fallback to macOS sips
    temp_out = f"/tmp/aircard_sips_{os.getpid()}.png"
    try:
        subprocess.check_call([
            "/usr/bin/sips",
            "-s", "format", "png",
            "-z", "969", "1536",
            str(path),
            "--out", temp_out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = Path(temp_out).read_bytes()
        Path(temp_out).unlink(missing_ok=True)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to process image: {e}")


def prepare_card_assets(png_bytes: bytes) -> dict[str, bytes]:
    """Prepare every format before modifying any files on the device."""
    helper = ROOT / "bin" / "card_pdf"
    if not helper.is_file():
        helper = ROOT / "build" / "card_pdf"
    with tempfile.TemporaryDirectory(prefix="aircard-pdf-") as directory:
        source = Path(directory) / "card.png"
        output = Path(directory) / "card.pdf"
        source.write_bytes(png_bytes)
        subprocess.run([str(helper), str(source), str(output)], check=True,
                       capture_output=True, timeout=30)
        pdf_bytes = output.read_bytes()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("Artwork converter did not produce a PDF")
    return {asset: pdf_bytes if asset.endswith(".pdf") else png_bytes
            for asset in TARGET_ASSETS}


def main():
    print("=" * 60)
    print("🎴 AirCard — Apple Wallet Card Skinner (via airlift)")
    print("=" * 60)

    # 1. Device discovery
    print("\n[1/5] Searching for connected device...")
    device = get_connected_device()
    if not device:
        print("❌ iPhone not found! Connect your iPhone via USB and unlock the screen.")
        sys.exit(1)

    print(f"✅ Found: {device['name']} ({device['product']}, iOS {device['version']})")
    print(f"   UDID: {device['udid']}")

    # 2. Check airlift compatibility
    probe = native("probe", device["udid"])
    if not operation_ok(probe):
        print("❌ Airlift pre-check failed. Ensure the device is paired and trusted.")
        sys.exit(1)

    # 3. Card discovery / selection
    saved_cards = load_saved_cards()
    print(f"\n[2/5] Saved cards: {len(saved_cards)}")
    for idx, h in enumerate(saved_cards, 1):
        print(f"  [{idx}] {h}")

    print("\nChoose an action:")
    print("  1 - Use existing cards")
    print("  2 - Scan cards (open Wallet & tap card)")
    print("  3 - Enter card hash(es) manually")
    mode = input("Your choice [1]: ").strip()

    hashes = saved_cards
    if mode == "2":
        hashes = capture_card_hashes(device["udid"], saved_cards)
    elif mode == "3":
        manual = input("Enter card hashes separated by commas or spaces: ").strip()
        new_items = [x.strip() for x in re.split(r"[\s,;]+", manual) if len(x.strip()) >= 16]
        for item in new_items:
            if item not in hashes:
                hashes.append(item)
        save_cards(hashes)

    if not hashes:
        print("❌ No cards available to flash.")
        sys.exit(1)

    print(f"\n[3/5] Ready to flash cards ({len(hashes)}):")
    for i, h in enumerate(hashes, 1):
        print(f"  [{i}] {h}")

    print("\nSelect cards to customize:")
    print("  'all' - apply to all cards")
    print("  comma-separated numbers (e.g. 1,3)")
    choice = input("Your choice [all]: ").strip().lower()

    if choice == "" or choice == "all":
        selected_hashes = hashes
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(",") if x.strip()]
            selected_hashes = [hashes[i - 1] for i in indices if 1 <= i <= len(hashes)]
        except Exception:
            print("Invalid input. Applying to all cards.")
            selected_hashes = hashes

    if not selected_hashes:
        print("❌ No cards selected.")
        sys.exit(1)

    # 4. Prepare image
    print(f"\n[4/5] Preparing image...")
    while True:
        img_input = input("Drag and drop image file into terminal (or enter path): ").strip()
        try:
            png_bytes = prepare_card_image(img_input)
            assets = prepare_card_assets(png_bytes)
            print(f"✅ Image optimized for Apple Wallet ({len(png_bytes)} bytes)")
            break
        except Exception as e:
            print(f"❌ Error: {e}. Please specify another image.")

    # 5. Flash cards
    print(f"\n[5/5] Flashing skin to selected cards ({len(selected_hashes)})...")

    failed = []
    for idx, h in enumerate(selected_hashes, 1):
        print(f"\n--- [{idx}/{len(selected_hashes)}] Card: {h} ---")
        pkpass_dir = f"/var/mobile/Library/Passes/Cards/{h}.pkpass"

        for asset in TARGET_ASSETS:
            ok = write_file(device["udid"], pkpass_dir, asset, assets[asset])
            if not ok:
                failed.append(f"{h}/{asset}")
            status = "OK" if ok else "FAIL"
            print(f"  -> {asset}: {status}")

        for ext in [".cache", ".pkcache"]:
            cache_dir = f"/var/mobile/Library/Passes/Cards/{h}{ext}"
            for leaf in CACHE_FILES:
                if not write_file(device["udid"], cache_dir, leaf, b"corrupted"):
                    failed.append(f"{h}{ext}/{leaf}")
        print("  -> System cache cleared (.cache & .pkcache)")

    print("\n" + "=" * 60)
    if failed:
        print("❌ Some writes failed: " + ", ".join(failed))
        sys.exit(1)
    print("🎉 DONE! All selected cards successfully updated!")
    print("=" * 60)
    print("1. Force close Apple Wallet on your iPhone.")
    print("2. If the image does not update immediately, restart your iPhone.")
    print("=" * 60)


if __name__ == "__main__":
    main()
