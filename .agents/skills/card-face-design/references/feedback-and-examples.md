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
