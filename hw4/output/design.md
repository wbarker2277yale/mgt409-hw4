# Design — "The Fall Catalogue"

Campus Customs sells Yale sweatshirts and tees, and most shops like it look like every other
Shopify template. We styled the site as a 1960s New Haven outfitter's catalogue, so it feels
like a place with a point of view. Every choice below is meant to make shoppers stay longer,
trust the shop, and get to the buy decision faster.

## References

- **J. Press, York Street, New Haven (founded 1902).** The clothier credited with "the Ivy
  League look": navy blazers, repp-stripe ties, Shetland "Shaggy Dog" sweaters, tweed, and
  printed catalogue brochures. We borrowed its navy, its regimental stripes, its tartan, and the
  catalogue's numbered, quiet layout.
- **Take Ivy (1965).** A Japanese photo book of candid campus snapshots (students on bikes, in
  the quad, at the boathouse) that taught a generation what Ivy style looked like. We borrowed
  its snapshot prints, typewritten captions, and the slightly faded color of 1960s film.
- **House style: red and parchment.** Cranberry and parchment lead; J. Press navy, old gold,
  and club green support.

## What changed, and why it should help customers stay and buy

| Area | What we did | Why it helps |
|---|---|---|
| **Color** | Parchment ground, cranberry for actions and prices, J. Press navy for headings, gold and green as accents. | The shop looks like Yale merch's natural home. One action color (cranberry) means every "buy-ward" element (prices, buttons, the clerk) is easy to spot. |
| **Type** | Caslon display for headlines (classic catalogue serif), Futura-style spaced capitals (Jost) for navigation and labels, a typewriter face (Courier Prime) for captions, style numbers, and the clerk. | A clear hierarchy: the product name reads first, then price, then details. The typewriter voice makes the chat feel like a person at a counter, not a widget. |
| **Masthead** | Navy strip ("New Haven, Conn. · Outfitters to the Elm City"), the crest and wordmark, small-caps navigation, and a **repp-stripe band** like a regimental tie. | It says "campus outfitter" in one glance and stays pinned while scrolling, so Products and the account are always one click away. |
| **Home cover** | "Dressed for the *Quad*." beside three **snapshot prints**: tilted, taped, with typewritten captions ("Fig. 1 — The big YALE hoodie, Cross Campus, 8:50 a.m."). A felt pennant flutters in front. | Shows real products in a scene, the way Take Ivy showed clothes on campus. A shopper imagines wearing the hoodie rather than reading a spec sheet. Each print links to its product. |
| **Departments** | Five numbered plates (I–V) with a one-line blurb, the number of styles, and the "from" price, each opening the filtered catalogue. | Answers "what do you have and what does it cost?" before the first click; two clicks from home to a filtered shelf. |
| **Product plates** | Photos in a white print border, toned like a printed catalogue, that **bloom to full color on hover**. A **hang tag** with the price swings and turns cranberry. A catalogue style number (No. 017) sits over each name. | Motion responds to the shopper's attention: the item they point at comes alive. The price is always visible on the tag, so there are no hidden-price clicks. |
| **Item page** | A matted photo with a caption, a large cranberry price, **fabric swatches** for each color, and an **"on hand" ledger** (size, leader dots, quantity) with a red **SOLD OUT** stamp on empty sizes. | Stock by size is the last question before buying; the ledger answers it at a glance and is honest about what's gone. Swatches show color faster than words. |
| **The clerk (chat)** | A pennant reading **Ask the Clerk** that flutters bottom-right. The panel is "The Counter": navy header, gold rule, ruled notepad paper, typewritten clerk replies, cranberry customer slips, and one-tap question chips. | A friendly, findable assistant raises engagement, and every answer comes from real stock and prices. The chips cut the "what do I ask?" hesitation. |
| **Chat results** | "A note from the clerk · you asked '…'" banner with a big match count above the cards. | The shopper sees that the page changed because of their question, and can always get back to everything. |
| **Forms** | Log in and Create account sit on a ruled **index card** with a red margin line. | Familiar and calm. Sign-up feels like filling in a card at the counter, not a security checkpoint. |
| **Footer** | A woven **tartan band** (navy, green, cranberry, gold overchecks) and the note "An independent student shop, not an official Yale store." | Finishes the look, and the honest affiliation line builds trust. |

## Motion, kept purposeful

- Pages fade up on arrival, and product plates arrive in a short stagger, so the eye moves top-left to bottom-right through the shelf.
- The hang tag swings, and the photo blooms to color, only on hover.
- The pennant flutters slowly at rest and quickly on hover.
- The chat panel opens with a small spring from the corner.
- All motion turns off for shoppers who set "reduce motion".

## Built in code, not images

The crest, pennants, repp stripe, tartan, paper grain, ruled paper, hang tags, ledger dots, and
sold-out stamp are all SVG or CSS. The only images on the site are the shop's own product photos.
The look stays sharp at any size and adds no image downloads.

Files: `frontend/src/index.css` (the whole look), `frontend/src/components/Ornaments.tsx`
(crest and pennant), `NavBar.tsx`, `Footer.tsx`, `ProductCard.tsx`, `ChatWidget.tsx`, and the pages
in `frontend/src/pages/`.
