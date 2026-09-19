# Reference reconstruction and validation

Use this workflow when a brief calls for faithful restoration of an existing card element. A new composition may retain selected issuer features without copying the entire reference. Decide which elements must match before measuring them.

## Establish a clean reference

Prefer the supplied native card bitmap to a photographed screen. Preserve it unchanged, record dimensions and profile, and separate foreground ink from substrate colour and brushed texture. For screenshots, isolate the card and correct perspective before measuring. Do not include the phone UI, drop shadow or selected-object outline.

Make a component inventory: main wordmark, four corners, horizontal and vertical border repeats, inner frame, background tile, bottom microlettering, copyright/signature and any marks the user wants removed. Inspect all of them at native resolution and enlarged scale. A well-matched top edge cannot compensate for an omitted bottom strip.

## Rebuild a coherent vector system

1. Obtain original issuer vectors first. Preserve native lettering when available; supporting type and custom wordmarks need separate treatment.
2. Measure inset, stroke width, corner centres, repeat period, baseline and joins in a single reference coordinate system. Separate perspective or scan distortion from intentional geometry.
3. When the user requires a redraw from scratch, use CV to locate edges and estimate geometry, then build clean vector paths, reusable motifs and explicit transforms. An embedded bitmap, raster alpha mask or unchecked auto-trace does not meet that requirement.
4. Reconstruct one repeat and test its seam before extending the frame or background. Keep corners and adjoining repeats phase-aligned. Rebuild guilloche curves and lettering as distinct elements so spacing and contrast remain adjustable.
5. For microlettering, verify the actual string, glyph form, width, spacing and baseline. A look-alike font can be wrong even when it fills the same rectangle. Outline verified type where needed; identify any approximation honestly.
6. Keep the vector restoration separate from the card's raster illustration and optional material texture. Check that the reconstructed component contains no embedded raster, including nested image references.

## Compare independently

Render the new vector at a higher scale and downsample to the reference grid. Register using stable landmarks and report the transform; do not warp the output to disguise a geometric error. Extract the reference ink mask independently rather than comparing the vector with a mask derived from itself.

For each component, save the reference crop, rendered crop, overlay and difference. Useful measurements are ink intersection-over-union, symmetric edge distance in reference pixels, repeat pitch, baseline offset and visible-ink bounds. Thin microtext is sensitive to thresholding and antialiasing, so use edge distance and enlarged crops alongside overlap. Report mean and high-percentile edge error rather than one aggregate score.

Inspect the four corners, the top-to-side joins, repeated seams, both ends of the bottom strip and representative background tiles at 200–400%, then inspect the complete design at phone size. Metrics diagnose errors; they are not acceptance thresholds. A high frame score does not prove the wordmark, footer or background is correct.

After changing colour or combining the restoration with illustration, check again for interrupted borders, weak microtext, a differently coloured footer, or an artwork layer hiding a required detail. Repeat the affected checks on the saved Figma export as well as the local rendering.

## Evidence to retain

- Reference identity, original dimensions, measured construction and the elements intentionally omitted.
- Editable geometry, source script and any fitted type details.
- Component comparisons, method and units; no unsupported claim of exact restoration.
- Phone-size and enlarged visual review, plus saved-editor comparison.

Keep project-specific scores in that project's report. Do not turn one AMEX reconstruction's overlap percentage, canvas size or font fit into a general requirement for another issuer.
