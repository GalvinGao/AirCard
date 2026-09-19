# Compositing and geometry

## Measure one reusable template

Record design width/height, outer clipping shape, corner construction, inner frame, safe area, logo bounds, bottom strip and export scale. Derive these from the supplied reference and target. Keep issuer-specific templates separate: a Suica silhouette requirement does not imply an Amex logo arrangement.

One successful example used a 1200 × 757 design canvas, a radius of 38 and a 2× export of 2400 × 1514. Those are example measurements, not platform specifications. Real screenshots, target apps and device previews can require a different template.

For a circular rounded rectangle with outer radius `R` and a constant inset `d < R`, the concentric inner radius is `R - d`. With `R=38` and `d=24`, use `r=14`: top-left centres are `(38,38)` for both. If the reference has squircle or other custom curves, preserve its path instead of replacing it with this formula.

Use a closed inner contour and explicitly located separator intersections. Avoid nearly overlapping paths, duplicated strokes, inconsistent stroke widths, and rules that end a fraction short. A bottom strip should have deliberate vertical space for its microprint; it should not accidentally become a separately coloured rectangle.

Keep the application export and presentation silhouette distinct. AirCard application PNGs default to opaque, full-bleed rectangles with square outer corners; extend the artwork to every corner and let the destination clip it. Do not flatten a rounded card onto a solid matte and call it full bleed. Use one shared silhouette mask only for requested rounded exports or previews. Record the actual target measurements; neither 1200 × 757 nor a project's 1536 × 969 reference is a universal card specification.

## Identity and typography

- Prefer original SVG, EPS or native PDF vector paths. Preserve their aspect ratio and internal geometry.
- Separate logo lettering from supporting type. Do not retype a custom wordmark in a similar bold font.
- Use digital RGB assets for screen artwork; colours converted from a print PDF can differ from the intended digital colour.
- Select an optical logo variant by its intended display size, not merely the large export bitmap. Example: a mark 132 units wide on a 1200-unit card appears about 43 pixels wide in a 393-pixel preview. Check the brand's own guidance.
- Verify font family and weight. Load available fonts before editing Figma text; outline legitimately sourced type when reliable import requires it. Preserve an editable text copy when useful and available.
- Align visible letter shapes optically with the grid. ViewBox padding can make equal numeric positions look unequal.

For an unrotated SVG rendered at width `w`, let `v0` and `V` be its viewBox x-origin and width, and `a`/`b` the visible ink bounds. To align its visible left edge to `L`, place it at `x = L - w * (a - v0) / V`. For a right edge at `R`, use `x = R - w * (b - v0) / V`. Measure the paths or a high-resolution alpha rendering; do not include a background rectangle in the ink bounds. Preserve the lettering and verify the result visually at phone size. Numeric bounds are a starting point for optical alignment, not a reason to ignore what the eye sees.

Measure minimum clear space and logo size in the intended display, not only the large export. Follow the current issuer guide: a Revolut wordmark's treatment does not inherit AMEX's engraved frame or metallic effects. Do not invent a payment-network mark or chip when the brief does not specify one.

## Alpha and masks

Native transparency is the first choice. Inspect it on both light and dark backgrounds, including hair tips and fine props. Preserve colour and translucency; aggressive background removal can erase linework or turn pale wings into holes.

Inspect all four source edges before placement. Alpha does not guarantee a complete silhouette: hair can end abruptly at the source boundary. Find an uncropped original, change the composition, or align that pre-existing cut exactly with the outside card edge as an intentional bleed. Moving it into the interior exposes a hard cut. Do not describe missing illustration as restored or blur it away.

When blending a scene, distinguish the character from its background. Keep the face, hands and meaningful detail opaque. Feather background boundaries with a sufficiently broad gradient, combining horizontal and vertical masks when needed. A fade should never erase half a face or visibly dissolve a foot merely to make an oversized crop fit.

Resize and composite with an alpha-aware workflow. If dark or white halos appear, check premultiplication, RGB hidden under transparent pixels, matte colours and colour profiles. Do not solve every halo with more blur.

Extend atmosphere using source-compatible colour and texture. Avoid hard photo rectangles or an unrelated texture that contradicts the source's lighting. Background shapes can intentionally bleed beyond the card; cutting a character's distinctive silhouette needs a stronger compositional reason.

## Diagnose a visible join before widening the mask

1. Convert source assets with embedded profiles into one working colour space before sampling. Retain the originals and record the conversion; assigning a profile is not the same as converting colour.
2. Inspect the original source rectangle and both sides of the final join at native pixels. Sample nearby background regions without including the character, linework or signature.
3. Toggle grain, shadows, light washes and other overlays. Match the finished composite, not just the two base hex colours. Grain applied to only one side can recreate a rectangle after a seemingly correct colour match.
4. Match the atmosphere, then use a broad background-only transition with explicit foreground protection. Inspect pale linework as well as faces and hands; colour-distance masks can misclassify light artwork as paper.
5. Check for washed-out faces or lost detail beneath readability overlays. Reposition or resize the scene to create identity space before adding more white or dark wash.
6. If the source still reads as a pasted rectangle, reconsider the composition. A continuous full-bleed scene or intentional portrait crop at the outer canvas may work better than repeated feathering, edge extension or Poisson/multiband blending.

Compare seam crops and phone previews after each meaningful change. A small mean colour difference can hide a local edge or damaged hair; report it as a diagnostic only. Record failed treatments as rejected experiments so a future revision does not mistake them for the final recipe.

## SVG details that need real rendering checks

- Use `gradientUnits="userSpaceOnUse"` with explicit coordinates for gradients on horizontal or vertical hairlines. Object-bounding-box gradients can vanish when a path has zero width or height.
- Inline SVG class fills when importing into an editor with limited CSS support.
- Prefix IDs when combining SVG documents: mask, clip, gradient and filter IDs are document-global, even inside nested SVG elements.
- Keep identity paths and borders vector. Flatten only image effects or masks that do not survive the destination import reliably.
- Explicitly set image aspect handling and intended crop. Do not let a default FILL mode quietly change the composition.
- Inspect joins after export; a clean vector source is not proof that the rasterizer or Figma import rendered it correctly.

## CV when it answers a concrete question

Useful measurements include alpha bounds, source resolution, palette samples, background/foreground registration, connected components and edge continuity. For one star-field reconstruction, registration aligned a transparent character with the published scene, then a character exclusion mask let small bright sky details be sampled separately.

Use this only when the result needs it. Check alignment residuals and inspect the sampling mask. Do not blindly trust keypoint counts or copy character edges into a texture. Identify source-derived pixels, newly constructed geometry and inspired colour fields honestly.

## Detail-review plan

Specify crops in design coordinates before export: all four corners; both ends of each divider; the full bottom strip; primary and network logos; supporting type; face; hair/wing extremities; and each blend boundary. Use real exported or saved-editor pixels. Inspect both smooth enlarged views and nearest-neighbour pixels when diagnosing raster seams.
