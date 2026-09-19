#!/usr/bin/env python3
"""
Backend engine for AirCard native macOS GUI app.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

# Augment PATH so bundled tools and system tools are always found
script_dir = Path(__file__).resolve().parent
bundled_bin = script_dir / "bin"
bundled_lib = script_dir / "lib"
app_bin = Path("/Applications/AirCard.app/Contents/Resources/bin")
app_lib = Path("/Applications/AirCard.app/Contents/Resources/lib")

paths_to_add = [
    str(bundled_bin),
    str(app_bin),
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin"
]
for p in reversed(paths_to_add):
    if os.path.isdir(p) and p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{p}:{os.environ.get('PATH', '')}"

lib_paths = [str(bundled_lib), str(app_lib)]
for lp in lib_paths:
    if os.path.isdir(lp):
        cur_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
        os.environ["DYLD_LIBRARY_PATH"] = f"{lp}:{cur_dyld}" if cur_dyld else lp

from apply_card_skin import (
    native,
    operation_ok,
    write_file,
    ROOT,
    DEVICE_HELPER,
)
from card_backup import backup_card, device_lock, restore_card, load_backup

from aircard import (
    get_connected_device,
    load_saved_cards,
    save_cards,
    TARGET_ASSETS,
    prepare_card_assets,
    CACHE_FILES,
)


def cmd_device():
    device = get_connected_device()
    if not device:
        print(json.dumps({"connected": False}))
        return
    probe = native("probe", device["udid"])
    device["airlift_compatible"] = operation_ok(probe)
    device["connected"] = True
    print(json.dumps(device))


def cmd_get_saved_cards():
    cards = load_saved_cards()
    print(json.dumps({"ok": True, "cards": cards}))


def cmd_save_cards(cards_json: str):
    try:
        cards = json.loads(cards_json)
        if isinstance(cards, list):
            save_cards(cards)
            print(json.dumps({"ok": True}))
            return
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return
    print(json.dumps({"ok": False, "error": "Invalid format"}))


def cmd_prepare_image(src: str, dst: str):
    path = Path(src).expanduser()
    if not path.is_file():
        print(json.dumps({"ok": False, "error": f"File not found: {src}"}))
        return
    try:
        from PIL import Image, ImageOps
        with Image.open(path) as img:
            img = img.convert("RGBA")
            target_size = (1536, 969)
            fitted = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
            fitted.save(dst, format="PNG")
        print(json.dumps({"ok": True, "path": dst}))
        return
    except ImportError:
        pass
    except Exception as e:
        pass
    
    # Fallback to macOS built-in sips tool (built into every macOS, 0 dependencies!)
    try:
        import subprocess
        subprocess.check_call([
            "/usr/bin/sips",
            "-s", "format", "png",
            "-z", "969", "1536",
            str(path),
            "--out", str(dst)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(json.dumps({"ok": True, "path": dst}))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))


def cmd_flash(udid: str, card_hash: str, image_path: str):
    try:
        with device_lock(udid):
            return _cmd_flash(udid, card_hash, image_path)
    except Exception as exc:
        print(json.dumps({"type": "error", "message": str(exc)}), flush=True)
        return False


def cmd_backup(udid: str, cards: list[str]):
    try:
        with device_lock(udid):
            for card in cards:
                manifest = backup_card(udid, card)
                print(json.dumps({"type": "backup", "message": f"Verified backup: {manifest}",
                                  "path": str(manifest)}), flush=True)
        return True
    except Exception as exc:
        print(json.dumps({"type": "error", "message": str(exc)}), flush=True)
        return False


def cmd_restore(udid: str, manifest_path: str):
    try:
        with device_lock(udid):
            rollback = restore_card(udid, manifest_path)
        print(json.dumps({"type": "success", "message": "Original artwork restored and verified. Reopen Wallet.",
                          "backup": str(rollback)}), flush=True)
        return True
    except Exception as exc:
        print(json.dumps({"type": "error", "message": str(exc)}), flush=True)
        return False


def _cmd_flash(udid: str, card_hash: str, image_path: str):
    img_path = Path(image_path)
    if not img_path.is_file():
        print(json.dumps({"type": "error", "message": "Image file not found"}))
        return False

    try:
        assets = prepare_card_assets(img_path.read_bytes())
    except Exception as exc:
        print(json.dumps({"type": "error", "message": f"Could not prepare artwork: {exc}"}), flush=True)
        return False
    print(json.dumps({"type": "progress", "message": "Backing up original artwork before writing..."}), flush=True)
    manifest = backup_card(udid, card_hash)
    print(json.dumps({"type": "backup", "message": f"Verified artwork backup: {manifest}",
                      "path": str(manifest)}), flush=True)
    saved, _ = load_backup(udid, manifest)
    writable_assets = [name for name in TARGET_ASSETS if saved['files'][name]['present'] is not None]
    skipped = [name for name in TARGET_ASSETS if name not in writable_assets]
    if skipped:
        print(json.dumps({"type": "warning", "message": "Leaving unverified artwork untouched: " + ", ".join(skipped)}), flush=True)
    failed = []
    pkpass_dir = f"/var/mobile/Library/Passes/Cards/{card_hash}.pkpass"
    
    total_steps = len(writable_assets) + (len(CACHE_FILES) * 2) + 1
    step = 0

    for asset in writable_assets:
        step += 1
        print(json.dumps({
            "type": "progress",
            "card": card_hash,
            "step": step,
            "total": total_steps,
            "asset": asset,
            "message": f"Writing {asset}..."
        }))
        sys.stdout.flush()
        ok = write_file(udid, pkpass_dir, asset, assets[asset])
        if not ok:
            failed.append(asset)
            print(json.dumps({
                "type": "error",
                "card": card_hash,
                "asset": asset,
                "message": f"Failed to write {asset}"
            }))
            sys.stdout.flush()

    # Clear cache
    for ext in [".cache", ".pkcache"]:
        cache_dir = f"/var/mobile/Library/Passes/Cards/{card_hash}{ext}"
        for leaf in CACHE_FILES:
            step += 1
            print(json.dumps({
                "type": "progress",
                "card": card_hash,
                "step": step,
                "total": total_steps,
                "message": f"Invalidating cache ({leaf} in {ext})..."
            }))
            sys.stdout.flush()
            if not write_file(udid, cache_dir, leaf, b"corrupted"):
                failed.append(f"{ext}/{leaf}")

    if failed:
        print(json.dumps({"type": "error", "message": "Failed to update: " + ", ".join(failed)}), flush=True)
        return False

    step += 1
    print(json.dumps({
        "type": "success",
        "card": card_hash,
        "step": step,
        "total": total_steps,
        "message": f"Successfully updated {card_hash[:12]}..."
    }))
    sys.stdout.flush()

    return True


KEYPAD_SUBTEXTS = {
    "0": "+",
    "1": "",
    "2": "A B C",
    "3": "D E F",
    "4": "G H I",
    "5": "J K L",
    "6": "M N O",
    "7": "P Q R S",
    "8": "T U V",
    "9": "W X Y Z",
}


def parse_passthm_archive(passthm_path: str, telephony_ver: str = "TelephonyUI-10") -> list[tuple[str, str, bytes]]:
    path = Path(passthm_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Passcode theme file not found: {passthm_path}")

    with zipfile.ZipFile(path, "r") as z:
        image_entries = [
            n for n in z.namelist()
            if not n.startswith("__MACOSX")
            and not n.endswith("/")
            and not Path(n).name.startswith(".")
            and any(n.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg"))
        ]
        if not image_entries:
            return []

        target_dir = f"/var/mobile/Library/Caches/{telephony_ver}"
        items_dict: dict[str, bytes] = {}

        for entry in image_entries:
            leaf = Path(entry).name
            data = z.read(entry)
            items_dict[leaf] = data

            stem = Path(leaf).stem
            stem_clean = re.sub(r"--?white$", "", stem, flags=re.IGNORECASE)
            m = re.search(r"(?:^[a-zA-Z]+-)?([0-9*#])(?:-([^-\n]+))?", stem_clean)
            digit = None
            subtext = ""
            if m:
                digit = m.group(1)
                if m.group(2):
                    subtext = m.group(2).strip()
            if not digit:
                m2 = re.search(r"([0-9*#])", leaf)
                if m2:
                    digit = m2.group(1)

            if digit:
                if subtext:
                    items_dict[f"en-{digit}-{subtext}--white.png"] = data
                    items_dict[f"other-{digit}-{subtext}--white.png"] = data
                items_dict[f"en-{digit}---white.png"] = data
                items_dict[f"other-{digit}---white.png"] = data

                std_subtext = KEYPAD_SUBTEXTS.get(digit)
                if std_subtext:
                    items_dict[f"en-{digit}-{std_subtext}--white.png"] = data
                    items_dict[f"other-{digit}-{std_subtext}--white.png"] = data

                if leaf.startswith("en-"):
                    items_dict["other" + leaf[2:]] = data
                elif leaf.startswith("other-"):
                    items_dict["en" + leaf[5:]] = data

        return [(target_dir, leaf, data) for leaf, data in items_dict.items()]


def cmd_inspect_passthm(passthm_path: str):
    path = Path(passthm_path).expanduser()
    if not path.is_file():
        print(json.dumps({"ok": False, "error": f"File not found: {passthm_path}"}))
        return
    try:
        detected_ver = "TelephonyUI-10"
        with zipfile.ZipFile(path, "r") as z:
            for entry in z.namelist():
                low = entry.lower()
                if "telephonyui-8" in low or "telephony-8" in low:
                    detected_ver = "TelephonyUI-8"
                    break
                elif "telephonyui-9" in low or "telephony-9" in low:
                    detected_ver = "TelephonyUI-9"
                    break

        items = parse_passthm_archive(str(path), detected_ver)
        if not items:
            print(json.dumps({"ok": False, "error": "No image assets found in archive"}))
            return

        keys_preview = {}
        for _, leaf, data in items:
            m = re.search(r'^[a-zA-Z]+-([0-9*#])-?', leaf)
            digit = m.group(1) if m else None
            if not digit:
                m2 = re.search(r'([0-9*#])', leaf)
                if m2:
                    digit = m2.group(1)
            if digit and digit not in keys_preview:
                b64 = base64.b64encode(data).decode("utf-8")
                mime = "image/png" if leaf.lower().endswith(".png") else "image/jpeg"
                keys_preview[digit] = f"data:{mime};base64,{b64}"

        print(json.dumps({
            "ok": True,
            "name": path.stem,
            "detected_version": detected_ver,
            "file_count": len(items),
            "keys_preview": keys_preview
        }))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))


def cmd_flash_passthm(udid: str, passthm_path: str, telephony_ver: str = "TelephonyUI-10"):
    path = Path(passthm_path).expanduser()
    if not path.is_file():
        print(json.dumps({"ok": False, "error": "Passcode theme file not found"}))
        return

    try:
        items_to_write = parse_passthm_archive(str(path), telephony_ver)
        if not items_to_write:
            print(json.dumps({"ok": False, "error": "No image assets found in archive"}))
            return

        total_steps = len(items_to_write)
        step = 0

        for tdir, leaf, payload in items_to_write:
            step += 1
            tdir_name = Path(tdir).name
            print(json.dumps({
                "type": "progress",
                "step": step,
                "total": total_steps,
                "leaf": leaf,
                "message": f"Writing {leaf} ({tdir_name})..."
            }))
            sys.stdout.flush()

            ok = write_file(udid, tdir, leaf, payload)
            if not ok:
                print(json.dumps({
                    "type": "warning",
                    "leaf": leaf,
                    "message": f"Could not write {leaf} to {tdir}"
                }))
                sys.stdout.flush()

        print(json.dumps({
            "type": "success",
            "step": total_steps,
            "total": total_steps,
            "message": f"Passcode theme '{path.stem}' successfully applied! Lock your iPhone to check."
        }))
        sys.stdout.flush()

    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    cmd = sys.argv[1]
    norm_cmd = cmd.lstrip("-")
    if norm_cmd == "device":
        cmd_device()
    elif norm_cmd == "cards":
        cmd_get_saved_cards()
    elif norm_cmd == "save-cards" and len(sys.argv) > 2:
        cmd_save_cards(sys.argv[2])
    elif norm_cmd == "prepare-image" and len(sys.argv) > 3:
        cmd_prepare_image(sys.argv[2], sys.argv[3])
    elif norm_cmd == "flash" and len(sys.argv) > 4:
        sys.exit(0 if cmd_flash(sys.argv[2], sys.argv[3], sys.argv[4]) else 1)
    elif norm_cmd == "backup-artwork" and len(sys.argv) > 3:
        sys.exit(0 if cmd_backup(sys.argv[2], sys.argv[3:]) else 1)
    elif norm_cmd == "restore-artwork" and len(sys.argv) > 3:
        sys.exit(0 if cmd_restore(sys.argv[2], sys.argv[3]) else 1)
    elif norm_cmd == "inspect-passthm" and len(sys.argv) > 2:
        cmd_inspect_passthm(sys.argv[2])
    elif norm_cmd == "flash-passthm" and len(sys.argv) > 3:
        t_ver = sys.argv[4] if len(sys.argv) > 4 else "TelephonyUI-10"
        cmd_flash_passthm(sys.argv[2], sys.argv[3], t_ver)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
