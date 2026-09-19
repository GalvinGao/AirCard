# Feedback and worked examples

| Feedback | Inspect | Targeted response |
|---|---|---|
| “The corner feels off” | Outer shape, inset, curve centres, stroke position, screenshot shadow | Correct the measured construction; inspect all four corners |
| “These lines don't align” | Endpoints, shared coordinates, duplicate paths, optical baseline, raster output | Unify the paths or exact joins and inspect both ends |
| “Wrong font” | Custom logo versus supporting font, exact font/weight, digital asset variant | Obtain original lettering and verify supporting type; do not just choose another similar font |
| “Why is the footer a different colour?” | Background rectangles, image endpoints, layer opacity, profile differences | Continue the actual background through the strip; keep rules and microprint separate |
| “Use a starry background like the official site” | The site's real main visual and artist context | Build from the relevant sky, palette and trails; do not substitute an unrelated horizon |
| “Swap left and right” | Figure direction, identity hierarchy, arm/hair space, protected logo orientation | Move the groups while preserving the original art orientation unless mirroring is explicitly appropriate |
| “Avoid hard crops” | Source boundaries, hair/props, feet, scene edges and alpha halos | Recompose first, then feather background transitions without erasing the subject |
| “I can still see the gap” | Final colour and texture on both sides, source-rectangle bounds, mask endpoint | Match the complete effect stack; protect foreground detail; change the composition if blending cannot remove the inset |
| “The logos don't look aligned” | Visible ink bounds, empty viewBox space, visual weight and clear space | Align visible letter shapes, then verify at phone size; preserve the original vector lettering |
| “Remove that caption” | Exact caption nodes and all current exports | Delete those nodes only; preserve the main identity; regenerate previews and package |
| “Research more deeply” | Unexplained motifs, guessed type, missing template details, weak source selection | Inspect primary references and alternatives until they explain actual choices, not until a search quota is met |

## Example: a restrained anniversary illustration

The useful information was not just “Miku has teal hair.” The official concept described wings built from tools for visual creation and sound. Costume and wing sheets explained the intricate silhouette. A pale composition retained that whole silhouette and allowed the illustration's detail to be the main event. A separate birthday caption was later removed at the user's request while the main Miku identity remained.

Transferable lesson: source context should shape preservation and placement, but source marketing copy does not become a compulsory label.

## Example: an asymmetric dark card

Gold-lit orchestral artwork supported a dark material and a vertical issuer spine. A free-floating divider initially lacked a coherent endpoint. Joining it to the frame improved the structure; changing its gradient to user-space coordinates also fixed a zero-width-path rendering failure.

Transferable lesson: diagnose both the visual relationship and the renderer. A numerical position alone is not proof of a visible line.

## Example: reversing a night composition

The revised composition placed an unmirrored figure on the right, facing the left-hand identity. Its source campaign used a star field and circular trails, so an unrelated watery reflection was removed. The new background used source-informed stars, new trail geometry and the original transparent character.

Transferable lesson: changing hierarchy and scene logic matters more than tinting the previous layout blue.

## Example: introducing a different illustrator

A travel-guide illustration created a bright fourth direction. A full silhouette remained readable at phone size, while busier postcard and ensemble alternatives did not. A real campaign plane asset was aligned with the tangent of a route rather than placed as an arbitrary sticker.

Transferable lesson: a new direction needs a reason, and even a small official motif still needs careful placement.

## Example: paper that matched before the effects

In a Kieed console composition, the illustration's ivory paper matched the sampled base. A translucent grey grain layer applied only to the surrounding base then darkened it, exposing the original picture rectangle. Removing that mismatch and broadening a background-only mask eliminated the visible join while preserving the console, face and signature.

Transferable lesson: compare colours after the whole layer stack. More feathering cannot reliably fix different surface treatments. Inspect both native-pixel boundary crops and the complete card.

## Example: transparent artwork with a cropped edge

A Tiv illustration had native alpha but its right-hand hair was already cut by the source image. Placing that cut inside the card made a conspicuous vertical edge. Moving the composition so the source cut met the outer card edge produced an intentional bleed while retaining the available illustration.

Transferable lesson: inspect the source silhouette before building a layout around it. Transparency is not evidence that every strand or prop is present.

## Example: a composition that needed to change

A Rella AMEX composition placed a bright-to-dark scene inside a differently lit field. Feathering, edge extension and Poisson/multiband experiments still looked pasted in and were rejected. A continuous full-bleed portrait removed the interior picture boundary. The identity then aligned to the actual Miku logo ink rather than the padded SVG box.

Transferable lesson: stop treating every composition problem as a mask problem. Intentional outer-edge cropping and protected negative space can preserve the illustration better than progressively dissolving it.

## Example: restoring the original face lighting

A panoramic Rella scene gained a pale overlay to make room for the Revolut wordmark. The overlay also washed out the faces. Removing it and adjusting the scene position and brand clear space retained the original lighting and improved hierarchy.

Transferable lesson: solve space and placement before changing the artist's local contrast. Reinspect faces whenever readability layers change.
