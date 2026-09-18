# Compositing and geometry

## Measure one reusable template

Record design width/height, outer clipping shape, corner construction, inner frame, safe area, logo bounds, bottom strip and export scale. Derive these from the supplied reference and target. Keep issuer-specific templates separate: a Suica silhouette requirement does not imply an Amex logo arrangement.

One successful example used a 1200 × 757 design canvas, a radius of 38 and a 2× export of 2400 × 1514. Those are example measurements, not platform specifications. Real screenshots, target apps and device previews can require a different template.

For a circular rounded rectangle with outer radius `R` and a constant inset `d < R`, the concentric inner radius is `R - d`. With `R=38` and `d=24`, use `r=14`: top-left centres are `(38,38)` for both. If the reference has squircle or other custom curves, preserve its path instead of replacing it with this formula.

Use a closed inner contour and explicitly located separator intersections. Avoid nearly overlapping paths, duplicated strokes, inconsistent stroke widths, and rules that end a fraction short. A bottom strip should have deliberate vertical space for its microprint; it should not accidentally become a separately coloured rectangle.

Apply the same final silhouette mask to all rounded exports. Backgrounds should remain opaque inside it unless intentional translucency is part of the brief. Keep the opaque full-bleed image separate when the destination clips corners itself.

## Identity and typography

- Prefer original SVG, EPS or native PDF vector paths. Preserve their aspect ratio and internal geometry.
- Separate logo lettering from supporting type. Do not retype a custom wordmark in a similar bold font.
- Use digital RGB assets for screen artwork; colours converted from a print PDF can differ from the intended digital colour.
- Select an optical logo variant by its intended display size, not merely the large export bitmap. Example: a mark 132 units wide on a 1200-unit card appears about 43 pixels wide in a 393-pixel preview. Check the brand's own guidance.
- Verify font family and weight. Load available fonts before editing Figma text; outline legitimately sourced type when reliable import requires it. Preserve an editable text copy when useful and available.
- Align visible letter shapes optically with the grid. ViewBox padding can make equal numeric positions look unequal.

## Alpha and masks

Native transparency is the first choice. Inspect it on both light and dark backgrounds, including hair tips and fine props. Preserve colour and translucency; aggressive background removal can erase linework or turn pale wings into holes.

When blending a scene, distinguish the character from its background. Keep the face, hands and meaningful detail opaque. Feather background boundaries with a sufficiently broad gradient, combining horizontal and vertical masks when needed. A fade should never erase half a face or visibly dissolve a foot merely to make an oversized crop fit.

Resize and composite with an alpha-aware workflow. If dark or white halos appear, check premultiplication, RGB hidden under transparent pixels, matte colours and colour profiles. Do not solve every halo with more blur.

Extend atmosphere using source-compatible colour and texture. Avoid hard photo rectangles or an unrelated texture that contradicts the source's lighting. Background shapes can intentionally bleed beyond the card; cutting a character's distinctive silhouette needs a stronger compositional reason.

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
