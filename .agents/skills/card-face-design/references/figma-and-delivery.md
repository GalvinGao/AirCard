# Figma and delivery

## Edit the user's actual file

Use the requested file/page and inspect it before writing. Discover current node IDs, selection, names, parentage, dimensions and nearby space. Do not copy a file key or node ID from a previous job. If the user says Personal Draft, find that actual file rather than making another file with the same name.

Use the available Figma plugin for precise edits. Load the applicable Figma skill and current tool documentation before invoking its API. Keep requests small, await asynchronous operations, return affected IDs and keep workflow metadata outside the design file. Verify available font styles before changing text.

For a fresh collection, preserve the previous board when useful and create the revised collection in clear space. For a small correction, modify the existing nodes in place. Do not duplicate an entire collection to delete one caption.

## Import and structure

Keep the card as layered artwork: base material, source illustration/mask, identity vectors, border/strip and optional approved details. A bitmap image layer is appropriate for an illustration; rasterising the entire card needlessly makes logos and geometry harder to refine.

Use native vector import for SVG assets. Follow the upload tool's current limits and returned instructions; record which local asset maps to each returned node. Upload all issued single-use URLs before requesting a new batch when the tool requires it. Never store expiring upload URLs in the delivery archive.

An upload may land on the first page rather than the requested page. Inspect the returned node's parent and explicitly move it to the intended page. Native card dimensions and aspect ratio should match the source after import.

Use auto layout for a comparison board's rows, labels, captions and cards. Use intentional absolute positioning inside the card artwork. Preserve visual layer names and leave sufficient space between options for a fair comparison.

## Verify the persisted rendering

1. Re-read dimensions and placement after editing.
2. Render the saved card and collection from Figma.
3. Verify image downloads are nonempty, have the expected content type and decode successfully. Follow the tool's download instructions; if required by the image endpoint, use a normal browser user agent.
4. Inspect the complete card, intended phone size, and enlarged problem areas. Check masks, gradient rules, logo paths, strip continuity and cropped artwork.
5. Compare against the local renderer. Small antialiasing differences are normal; a low average pixel difference does not excuse a missing small logo or line.
6. Fix the affected nodes and the reproducible source, then refresh only the relevant verification.

If Figma access is unavailable, finish the local editable artifacts and report exactly which step remains unavailable. Do not claim a file was edited based solely on an exported SVG or a successful upload response. Do not work around an explicit permission or safety denial using another route.

## Package the collection

Typical deliverables are high-resolution PNGs, opaque full-bleed variants when useful, editable SVG/Figma sources, a small comparison sheet, and concise source credits. Keep phone chrome and presentation shadows out of the application images.

Avoid shipping raw font downloads, temporary upload URLs, browser state or unrelated research files. Include enough provenance to locate the source assets again. A technical review report should say what it checked and leave aesthetic judgement to the actual visual inspection.

For follow-up feedback, update every current representation: source code, Figma nodes, PNG/SVG exports, previews, detail sheets, README claims and the archive. Historical reference boards may remain clearly labelled as previous versions; current download links must contain the current design.

Report the design outcome, verification and links briefly. Do not claim a skin is applied to a device unless that separate action was requested and observed.
