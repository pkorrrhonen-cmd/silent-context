# Slides: outline, v1

**The deck exists:** `silent-context.pptx` and `silent-context.pdf` in [`slides/`](slides/), built on 7.11.2026 from this outline
by the session; what changed on the way is in [`DECISIONS.md`](DECISIONS.md) rows 15 to 17 and [`CHANGELOG.md`](CHANGELOG.md).
The deck is written by the scripts in [`slides/build/`](slides/build/), so a change to the words is a change to
`deck.js` and a rebuild; its README says how.

A draft for the owner, 7.11.2026, following the build plan's section 6: eight to ten slides, in English,
plain words, nothing the data does not carry. Every number comes from [`acceptance.md`](acceptance.md),
[`CHANGELOG.md`](CHANGELOG.md) or the README. The owner turns this into the deck in his own tool.

## 1. The problem, in Elisa's words

- Field engineers and network experts learn how a fault behaves. That knowledge stays in their
  conversations and emails.
- The task: capture it without extra work, tie it to the right network entities with its source and its
  period of validity, and let an agent use it the next time a similar case appears.
- Elisa's own example: an SFP replaced on TRN-042, the link up, the counters at zero, and one expert who
  knows what to do.

## 2. Silent context, in one picture

- Reads Teams and email exports exactly as written. Nobody fills in anything.
- Turns advice into **context claims** tied to the graph, each with its source, the expert's own words
  about which units it covers, and two clocks: when it holds in the world, and when we learned it.
- Gives an agent one call, `claims_for`: propose, check first, or "I don't know" with who to ask.
- The page: the demo at `http://127.0.0.1:8000`, ten scenes, no model and no key.

## 3. Capture and bind

- One model call per thread reports what the text says. An identifier counts only if it is literally in
  the text; code binds it to the graph, and the model never picks an entity.
- An unclear binding waits with its reason: no unit named, several could fit, an unknown id, a
  contradicting context. It may wait forever. The system never asks anyone.
- One person's accounts become one claim with several sources. A relay is a source, not a telling.

## 4. The data model

- Claim text in the speaker's words, with "sometimes" and "usually" kept.
- The entity it was seen on, and apart from it the scope: wording verbatim, status confirmed or undefined.
- World time and information time apart. Unknown time stays unknown. No age limit from "around 2019".
- Evidence as events with a date and a link: told, reported success, reported failure, disputed,
  superseded. Rendered from a template: no counts, no percentages, no figure per person.
- Status is computed at read time for a claim and a unit, never stored.

## 5. The agent

- Three tiers from rules: propose when a success is reported on this unit's class, no disagreement, and
  the claim's own check holds; check first when only told, in doubt, a guess, or disputed; I don't know
  with the group to ask, and the gap logged.
- One prohibition in code: no reboot or hardware replacement before a failed bounce is reported.
- The agent reads counters from telemetry itself when a recent sample exists.
- What a person did and the outcome fill in from device events. Nobody reports.

## 6. What was measured

- 154 tests, all with no key (the README's "What was tested" is the source; this outline first said 152).
- Truth set, 11 sources: found 11/11, merged 7/7, entity 4/4, scope 4/4, time 7/7, evidence 6/6.
- Held-out binding set, 16 synthetic sources the rule author has not read: 1 of 16 confidently wrong in
  the recorded run; 0, 0, 0, 1, 1 in five repeats with the prompt unchanged, the same file each time.
- Acceptance cases A0 to A11: 20 computed rows, 20 hold ([`acceptance.md`](acceptance.md)).
- Clean install from the README with no key: passed. Cypher export loaded into Neo4j with no edits.
- These numbers describe this synthetic data only.

## 7. Elisa's question: is the information fact?

- The answer is a claim's origin, what was reported about it, and when it was last confirmed. Not a
  score for the person.
- Why no person scores: an employee assessment it was never meant to be, personal data it does not
  need, and a source that dries up once it is graded.
- Why no counts: "confirmed twice" invites a trust the data does not carry. The events are listed; the
  reader counts if they want to.

## 8. What is real, what is simulated

- Real: Elisa's two files unchanged; the model's reading, recorded; binding, dating and merging in code;
  the agent, live; the exports.
- Simulated: every other source, the dates, the event stream, the telemetry, the graph, the clock, the
  channels. No real network, channel or person.
- Not built on purpose: asking the expert at the moment of need; matching Elisa's own graph; a semantic
  symptom match; acting on the network ([`what-is-simulated.md`](what-is-simulated.md)).

## 9. What comes next

- The question at the moment of need, as a continuation of the gap log: Elisa's own line, "if the agent
  does not know, a person can ask Erkki". A Teams message or a 20-second call when Erkki is driving away
  from the site. Not built, because synthetic data cannot show it is not extra work.
- A question budget and situation conditions, so the asking never becomes the extra work it replaces.
- An autonomy policy: certainty is necessary, never sufficient. The log of proposed, done and outcome is
  the record that decision needs.
- For production at Elisa: schema matching against the inventory graph, channel connectors, a semantic
  symptom match.

## 10. The limits, said plainly

- The system never starts a conversation with a specialist.
- It shows the origin of a claim and what was reported about it, not the truth.
- It scores claims, not people.
- Telling apart which units a claim applies to, before someone narrows it down, rests on synthetic data.
