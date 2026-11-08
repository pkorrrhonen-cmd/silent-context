# Retrospective: what the two entries ahead of us did, read from their public repositories

Written 8.11.2026 evening, after the result. Elisa's own top three at Since AI 2026: Kaiku first, Knownstate second,
Silent context third, of fifteen entries. Elisa's reviewers said they held one bar across usability, linking
precision, time validity and overall readiness, with a few hours for fifteen repositories, demos, videos and
documents. This page reads the two repositories ahead of us against that bar, so the next hackathon starts from it.
Everything here is from the public repositories as they stood on 8.11.2026; nothing was run. Author: Petri Korhonen.

| | Kaiku (1st) | Knownstate (2nd) | Silent context (3rd) |
|---|---|---|---|
| Repository | [alexisselorm/pauwer_elisa_hackathon](https://github.com/alexisselorm/pauwer_elisa_hackathon) | [silvekoski/knownstate](https://github.com/silvekoski/knownstate) | this one |
| Team | two people, 113 commits over the weekend | one person, published as one commit on Sunday | one person with AI tools, 73 commits |
| Size | 443 files, about 33 000 lines of Python and TypeScript, 38 test files | 352 files, about 13 700 lines of TypeScript, 203 tests, 55 eval cases | 160 tests, a truth set of 13 and a held-out set of 16 |
| Where it runs | Docker Compose on your machine, a Slack workspace and a Featherless key; 30 minutes for the first run | live on an OpenShift sandbox with live models, Tiger Cloud Postgres | the page with recorded answers, no key; a hosted copy on Cloudflare |
| Capture | a Slack bot watches channels live; a resolved or idle thread is triaged by a small model and extracted by a chat model; one card appears in the thread; an email drop folder, Teams backfill, PDF, Confluence and ITSM pages through the same path | every message read twice by a fine-tuned 2B classifier (alone, and with the ten previous), the selected windows to Kimi; Teams, Slack, email and PDF | one model call per thread on the exports as they are; the answers recorded |
| Binding | six gates in code: every field quotes the source verbatim, a rule must come from an answer, the entity must exist at valid_from, the symptoms are checked against telemetry, the time invariants run in the write's transaction, a second channel corroborates instead of duplicating | a rule from the inventory, not the chat: `model = 'TX-3000' AND firmware < '4.2'` with anchors and basis; a low-confidence binding becomes a one-click question | code-only binding to a unit in the graph, the wording of which units it covers kept verbatim; an unclear binding waits with its reason |
| Time | five layers in Neo4j (as-designed, as-built, as-running, context, events), every query at an instant and "as known at" a second instant | valid_from and valid_to on every fact, every query filtered by them, superseded kept; a firmware upgrade closes the entity row | two clocks per claim (world time and information time), evidence as dated events, a time axis on the page |
| Trust and learning | the network confirms the knowledge: an outcome reported over MCP, the telemetry decides, confidence is Beta(1 + support, 1 + refute) | confidence shown as a number, 46 % before the expert's click and 77 % after; conflicting experts kept as conflicting; a wrong answer becomes a regression eval case | evidence events (told, success, failure, disputed, superseded); outcomes from device events; no numbers shown as confidence by design |
| The specialist's extra work | none at capture; the card's buttons are optional | one-click questions in the author's own thread, 17 questions for 29 assertions in a fresh seed | none, ever (decision P6): the system never starts a conversation |
| For the agent | 13 MCP tools with a bearer token per agent, every write an event with the agent id; a Slack ops agent as the reference client; a network simulator with fault injection | MCP `get_context`, `get_telemetry`, `record_outcome`; an ElevenLabs voice agent; the chat is a client of the same tools | `claims_for`, `access_for`, `source` as MCP tools; a policy on who acts; no write path to any device |
| Evaluation shown | a committed held-out eval on the console's scorecard: Elisa's example 4/6, held-out capture 4/9, held-out questions 8/12, with every failed check listed | an evals dashboard in the app: 55 cases, score 0.92, cutoff and half-life sweeps; the slides say plainly what was not run | numbers in the README and acceptance.md: 13/13 found, 9/9 merged, 1 of 16 held-out bindings wrong |
| Extras | a recap video and a technical PDF in the repository; five plan documents, the time model verified against the brief's words | a 3D demo game with the app as the phone in the engineer's hand; three partner awards entered (Tiger Data, ElevenLabs, Red Hat); a PRD that cites a review session with Elisa by the minute | a page of thirteen scenes, two videos, two decks, a hosted copy |

## What the bar rewarded

**Usability was the primary criterion, and both winners built something a person types into.** Knownstate opens
with one text box: "What are you stuck on?", three example questions, and an answer that begins "Do this". Kaiku
lives where the engineers already are: the card appears in the Slack thread they were typing in, and the ops agent
answers in the alarm thread. Silent context is a page of scenes that tells the story well, but a judge cannot ask it
a question. The story format served the video and the jury's reading; it did not serve the "could I use this"
test.

**Readiness meant live.** Knownstate ran live models on a live deployment with a live database. Kaiku ran a live
Slack bot, a simulator and real models behind one key. Silent context ran with no model and no key on purpose, so a
judge could run it anywhere; the same choice read as a prototype with recorded answers next to two systems that
were capturing while the judge watched. Keep the keyless path, but ship the live path too.

**Linking precision was argued with evidence in the product.** Kaiku's six gates and Knownstate's inventory rules
answer the question "why did it bind here" on screen, and both show held-out evals inside the product, failures
included. Our held-out set and acceptance table are as honest, but they live in documents.

**The brief allowed one-click questions, and both winners used them.** Knownstate's PRD quotes the brief: the
specialists must get no extra work, except one-click questions. We decided P6, never, and drafted the question for a
person to send instead. That was a stricter reading than the brief asked for, and it cost usability: a one-click
confirmation in the author's own thread is the brief's own picture of the specialist's role.

**Both winners talked to Elisa during the event.** Knownstate's PRD cites a review session with Elisa by the
minute ("Elisa said that this solution catches the idea of the challenge very well") and a graph talk at the venue.
Kaiku's first plan verifies the time model against the brief's words. We worked from the brief and the example files
alone, away from the venue; the reviewers' note names the Q&A stand as where the good questions were asked.

**Partner technologies did not decide Elisa's ranking.** Kaiku entered none and won. Knownstate entered three
awards and says in its PRD that they do not change the Elisa evaluation. A FIWARE entry named Kaiku exists in the
same event, but it is a Fonecta challenge entry by another team ([oroomi/kaiku](https://github.com/oroomi/kaiku)),
not Elisa's winner.

## The layer we built, in the owner's words

We drew the boundary ourselves, and too tightly. We built more network automation: the agent that acts under a policy
for the autonomous network, the claims it reads, the prohibition in code. The winners built more of the tool the
field engineer holds: chat-like tools for the people on call, where the knowledge is collected and where it is
read back. The work sat one layer apart, and the jury judged the layer people touch every day: usability, and for
whom the product is. The next brief is read from several vantage points before the boundary is drawn: who touches
this daily, who collects, who decides, and what the judge can do with it in two minutes.

## What to keep from ours

The decision record, the truth set written before the rules, the held-out set the rule author never read, the two
clocks, the policy on who acts, no write path to devices, the claim in the expert's own words with its source, the
"left out on purpose" list, and the reading of the brief as a product for named people. Both winners did several of
these too; they are the floor, not the difference.

## For the next hackathon

1. Build the thing a judge types into first, live, with a real model behind it, and keep the keyless fallback as a
   second path. A story page or a video is the explanation, not the product.
2. Capture from a real channel during the event. A Slack app in Socket Mode needs no public address and makes the
   "it appeared in my thread" moment real.
3. Read the brief for what it allows, not only for what it forbids, and order the pitch by its evaluation criteria in
   the order the brief gives them.
4. Put the evals inside the product: a scorecard page with the failures expanded is worth more than the same numbers
   in a document.
5. Talk to the challenge owner at the stand on the first evening, and write down what they said with the time.
6. Enter the partner awards whose technology the build uses anyway; they are separate prizes and separate visibility.
7. A team of two shipped about three times the code of a solo entry in the same hours; a solo entry with AI tools
   placed second with a live deployment. Scope the solo entry to one live path done fully.
