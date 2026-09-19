# AirCard 🎴

> **Apple Wallet Card Skinner & Lockscreen Passcode Themer for iOS 18+ (No Jailbreak Required)**  
> **Tested on iOS 27 release.**
> Powered by the `airlift` AirTraffic sync exploit.

---

## Features
- 🎨 **Custom Card Skins:** Assign custom artwork, textures, or bank logos to Apple Pay and Wallet cards.
- 🔢 **Lock Screen Passcode Themes (.passthm):** Apply custom keypad button artwork from popular `.passthm` themes directly to iOS 18+ lockscreen.
- 🧩 **Passcode Theme Creator:** Create custom themes from a single wallpaper (Seamless Poster Slicing) or build key-by-key (Individual Keys).
- 🔍 **Interactive Photo Framing:** Pan and zoom artwork directly inside keypad buttons with real-time iPhone preview.
- ✏️ **Edit Existing .passthm Themes:** Open any Cowabunga or Nugget theme package directly in the creator, tweak button artwork, reposition photos, and re-export or flash.
- ⚡ **Per-Card & Bulk Customization:** Set unique artwork for each card or apply one design across all cards with a single click.
- 📱 **Zero-Hassle Card Detection:** Tap any card in your iPhone's Wallet app to detect its hash in real-time.
- 🚀 **100% Standalone (Universal):** Native support for both **Apple Silicon** and **Intel (x86)** Macs. All required device-communication utilities and image engines are pre-bundled inside the app.
- 📦 **Zero Prerequisites:** No Homebrew, Python packages, or terminal setup required for macOS users.

---

## Installation

### macOS (Universal DMG)
1. Download **`AirCard.dmg`** from [Releases](https://github.com/mak5er/AirCard/releases).
2. Open `AirCard.dmg` and drag **`AirCard.app`** into your **Applications** folder.
3. Fully compatible with both **Apple Silicon** and **Intel (x86)** Macs.

> [!NOTE]
> **First Launch on macOS (Gatekeeper):**
> If macOS displays an unidentified developer prompt on first launch:
> - **Method 1 (UI):** Right-click (or Control-click) `AirCard.app` in Applications ➔ click **Open** ➔ click **Open**.
> - **Method 2 (Terminal):**
>   ```sh
>   sudo xattr -cr /Applications/AirCard.app
>   ```

---

## How to Customize Apple Wallet Cards
1. Connect your iPhone to your Mac via USB cable and ensure it is unlocked and trusted.
2. In AirCard, stay on the **Wallet Cards** tab and click **Scan Cards**.
3. On your iPhone:
   - **Double-click the Side (Power) button** to open Apple Pay.
   - Authenticate with **Face ID**.
   - **Tap your card** (or tap it once more) to trigger instant detection!
4. Click on any card mockup or drag & drop an image directly onto the card.
5. Click **Flash Skins**.
6. Force-close the **Wallet** app on your iPhone from the App Switcher (or reboot) to see your new custom card design!

---

## Design Card Artwork with an Agent

This checkout includes the [card-face-design skill](.agents/skills/card-face-design/SKILL.md)
for creating several distinct card faces with source research, official assets,
precise geometry, soft masks, and Figma/export verification. It includes brief,
art-direction, asset-provenance, and review templates, plus a non-generative
script/CV workflow.

From an agent session in this checkout, invoke:

```text
$card-face-design Create three distinct card faces for AirCard using these references.
```

For an agent without automatic skill discovery, load the linked `SKILL.md` directly.
To review exported cards, copy and fill in the
[collection manifest](.agents/skills/card-face-design/templates/collection.json), then run:

```sh
python3 .agents/skills/card-face-design/scripts/review_cards.py \
  --manifest /absolute/path/to/collection.json \
  --out /absolute/path/to/review
```

The review helper requires Python 3.10+ and Pillow; dependencies are listed in
[requirements.txt](.agents/skills/card-face-design/requirements.txt). It checks export
sizes, shared alpha silhouettes, and optional full-bleed opacity, and produces
phone-size comparisons and unscaled detail crops. Inspect those images before
choosing the final PNG in AirCard. A passed export check does not verify Wallet
rendering on the device.

---

## How to Apply Lockscreen Passcode Themes (.passthm)
1. Switch to the **Passcode Themes** tab at the top of AirCard.
2. Drag & drop any `.passthm` file into the app (or click **Choose .passthm File**).
3. AirCard will inspect the theme and display an interactive preview on the numeric keypad (0–9, *, #).
4. Click **Apply Passcode Theme**.
5. Restart your iPhone to reload the lock screen cache and see your custom passcode buttons!

> [!IMPORTANT]
> **Turn OFF Bold Text:**  
> On your iPhone, go to **Settings ➔ Display & Brightness** and make sure **Bold Text** is turned **OFF**. If Bold Text is enabled, iOS bypasses cached keypad graphics and draws vector fonts instead.

---

## Building from Source

### Xcode (macOS 14+)

Open `AirCard.xcodeproj`, select the **AirCard** scheme and **My Mac**, then build.
The project is configured for the MikuNet LLC team (`F25GFFJL49`); choose your own
team in Signing & Capabilities when building elsewhere.

The build compiles the device helpers and native PDF converter, and bundles the
Python backend. It copies the libimobiledevice tools and libraries from an installed
`/Applications/AirCard.app`. To use another release, set the build setting
`AIRCARD_DEPENDENCIES` to that app's `Contents/Resources` directory. Python 3 must
be available on the Mac (Xcode's command-line tools provide it).

```sh
xcodebuild -project AirCard.xcodeproj -scheme AirCard -configuration Release \
  -derivedDataPath build/Xcode -destination 'platform=macOS' build
```

Output: `build/Xcode/Build/Products/Release/AirCard.app`.
This produces a development-signed build, not a notarized distribution release.

Artwork flashing writes both PNG variants and a real `cardBackgroundCombined.pdf`
for PDF-backed cards such as Suica, and invalidates FrontFace, PlaceHolder, and
Preview caches. A failed write is reported as a failure. Actual Wallet rendering
still needs verification on a connected device.

### Shell build

```sh
git clone https://github.com/mak5er/AirCard.git
cd AirCard
chmod +x build.sh
./build.sh
```
This builds universal binaries (`arm64` + `x86_64`), bundles dependencies into `build/AirCard.app`, and outputs `build/AirCard.dmg`.

---

## Contributors
- **[@mak5er](https://github.com/mak5er)** (Developer) — [GitHub](https://github.com/mak5er) · [Twitter / X](https://x.com/mak5er)
- **[@Lumid-Off](https://github.com/Lumid-Off)** (Contributor & Developer) — [GitHub](https://github.com/Lumid-Off) · [Twitter / X](https://x.com/LumidOff)

## Credits
- Core exploit based on `airlift` (AirTraffic sync escape).

## Artwork backups and restore

Flash Skins now requires a verified backup before writing any artwork. The same
requirement applies to both command-line entry points. Backups preserve the exact
bytes of `cardBackgroundCombined@3x.png`, `cardBackgroundCombined@2x.png`, and
`cardBackgroundCombined.pdf`, including a record of which files were absent.
They do not copy the whole pass directory or the disposable Wallet caches.

Use **Backups → Back Up Selected Cards** to back up without flashing, **Show
Backups** to browse snapshots, or **Restore Artwork…** to select a `manifest.json`.
Backups are stored in `~/Library/Application Support/AirCard/Backups`, grouped by
hashed device/card identifiers and timestamp. Every successful snapshot has a
manifest containing the device, card, file sizes, and SHA-256 checksums. Later
backups do not replace earlier snapshots. A backup captures the current artwork;
it cannot recover an issuer image that was overwritten before the first backup.

Restore validates the device and checksums, backs up the current artwork first,
restores saved files, removes newly introduced artwork absent from the selected
snapshot, verifies readback, and invalidates Wallet caches. If a write fails, the
snapshot is retained and the operation reports failure; restoring several files
is not an atomic transaction.

The reader attempts access through a temporary Airlift directory link. If iOS
blocks directory access, backup and flashing stop without moving artwork.
The experimental move-based fallback is disabled: testing on iOS 26.7 saved
one original locally but could not verify its return to the phone. Backups and
restore are therefore not yet supported on that tested device.

Every overwritten file must have a verified backup or have been positively
confirmed absent by a complete directory listing. Older experimental snapshots
may contain unknown entries; those entries are left untouched during restore.

Books sync state is preserved. Pending backup sessions remain on disk if cleanup
fails and must recover successfully before the next artwork operation. Artwork
operations are serialized per device. Keep the same Mac's backup directory when
recovering an interrupted session.

```sh
python3 aircard_backend.py --backup-artwork DEVICE_ID CARD_HASH
python3 aircard_backend.py --restore-artwork DEVICE_ID /path/to/manifest.json
python3 -m unittest discover -s tests -p 'test_card*.py' -v
```
