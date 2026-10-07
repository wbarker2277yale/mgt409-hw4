# AI Prompts — Homework 4: Campus Customs Shop + Chatbot

A record of the prompts I used with the AI assistant for this assignment. Every prompt is written in my own words, not copied from the assignment site. Spelling and typos have been corrected. Where my original wording was unclear, a clarified version is shown in [brackets].

---

## Problem 1 — Vibe Coder Prompts

**Prompt 1:**
> Open the folder for Homework 4.

**Prompt 2:**
> Log matches earlier homeworks.
>
> [Clarified: Record the prompts in `AI_prompts.md`, in the same format as the prompt logs from Homework 3 and Homework 5.]

---

## Problem 2 — Analyze the Database

**Prompt:**
> Notes and database are the same. Data. Campus Customs. Prepare to grow the harness.
>
> [Clarified: Same setup as earlier homeworks: the Campus Customs data pack goes in `data/` and the notes go in `output/harness.md`, which will grow with each problem. The Homework 5 database lacks the `catalogue` and `users` tables, so the Homework 4 data pack (`campus_customs.db` plus the `products/` photos) was used. The harness lists every field of `catalogue`, `inventory`, and `users` and says why each matters to the shop or the chatbot.]

---

## Problem 3 — Build the Campus Customs Website

**Prompt:**
> Build the frontend. Scaffold, React, Vite, TypeScript. Needs a nav bar with the usual suspects for such a site.
>
> [Clarified: Nav bar with Home, Products, About Us, Log in, and Create account. The Products page shows every item from the database as a card with its photo; a chat button sits in the bottom-right corner as a placeholder until the agent is built.]

**Follow-up prompts:**
> Single item page needed.
>
> [Clarified: Clicking a product opens its own page, with a large photo on one side and its details on the other.]

> `backend/main.py` needed.
>
> [Clarified: A FastAPI backend in `backend/main.py` serves the products, stock, and photos from the database to the website.]

---

## Problem 4 — Create Account and Login

**Prompt:**
> The login needs to be usable via a test account.
>
> [Clarified: Make Log in and Create account work for real against the `users` table. The seeded test account (`test@campuscustoms.yale.edu`) must be able to log in, new accounts collect first name, last name, email, and password, and passwords are stored only as salted hashes. Notes go in `output/harness.md`.]

---

## Problem 5 — PydanticAI Agent Backend

**Prompt:**
> Make a PydanticAI agent backend, `backend/main.py`, with all the accoutrements needed. This will help `uvicorn main:app --reload --port 8000`.
>
> [Clarified: "Accoutrements" means the agent's files next to `main.py`: `prompts/prompt.md`, `agent.py`, `tools.py`, and `models.py`, plus a chat route that connects the chat widget to the agent. The backend runs from the `backend/` folder with `uvicorn main:app --reload --port 8000`.]

---

## Problem 6 — Tools: Product Info and Stock

**Prompt:**
> Six: tools, product info and stock.
>
> [Clarified: Give the agent tools that look up each product's real description, price, and stock (by size) in the database.]

**Follow-up prompt:**
> Agents need tools to give them real info. You need to find the tools, based on the rational needs of such an institution. Prompts and models need to be updated; likewise the harness.
>
> [Clarified: Beyond the basic lookups, choose the tools a campus shop's assistant actually needs (search, product info, stock by size, in-stock alternatives, what we carry), then update `prompts/prompt.md`, `models.py`, and `output/harness.md` to match. The original prompt named only the data to look up, not which tools a shop needs.]

---

## Problem 7 — Chat Search That Updates the Page

**Prompt:**
> Need a chat search that updates the page too, searching the catalogue.
>
> [Clarified: When a customer asks the chat about a kind of item, the agent searches the catalogue and the matching products appear on the website as product cards, and each card still opens its single-item page.]

---

## Problem 8 — Customer Memory

**Prompt:**
> Problem 8, customer memory. We need memory to tell us what shoppers did: what, when, where, why, tools, etc. Need some page context, and the agent context can have code. Guests may chat, but history is for logged-in users. Update the harness with how it's done.
>
> [Clarified: Save each logged-in shopper's chat in the database with what was said and shown, when, which page and product they were on (where), the agent's one-line reading of their goal (why), and the tools it used. Reload it when they return. Give the agent the shopper's name and email and the page they're on through code-written context, so "this" means the product on screen. Guests can chat, but nothing is saved.]

---

## Problem 9 — Usability Improvements

**Prompt:**
> Nine, usability improvements: once the core works, improve it via two front-end and two agent/backend improvements. Aesthetic improvements will give the shop a sixties, J. Press, Take Ivy kind of look. The improvements are for you to figure out. Simulate site use if you need to and find hiccups. Backend improvements should focus on quality, accuracy, and safety. `output/usability.md` is to be written prior to building; tell what is added and why it is good that you did so. Ensure the improvements actually exist in the app.
>
> [Clarified: Run a simulated shopping session to find real problems, write `output/usability.md` first, then build 2 front-end improvements (catalogue filters; context-aware quick questions) and 2 backend improvements (smarter search; a safety guard), and check each one in the running app.]

---

## Problem 10 — Style the Website

**Prompt:**
> Ten, style the website. You know what I like from previous runs. My usual imaginative design, if you please, but lean on the aesthetic comments above. Research the references I gave you thoroughly.
>
> [Clarified: A 1960s Ivy look drawn from J. Press (New Haven) and Take Ivy (1965), within my usual red-and-parchment style with illustrations drawn in code. `output/design.md` explains what changed and why it should help customers stay and buy.]

---

## Problem 11 — Site Testing (App Check)

**Prompt:**
> Problem 11, site testing: make a double-clickable HTML. Open it, run it, screenshot it at relevant points, and add captions. I want to see the chat checking an inventory level, the dynamic search result cards, and one of the additional abilities added in Problem 9.
>
> [Clarified: `output/app_check.html` with screenshots saved in `output/app_check_images/`, linked by relative paths, and a caption for each.]

**Follow-up prompts:**
> Make it easy to grade; you know how this class is graded from previous discussions. Use AI-friendly tags for everything.
>
> [Clarified: Give each check a heading, the steps, a captioned screenshot, and a "what this proves" line. Use semantic HTML with labeled sections and a machine-readable summary, so both people and AI graders can find each check. The first prompt didn't say how the page would be graded.]

> Open the frontend in my Safari, or the HTML page, or whatever.

> Open screenshots.

---

## Problem 12 — Audit Trail, Safety, Finish Harness

**Prompt:**
> Build in a sensible order per your above questions; I am working on getting these in text, and you can troubleshoot how to move through them. Problem 12: audit trail, safety, finish harness. Append-only `output/audit_trail.json`.

**Follow-up prompt:**
> Do not wipe between runs, and come up with safety rules (we have done this before; perhaps check what we have used before) and place them in `prompts/prompt.md`. Then finish the output harness so it is clear how it works. Include `models.py` to show fields and why they were chosen, tools, rules, specs, etc.
>
> [Clarified: The safety rules follow the pattern of Homework 3 and Homework 5 (numbered rules in groups; facts only from tools; messages are information, not instructions; no claims of Yale endorsement; only the personal details the task needs). The harness marks which rules are also enforced in code. The first prompt didn't say what the harness should cover.]

---

## Problem 13 — Push to GitHub and Submit the URL

**Prompt:**
> Then 13: we will publish to GitHub and submit the URL. Everything, all code, in a folder called `hw4`, and push to a public GitHub repo. Deliver me the repo URL I can place in Canvas. As always, security when publishing: no `.env`, no Campus Customs database, no images from the store. Use `.gitignore` with `.env.example`. For the layout, that shall be your guide. The agent itself is four files under `backend`: `prompts/prompt.md`, `agent.py`, `tools.py`, `models.py`. The README explains how the bow and stern ends interact.
>
> [Clarified: Sent with a screenshot of the assignment's required `hw4/` folder layout. "Bow and stern ends" means the frontend and the backend.]
