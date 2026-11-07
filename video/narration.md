# Silent context: the video's narration, v1

**State:** v1, 7.11.2026, a draft for the owner's review; not yet voiced. One block per scene in the form the
aligner parses (`VIDEO-RULEBOOK.md` §3, whole seconds), at about 2.5 words a second with room for the
picture's beats. The owner's rule for this video (`docs/DECISIONS.md` row 10): the whole idea is clear in the
first 20 seconds, how it happens is shown after that as a short clear presentation, and at about 60 seconds
the viewer has fully grasped what this is. Block 01 is the 20 seconds; blocks 02 to 05 bring the viewer to
66 seconds; the rest show the harder cases and the limits. Nothing is sped up: the page moves between
scenes in well under a second, so no speed-up is said on screen.

Voice (rulebook §11): impersonal throughout, no "I". Content rules (`SINCEAI-2026-VIDEO`): what works,
what is simulated and what is future are said in block 11; no confidential data, no made-up numbers.

Total: 351 words over 129 s, about 2.7 words a second.

Pronunciation: TRN as the letters "T R N"; SFP as the letters "S F P"; Nilo "NEE-lo"; Elisa "EH-lee-sa".

The picture for each block is a scene of the page (`scenes.py`): block 01 shows scene 4, the agent proposing;
blocks 02 to 11 show scenes 1 to 10 in order.

---
## 01 · The whole thing · 20 s · 55 words

Network experts solve faults in chats and emails, and the knowledge stays there. Silent context reads those messages exactly as they are, turns the advice into claims tied to the network, each with its source and how long it holds, and gives an agent one call: what to do next, and where that came from.

## 02 · The gap · 10 s · 28 words

Before anything is captured, the agent is asked about a unit whose link is up but carries no traffic. It does not know, and says who to ask.

## 03 · Capture · 10 s · 28 words

The same fault was solved a week earlier, in a Teams thread and an email. Both are read exactly as written. Nobody fills in anything for the system.

## 04 · Bind · 13 s · 38 words

The advice becomes one claim: what to check and what to do. It is tied to the unit, keeps the expert's own words on which units it covers, and is dated from the moment the module was replaced.

## 05 · Use · 13 s · 37 words

Now the same fault on another unit of the same class. The agent reads the counters from the device itself, proposes the expert's step with its source, and holds back a reboot until a bounce has failed.

## 06 · Learn · 8 s · 20 words

What a person did, and what happened, comes from the device events. The record fills itself in. Nobody reported anything.

## 07 · Ageing · 10 s · 27 words

A firmware update on one unit puts the advice in doubt for that unit only. The agent asks to check again there. Nothing expires by a calendar.

## 08 · Not for all · 10 s · 24 words

On a newer unit the step did not help, and the expert narrowed the advice. The agent stops offering it there, and says why.

## 09 · Disagree · 9 s · 23 words

When two experts disagree, both stay visible with their sources. The agent does not pick a side. It asks for the counters first.

## 10 · The barrier · 8 s · 20 words

Before anyone drives to a site: where the key is now, who said so, and how old that information is.

## 11 · The limits · 18 s · 51 words

What this does not claim. It never starts a conversation with a specialist. It shows where a claim came from and what was reported, not the truth. It scores claims, never people. Everything except Elisa's two example files is simulated. Asking the expert at the moment of need is not built.
