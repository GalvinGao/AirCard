#!/usr/bin/env python3
"""Check card exports and make review images without modifying the input artwork."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow is required. Use a suitable existing Python runtime or install requirements.txt in a virtual environment.")


def positive_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return float(value)


def positive_integer(value: object, label: str) -> int:
    number = positive_number(value, label)
    if not number.is_integer():
        raise ValueError(f"{label} must be a whole number")
    return int(number)


def image_path(base: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("Image paths must be nonempty strings")
    return (base / value).resolve()


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def fit_label(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> str:
    if draw.textbbox((0, 0), text, font=font)[2] <= width:
        return text
    while text and draw.textbbox((0, 0), text + "…", font=font)[2] > width:
        text = text[:-1]
    return text + "…" if text else ""


def checker(size: tuple[int, int]) -> Image.Image:
    result = Image.new("RGBA", size, "#f4f2ee")
    draw = ImageDraw.Draw(result)
    for y in range(0, size[1], 12):
        for x in range(0, size[0], 12):
            if (x // 12 + y // 12) % 2:
                draw.rectangle((x, y, x + 11, y + 11), fill="#e7e4de")
    return result


def render_sheet(items: list[tuple[str, Image.Image]], path: Path, width: int, height: int,
                 font: ImageFont.ImageFont, nearest: bool = False) -> None:
    columns = min(2, len(items))
    rows = math.ceil(len(items) / columns)
    margin, label_height = 24, 36
    sheet = Image.new("RGB", (columns * (width + margin) + margin,
                              rows * (height + label_height + margin) + margin), "#eeebe4")
    draw = ImageDraw.Draw(sheet)
    for index, (label, original) in enumerate(items):
        x = margin + (index % columns) * (width + margin)
        y = margin + (index // columns) * (height + label_height + margin)
        draw.text((x, y), fit_label(draw, label, font, width), font=font, fill="#243e48")
        scale = min(width / original.width, height / original.height)
        size = (max(1, round(original.width * scale)), max(1, round(original.height * scale)))
        resampling = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS
        resized = original.resize(size, resampling)
        background = checker(size)
        background.alpha_composite(resized)
        sheet.paste(background.convert("RGB"), (x + (width - size[0]) // 2, y + label_height))
    sheet.save(path)


def review(manifest_path: Path, output: Path, font_path: Path | None, nearest: bool) -> dict:
    config = json.loads(manifest_path.read_text())
    if not isinstance(config, dict):
        raise ValueError("The manifest must be a JSON object")
    canvas = config.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError("canvas.width and canvas.height are required")
    width = positive_integer(canvas.get("width"), "canvas.width")
    height = positive_integer(canvas.get("height"), "canvas.height")
    scale = positive_number(config.get("export_scale", 1), "export_scale")
    expected = (positive_integer(width * scale, "export width"),
                positive_integer(height * scale, "export height"))
    preview = positive_integer(config.get("preview_width", 393), "preview_width")
    cards = config.get("cards")
    if not isinstance(cards, list) or not cards:
        raise ValueError("cards must contain at least one card")
    for key in ("same_alpha", "require_transparent_corners"):
        if key in config and not isinstance(config[key], bool):
            raise ValueError(f"{key} must be true or false")

    base = manifest_path.parent
    inputs = {manifest_path.resolve()}
    for card in cards:
        if not isinstance(card, dict) or not isinstance(card.get("name"), str) or not card["name"].strip():
            raise ValueError("Each card needs a nonempty name")
        inputs.add(image_path(base, card.get("image")))
        if "fullbleed" in card:
            inputs.add(image_path(base, card["fullbleed"]))
    outputs = [output / name for name in ("phone-contact-sheet.png", "detail-crops.png", "review-report.json")]
    if inputs.intersection(p.resolve() for p in outputs):
        raise ValueError("The output paths would overwrite an input file; choose a different --out directory")

    report: dict = {"expected_export_size": list(expected), "preview_width": preview,
                    "technical_checks_passed": False, "visual_review_required": True,
                    "cards": [], "errors": [], "generated_files": []}
    images: list[tuple[str, Image.Image]] = []
    details: list[tuple[str, Image.Image]] = []
    detail_records: list[dict] = []
    hashes: list[str] = []
    for card in cards:
        name = card["name"]
        entry: dict = {"name": name, "image": str(image_path(base, card["image"]))}
        report["cards"].append(entry)
        try:
            image = load_rgba(Path(entry["image"]))
            entry["actual_size"] = list(image.size)
            if image.size != expected:
                report["errors"].append(f"{name}: size {image.size} differs from {expected}")
            alpha = image.getchannel("A")
            digest = hashlib.sha256(alpha.tobytes()).hexdigest()
            hashes.append(digest)
            entry["alpha_sha256"] = digest
            entry["alpha_extrema"] = list(alpha.getextrema())
            if alpha.getbbox() is None:
                report["errors"].append(f"{name}: image is entirely transparent")
            if config.get("require_transparent_corners", False):
                corners = ((0, 0), (image.width - 1, 0), (0, image.height - 1),
                           (image.width - 1, image.height - 1))
                if any(alpha.getpixel(point) != 0 for point in corners):
                    report["errors"].append(f"{name}: expected transparent outer corner pixels")
            images.append((name, image))
            if "fullbleed" in card:
                full_path = image_path(base, card["fullbleed"])
                full = load_rgba(full_path)
                opaque = full.getchannel("A").getextrema() == (255, 255)
                entry["fullbleed"] = {"path": str(full_path), "size": list(full.size), "opaque": opaque}
                if full.size != expected:
                    report["errors"].append(f"{name}: full-bleed dimensions differ from {expected}")
                if not opaque:
                    report["errors"].append(f"{name}: full-bleed image contains transparency")
            crops = card.get("crops", [])
            if not isinstance(crops, list):
                raise ValueError("crops must be a list")
            for crop in crops:
                if not isinstance(crop, dict):
                    raise ValueError("Each crop must contain a label and box")
                box = crop.get("box")
                if not isinstance(box, list) or len(box) != 4 or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in box
                ):
                    raise ValueError("Crop boxes need four finite numbers in design-canvas coordinates")
                x0, y0, x1, y1 = box
                if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                    raise ValueError(f"Crop is outside the design canvas or empty: {box}")
                if image.size != expected:
                    continue  # Do not present incorrectly located detail crops as valid evidence.
                pixel_box = tuple(round(v * scale) for v in box)
                if pixel_box[2] <= pixel_box[0] or pixel_box[3] <= pixel_box[1]:
                    raise ValueError(f"Crop is smaller than one export pixel: {box}")
                label = str(crop.get("label", "Detail"))
                details.append((f"{name} / {label}", image.crop(pixel_box)))
                detail_records.append({"card": name, "label": label,
                                       "design_box": box, "pixel_box": list(pixel_box)})
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            entry["error"] = str(exc)
            report["errors"].append(f"{name}: {exc}")

    if config.get("same_alpha", True) and len(set(hashes)) > 1:
        report["errors"].append("Card alpha masks differ; the collection does not share one silhouette")
    report["same_alpha"] = len(hashes) == len(cards) and len(set(hashes)) == 1
    report["technical_checks_passed"] = not report["errors"]
    detail_paths = [output / "detail-crops" / f"{index:02d}.png"
                    for index in range(1, len(details) + 1)]
    if inputs.intersection(p.resolve() for p in detail_paths):
        raise ValueError("The detail paths would overwrite an input file; choose a different --out directory")
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(font_path), 18) if font_path else ImageFont.load_default(size=18)
    if images:
        path = output / "phone-contact-sheet.png"
        render_sheet(images, path, preview, round(preview * height / width), font)
        report["generated_files"].append(str(path.resolve()))
    if details:
        path = output / "detail-crops.png"
        render_sheet(details, path, 560, 360, font, nearest)
        report["generated_files"].append(str(path.resolve()))
        detail_paths[0].parent.mkdir(parents=True, exist_ok=True)
        for (_, crop_image), detail_path, record in zip(details, detail_paths, detail_records):
            crop_image.save(detail_path)
            record["path"] = str(detail_path.resolve())
            record["size"] = list(crop_image.size)
            report["generated_files"].append(record["path"])
    report["detail_crops"] = detail_records
    report_path = output / "review-report.json"
    report["generated_files"].append(str(report_path.resolve()))
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font", type=Path, help="Optional local font for review-sheet labels")
    parser.add_argument("--nearest-details", action="store_true", help="Enlarge detail pixels without smoothing")
    args = parser.parse_args()
    try:
        report = review(args.manifest.resolve(), args.out.resolve(), args.font, args.nearest_details)
    except (OSError, ValueError, TypeError, Image.DecompressionBombError) as exc:
        print(f"Card review failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: report[key] for key in
                      ("technical_checks_passed", "visual_review_required", "errors", "generated_files")}, indent=2))
    return 0 if report["technical_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
