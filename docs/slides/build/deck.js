// The slides for the Since AI 2026 submission of Silent context, from docs/slides.md, in the page's own look.
// Builds docs/slides/silent-context.pptx. Every number and sentence comes from README.md, docs/acceptance.md,
// docs/what-is-simulated.md, docs/product.md or video/narration.md.
const pptxgen = require("pptxgenjs");
const path = require("path");
// Writes the theme colours into the deck, because pptxgenjs cannot: until this runs, scheme colours resolve to
// Office's stock palette.
async function applyTheme(file, theme) {
  const fs = require("fs");
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  const c = theme.colors;
  const slot = (name) => `<a:${name}><a:srgbClr val="${c[name]}"/></a:${name}>`;
  const names = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const scheme = `<a:clrScheme name="${theme.name}">` + names.map(slot).join("") + "</a:clrScheme>";
  const xml = (await zip.file(part).async("string")).replace(/<a:clrScheme[\s\S]*?<\/a:clrScheme>/, scheme);
  zip.file(part, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

const OUT = process.argv[2];
const SHOTS = path.join(__dirname, "shots");

const THEME = {
  name: "Silent context",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    // Light since 7.11.2026 evening, the same tokens as web/style.css: Elisa's blue, orange and greys, measured from elisa.fi.
    dk1: "171C43", lt1: "EFEFF1", dk2: "70707A", lt2: "FFFFFF",
    accent1: "005FED", accent2: "FF6400", accent3: "008253", accent4: "A8690F", accent5: "5B7A96", accent6: "E0022A",
    hlink: "005FED", folHlink: "064AAC",
  },
};
const BG = "EFEFF1", PANEL = "FFFFFF", RAISED = "F6F6F7", LINE = "D2D2D6", FAINT = "8D8D95";
const MONO = "Consolas";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Petri Korhonen";
pres.title = "Silent context";
pres.subject = "Since AI 2026, Elisa's challenge";
const C = pres.SchemeColor;

const W = 13.333, ML = 0.6, CW = W - 2 * ML; // content width 12.133
const FOOT = "Silent context · Since AI 2026 · Elisa's challenge";

function footer(y = 6.98) {
  return { text: { text: FOOT, options: { x: ML, y, w: 9, h: 0.3, fontFace: MONO, fontSize: 10, color: FAINT, charSpacing: 1, margin: 0, valign: "middle" } } };
}
const slideNumber = { x: 12.0, y: 6.98, w: 0.73, h: 0.3, fontFace: MONO, fontSize: 10, color: FAINT, align: "right", margin: 0 };

pres.defineSlideMaster({ title: "COVER", background: { color: BG }, objects: [footer()], slideNumber });
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: BG },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: ML, y: 0.5, w: 10, h: 0.32, fontFace: MONO, fontSize: 12, bold: true, color: C.accent1, charSpacing: 3, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: ML, y: 0.86, w: CW, h: 0.95, fontSize: 30, bold: true, color: C.text1, margin: 0, valign: "top", align: "left" }, text: "" } },
    footer(),
  ],
  slideNumber,
});

// Helpers in the page's look: a panel, a mono label, a paragraph.
let objectCount = 0;
const named = (s) => `${s} ${++objectCount}`;
function panel(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06, fill: { color: opts.fill || PANEL }, line: { color: opts.line || LINE, width: 0.75 }, objectName: named("panel"),
  });
}
function label(slide, text, x, y, w, opts = {}) {
  slide.addText(text.toUpperCase(), {
    x, y, w, h: 0.28, fontFace: MONO, fontSize: opts.size || 11, bold: true, color: opts.color || C.accent1, charSpacing: 2, margin: 0, valign: "middle", isTextBox: true, objectName: named("label"),
  });
}
function para(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h, fontSize: opts.size || 14, color: opts.color || C.text1, margin: 0, valign: opts.valign || "top", align: "left", lineSpacingMultiple: opts.lines || 1.12, paraSpaceAfter: opts.after || 0, isTextBox: true, objectName: named("text"), ...(opts.extra || {}),
  });
}
function bullets(slide, items, x, y, w, h, opts = {}) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: i < items.length - 1 } }));
  slide.addText(runs, {
    x, y, w, h, fontSize: opts.size || 14, color: opts.color || C.text1, margin: 0, valign: "top", align: "left", paraSpaceAfter: opts.after || 5, lineSpacingMultiple: 1.08, isTextBox: true, objectName: named("list"),
  });
}
function mono(text, extra = {}) { return { text, options: { fontFace: MONO, ...extra } }; }
function image(slide, file, x, y, w, h) {
  slide.addImage({ path: path.join(SHOTS, file), x, y, w, h, objectName: named("page") });
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { type: "none" }, line: { color: LINE, width: 0.75 }, objectName: named("frame") });
}
function content(section, eyebrow, title) {
  const slide = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  slide.addText(eyebrow.toUpperCase(), { placeholder: "eyebrow", charSpacing: 3 });
  slide.addText(title, { placeholder: "title" });
  return slide;
}

// ---------------------------------------------------------------- 1. The problem, in Elisa's words
pres.addSection({ title: "The idea" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "The idea" });
  s.addText("SILENT CONTEXT", { x: 0.8, y: 1.05, w: 6, h: 0.32, fontFace: MONO, fontSize: 14, bold: true, color: C.accent1, charSpacing: 4, margin: 0, isTextBox: true, objectName: "brand" });
  s.addText("Expert advice lives in chats and emails, and stays there.", { x: 0.8, y: 1.5, w: 6.3, h: 2.1, fontSize: 38, bold: true, color: C.text1, margin: 0, valign: "top", lineSpacingMultiple: 1.05, isTextBox: true, objectName: "headline" });
  s.addText([
    { text: "The next person solves the same fault ", options: { color: C.text2 } },
    { text: "from zero.", options: { color: C.text1, bold: true } },
  ], { x: 0.8, y: 3.75, w: 6.3, h: 0.6, fontSize: 22, margin: 0, valign: "top", isTextBox: true, objectName: "lead" });
  para(s, "Elisa's challenge: capture what field engineers and network experts learn, without giving those people extra work; tie it to the right network entities with its source and period of validity; and let an agent use it the next time a similar case appears.",
    0.8, 4.55, 6.3, 1.5, { size: 15, color: C.text2, lines: 1.18 });

  // The thread beside it, as the page shows one: excerpts from Elisa's example file.
  const tx = 7.4, ty = 0.95, tw = 5.33, th = 5.45;
  panel(s, tx, ty, tw, th);
  const msgs = [
    ["Veikko Vikkelä", "Field Engineer · 09:14", "Changed the SFP on transmission node TRN-042. Link is up and alarms cleared, but traffic is still not coming back."],
    ["Erkki Expert", "Network Expert · 09:19", "Check whether the traffic counters are actually increasing. If they stay at zero even though the interface is UP, it's probably the issue I've seen before."],
    ["Veikko Vikkelä", "Field Engineer · 09:21", "Yes. Link UP. RX power looks normal. Counters basically zero."],
    ["Erkki Expert", "Network Expert · 09:22", "That's it. Disable the interface, wait a little, then enable it again. Don't reboot the whole unit unless that fails."],
    ["Veikko Vikkelä", "Field Engineer · 09:26", "Is this documented somewhere?"],
    ["Erkki Expert", "Network Expert · 09:27", "Not that I know of. We've just learned it over the years."],
  ];
  const runs = [];
  msgs.forEach(([who, role, text], i) => {
    runs.push({ text: who, options: { fontFace: MONO, fontSize: 10.5, bold: true, color: C.accent1, breakLine: false, paraSpaceBefore: i ? 6 : 0 } });
    runs.push({ text: "  " + role, options: { fontFace: MONO, fontSize: 10.5, color: FAINT, breakLine: true } });
    runs.push({ text, options: { fontSize: 13, color: C.text1, breakLine: true } });
  });
  s.addText(runs, { x: tx + 0.25, y: ty + 0.22, w: tw - 0.5, h: th - 0.9, margin: 0, valign: "top", lineSpacingMultiple: 1.08, isTextBox: true, objectName: "thread" });
  s.addShape(pres.ShapeType.line, { x: tx + 0.25, y: ty + th - 0.58, w: tw - 0.5, h: 0, line: { color: LINE, width: 0.75 }, objectName: "thread rule" });
  s.addText("Teams excerpts · Elisa's example file, unchanged", { x: tx + 0.25, y: ty + th - 0.5, w: tw - 0.5, h: 0.3, fontFace: MONO, fontSize: 10, color: FAINT, charSpacing: 1, margin: 0, valign: "middle", isTextBox: true, objectName: "thread tag" });

  s.addText("Petri Korhonen · github.com/pkorrrhonen-cmd/silent-context · MIT", { x: 0.8, y: 6.3, w: 7, h: 0.3, fontFace: MONO, fontSize: 10, color: FAINT, charSpacing: 1, margin: 0, isTextBox: true, objectName: "author" });
  s.addNotes("Network experts solve faults in chats and emails. The fix stays in the thread, and the next person starts from zero. Elisa's own example: an SFP replaced on TRN-042, the link up, the counters at zero, and one expert who knows what to do. The task: capture that without extra work, tie it to the right network entities with its source and its period of validity, and let an agent use it the next time a similar case appears.");
}

// ---------------------------------------------------------------- 2. Silent context, in one picture
{
  const s = content("The idea", "The answer", "Silent context turns those messages into claims an agent can use");
  const steps = [
    ["Read as written", "Teams threads and emails, exactly as they are. Nobody fills in anything for the system."],
    ["Tied to the network", "A context claim on the unit, with its source, the expert's own words on which units it covers, and two clocks: when it holds in the world, and when we learned it."],
    ["One call for the agent", null],
  ];
  const x = ML, w = 5.0;
  steps.forEach(([head, text], i) => {
    const y = 2.0 + i * 1.55, h = 1.4;
    panel(s, x, y, w, h);
    label(s, head, x + 0.25, y + 0.18, w - 0.5);
    if (text) para(s, text, x + 0.25, y + 0.5, w - 0.5, h - 0.6, { size: 14 });
    else s.addText([
      mono("claims_for", { color: C.accent1, bold: true }),
      { text: " answers with a next step and its sources: ", options: {} },
      { text: "propose", options: { color: C.accent3, bold: true } }, { text: ", ", options: {} },
      { text: "check first", options: { color: C.accent4, bold: true } }, { text: ", or ", options: {} },
      { text: "I don't know", options: { color: C.accent5, bold: true } }, { text: " with who to ask.", options: {} },
    ], { x: x + 0.25, y: y + 0.5, w: w - 0.5, h: h - 0.6, fontSize: 14, color: C.text1, margin: 0, valign: "top", lineSpacingMultiple: 1.12, isTextBox: true, objectName: "step three" });
  });
  const ix = 5.95, iw = W - ML - ix, ih = iw * 9 / 16;
  image(s, "scene-4.png", ix, 2.0, iw, ih);
  para(s, "The page: thirteen scenes, no model and no key. Every answer on it is computed when asked, and the time axis shows what was known when.", ix, 2.0 + ih + 0.18, iw, 0.7, { size: 13, color: C.text2 });
  s.addNotes("Silent context reads those messages as they are. The advice becomes claims tied to the network, each with its source and how long it holds. An agent gets one call: what to do next, and where that came from. The demo page runs with no model and no key; the arrow keys move through thirteen scenes.");
}

// ---------------------------------------------------------------- 3. Capture and bind
pres.addSection({ title: "How it works" });
{
  const s = content("How it works", "Capture and bind", "The model reads; code binds, or waits with a reason");
  const cells = [
    ["Read", "One model call per thread reports what the text says. An identifier counts only if it is literally in the text."],
    ["Bind", "Code ties the claim to the graph. The model never picks an entity."],
    ["Wait", "An unclear binding waits with its reason: no unit named, several could fit, an unknown id, a contradicting context. It may wait forever. The system never asks anyone."],
    ["Merge", "One person's accounts become one claim with several sources. A relay is a source, not a telling."],
  ];
  const cw = (CW - 0.4) / 2;
  cells.forEach(([head, text], i) => {
    const x = ML + (i % 2) * (cw + 0.4), y = 1.95 + Math.floor(i / 2) * 1.0;
    label(s, head, x, y, cw);
    para(s, text, x, y + 0.3, cw, 0.8, { size: 14 });
  });
  const iw = 10.6, ih = iw * 292 / 1265;
  image(s, "bind-claims-graph.png", ML + (CW - iw) / 2, 4.25, iw, ih);
  s.addNotes("One model call per thread reports what the text says, and an identifier counts only if it is literally in the text. Code binds the claim to the graph; the model never picks an entity. An unclear binding waits with its reason and may wait forever; the system never asks anyone. One person's accounts become one claim with several sources. The picture is the page's third scene: Erkki's advice as one claim, tied to TRN-042, with its links on the right.");
}

// ---------------------------------------------------------------- 4. The data model
{
  const s = content("How it works", "The data model", "A claim keeps its words, its scope and two clocks");
  const cells = [
    ["Words", "Claim text in the speaker's words, with “sometimes” and “usually” kept.", null],
    ["Entity and scope", "The entity it was seen on, and apart from it the scope: wording verbatim, status confirmed or undefined.", "seen on TRN-042 · covers “These old units” (undefined)"],
    ["Two clocks", "World time and information time apart. Unknown time stays unknown. No age limit is derived from “installed around 2019”.", "from 14.10. · still believed true"],
    ["Evidence", "Events with a date and a link: told, reported success, reported failure, disputed, superseded. Rendered from a template: no counts, no percentages, no figure per person.", null],
    ["Status", "Computed at read time for a claim and a unit, never stored.", "ACTIVE · SUPERSEDED · DISPUTED"],
    ["The graph", "Entities: units, classes, sites, a barrier, a procedure type and groups. Exported as graph.json and graph.cypher; the Cypher loads into Neo4j 5 with no edits.", null],
  ];
  const cw = (CW - 0.5) / 3, ch = 2.2;
  cells.forEach(([head, text, example], i) => {
    const x = ML + (i % 3) * (cw + 0.25), y = 2.0 + Math.floor(i / 3) * (ch + 0.25);
    panel(s, x, y, cw, ch);
    label(s, head, x + 0.25, y + 0.18, cw - 0.5);
    para(s, text, x + 0.25, y + 0.5, cw - 0.5, 1.25, { size: 14 });
    if (example) s.addText(example, { x: x + 0.25, y: y + ch - 0.55, w: cw - 0.5, h: 0.35, fontFace: MONO, fontSize: 11, color: C.accent1, margin: 0, valign: "middle", isTextBox: true, objectName: named("example") });
  });
  s.addNotes("The claim text stays in the speaker's words, hedges included. The entity it was seen on and the scope it is said to cover are separate; the scope keeps its wording and a status, confirmed or undefined. World time and information time are separate, and unknown time stays unknown. Evidence is a list of events with a date and a link, rendered from a template with no counts or percentages. Status is computed at read time, never stored.");
}

// ---------------------------------------------------------------- 5. The agent
{
  const s = content("How it works", "The agent", "Three tiers from rules, one prohibition in code, no model");
  const tiers = [
    ["Propose", C.accent3, "A success is reported on this unit's class, no disagreement, and the claim's own check holds."],
    ["Check first", C.accent4, "Only told, in doubt, a guess, or disputed."],
    ["I don't know", C.accent5, "With the group to ask, and the gap logged."],
  ];
  const cw = (CW - 0.5) / 3, ch = 1.45;
  tiers.forEach(([head, color, text], i) => {
    const x = ML + i * (cw + 0.25), y = 2.0;
    panel(s, x, y, cw, ch);
    label(s, head, x + 0.25, y + 0.18, cw - 0.5, { color, size: 12 });
    para(s, text, x + 0.25, y + 0.52, cw - 0.5, 1.0, { size: 14 });
  });
  const ih = CW * 168 / 1164;
  image(s, "use-answer.png", ML, 3.7, CW, ih);
  para(s, "The page's fourth scene: the same fault on TRN-051, the same class as TRN-042. The agent reads the counters from telemetry itself when a recent sample exists, proposes the expert's step with its source, and holds back a reboot or a hardware replacement until a failed bounce is reported.",
    ML, 3.7 + ih + 0.15, CW, 0.7, { size: 13, color: C.text2 });
  para(s, "What a person did, and the outcome, fill in from the device events. Nobody reports anything. That record is what the next slide's policy reads.", ML, 3.7 + ih + 0.9, CW, 0.35, { size: 14 });
  s.addNotes("Three tiers from rules: propose when a success is reported on this unit's class, no disagreement, and the claim's own check holds; check first when only told, in doubt, a guess, or disputed; I don't know with the group to ask, and the gap logged. One prohibition in code: no reboot or hardware replacement before a failed bounce is reported. The agent reads counters from telemetry itself when a recent sample exists. What a person did and the outcome fill in from device events, and that record is what the policy on who acts reads.");
}

// ---------------------------------------------------------------- 5b. Who acts
{
  const s = content("How it works", "Who acts", "A policy says who does the next step. The agent itself, once a success is on record");
  const rows = [
    ["Step", "Reversible", "Needs", "Who acts"],
    ["Turn the port off and on", "yes", "proposed on this class before and carried out with the counters rising; no disagreement; the counters read from the device by the agent", "the agent itself"],
    ["Reboot", "no", "a failed lighter fix reported", "a person"],
    ["Replace a part", "no", "the same", "a person"],
    ["Drive to a site", "no", "", "a person"],
  ];
  const widths = [2.6, 1.3, 5.6, 2.1], top = 1.95, rh = 0.42;
  rows.forEach((cells, r) => {
    let x = ML;
    cells.forEach((text, c) => {
      const head = r === 0;
      s.addText(text, { x, y: top + r * rh + (r > 1 ? 0.22 : 0), w: widths[c], h: r === 1 ? 0.64 : rh, fontFace: head ? MONO : undefined, fontSize: head ? 10.5 : 12.5, bold: head || c === 3, color: head ? C.accent1 : (c === 3 && r === 1 ? C.accent3 : C.text1), margin: [2, 4, 2, 0], valign: "top", isTextBox: true, objectName: named("policy cell") });
      x += widths[c] + 0.15;
    });
  });
  const ih = CW * 236 / 1140 * 0.78, iw = CW * 0.78, iy = 4.25;
  image(s, "act-answer.png", ML + (CW - iw) / 2, iy, iw, ih);
  para(s, "The page's sixth scene: the same fault on a third unit of the same class, after the agent's own log shows TRN-051's proposal carried out with the counters rising. The decision is real and computed when asked; the action is an event in the synthetic stream, with no write path to any device.",
    ML, iy + ih + 0.1, CW, 0.5, { size: 12, color: C.text2, lines: 1.1 });
  s.addNotes("A policy says who does the next step. By default the agent proposes and a person acts. The agent itself acts only on a reversible step that its own log shows was proposed on this class before and carried out with the counters rising, with no disagreement and the counters read from the device by the agent. A reboot or a hardware replacement never goes to the agent. The demo's network is synthetic: the agent's action is an event in the synthetic stream, and there is no write path to any device. The decision is real and computed when asked.");
}

// ---------------------------------------------------------------- 5c. Any source, and the question
{
  const s = content("How it works", "Any source, and the question", "The same reader for a ticket and a thread in Finnish; a drafted question when it does not know");
  const lw = 5.6;
  label(s, "Any source, any language", ML, 2.0, lw);
  para(s, "A ticket export's worklog and a Teams thread in Finnish are read by the same reader as Elisa's Teams export and email, and become the same kind of claim, in the speaker's own words and language. The ticket's closing note adds an outcome to advice told in a chat. Ask about the Koski gate and the answer is in Finnish, because that is what was said.", ML, 2.35, lw, 1.8, { size: 13.5 });
  label(s, "When it does not know", ML, 4.3, lw);
  para(s, "It writes the question for the person on call, who sends it. The system itself sends nothing. A budget of three questions a week per group shows when the asking would become the extra work it replaces.", ML, 4.65, lw, 1.3, { size: 13.5 });
  const ix = ML + lw + 0.4, iw = W - ML - ix;
  const ih1 = iw * 112 / 1140, ih2 = iw * 87 / 900, ih3 = iw * 276 / 310 * 0.42;
  image(s, "koski-answer.png", ix, 2.0, iw, ih1);
  image(s, "ask-draft.png", ix, 2.0 + ih1 + 0.3, iw, ih2);
  image(s, "sources-list.png", ix + (iw - iw * 0.42) / 2, 2.0 + ih1 + ih2 + 0.6, iw * 0.42, ih3);
  s.addNotes("Any source, any language: a ticket export and a Teams thread in Finnish are read by the same reader as Elisa's files and become the same kind of claim, in the speaker's own words. The ticket's closing note adds an outcome to advice told in a chat. When the agent does not know, it writes the question for the person on call, who sends it; the system sends nothing, and a budget of three a week per group keeps the asking small.");
}

// ---------------------------------------------------------------- 6. What was measured
pres.addSection({ title: "What was measured, and what it is not" });
{
  const s = content("What was measured, and what it is not", "What was measured", "Everything below runs with no key, from the recorded answers");
  const tiles = [
    ["160", "tests pass", "The data set's shape, the store's rules, extraction and binding against the truth set, the agent's acceptance cases, the policy on who acts, the page, the MCP wrapper."],
    ["13 / 13", "truth set sources found", "13 sources: merged 9/9, entity 5/5, scope 5/5, time 9/9, evidence 8/8. The second day's two rows were written before their sources were read."],
    ["1 of 16", "confidently wrong, held-out binding set", "16 synthetic sources the rule author has not read. Five repeats with the prompt unchanged: 0, 0, 0, 1, 1, the same file each time."],
    ["21 of 21", "acceptance rows hold", "The build plan's cases A0 to A11 and A12 for the policy, written by app.accept from the recorded answers. A test keeps every computed row passing."],
    ["Passed", "clean install from the README", "git archive into an empty folder, .env with no values, every command in the README runs with no key, on 7.11.2026."],
    ["No edits", "Cypher export loaded into Neo4j 5", "At noon on 7.11.: 5 claims, 14 entities, 14 evidence events and 9 sources as nodes, all ten edge types; one query answered the agent's question from the graph. The data grew that evening; the load was not repeated."],
  ];
  const cw = (CW - 0.5) / 3, ch = 2.12;
  tiles.forEach(([value, head, detail], i) => {
    const x = ML + (i % 3) * (cw + 0.25), y = 2.0 + Math.floor(i / 3) * (ch + 0.25);
    panel(s, x, y, cw, ch);
    s.addText(value, { x: x + 0.25, y: y + 0.15, w: cw - 0.5, h: 0.65, fontSize: 36, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: named("value") });
    para(s, head, x + 0.25, y + 0.85, cw - 0.5, 0.3, { size: 14, extra: { bold: true } });
    para(s, detail, x + 0.25, y + 1.17, cw - 0.5, 0.85, { size: 11.5, color: C.text2, lines: 1.1 });
  });
  para(s, "These numbers describe this synthetic data only. Not tested: extraction on real conversations, outcomes read from real chat, and the class binding on anything but this data.",
    ML, 6.56, CW, 0.35, { size: 12, color: C.text2, valign: "middle" });
  s.addNotes("160 tests, all with no key. The truth set of 13 sources: found 13 of 13, merged 9 of 9, entity 5 of 5, scope 5 of 5, time 9 of 9, evidence 8 of 8. The held-out binding set: 16 synthetic sources the rule author has not read, 1 of 16 confidently wrong in the recorded run, and 0, 0, 0, 1, 1 in five repeats. Acceptance cases A0 to A12: 21 computed rows, 21 hold. A clean install from the README with no key passed on the first day. The Cypher export loaded into Neo4j with no edits at noon on the first day. These numbers describe this synthetic data only.");
}

// ---------------------------------------------------------------- 7. Elisa's question: is the information fact?
{
  const s = content("What was measured, and what it is not", "Elisa's question", "Is the information fact? The answer is a claim's origin, not a score");
  const lw = 6.1;
  para(s, "The answer is a claim's origin, what was reported about it, and when it was last confirmed. Not a score for the person.", ML, 2.0, lw, 0.9, { size: 16 });
  label(s, "Why no person scores", ML, 3.05, lw);
  bullets(s, [
    "An employee assessment it was never meant to be.",
    "Personal data it does not need.",
    "A source that dries up once it is graded.",
  ], ML, 3.4, lw, 1.3, { size: 14 });
  label(s, "Why no counts", ML, 4.85, lw);
  para(s, "“Confirmed twice” invites a trust the data does not carry. The events are listed; the reader counts if they want to.", ML, 5.2, lw, 0.9, { size: 14 });
  const ix = ML + lw + 0.5, iw = W - ML - ix, ih = iw * 292 / 701;
  image(s, "bind-claims.png", ix, 2.0, iw, ih);
  para(s, "One claim on the page: its words, where it was seen, which units it covers in the expert's own words, who told it and where, how long it has been known, and the evidence as events with their source.", ix, 2.0 + ih + 0.18, iw, 1.0, { size: 13, color: C.text2 });
  s.addNotes("Elisa asked how to tell whether the information is fact. The answer here is a claim's origin, what was reported about it, and when it was last confirmed, not a score for the person. No person scores: an employee assessment it was never meant to be, personal data it does not need, and a source that dries up once it is graded. No counts: confirmed twice invites a trust the data does not carry; the events are listed and the reader counts if they want to.");
}

// ---------------------------------------------------------------- 8. What is real, what is simulated
{
  const s = content("What was measured, and what it is not", "What is real, what is simulated", "The mechanism is real; the network behind it is not");
  const cols = [
    ["Real", [
      "Elisa's two files, unchanged; a test holds their checksums.",
      "The model's reading of every source, recorded once and replayed; not called at demo time.",
      "Binding, dating and merging, in code, live on every rebuild of the store.",
      "The agent: claims_for and access_for, rules and a template, no model.",
      "The exports: graph.json and graph.cypher, written from the store.",
    ]],
    ["Simulated", [
      "Every other source: nine threads and emails written for this demo, and on the second day a ticket export and a thread in Finnish.",
      "The dates: Elisa's files carry none, so a manifest gives each source a received time.",
      "The event stream and the telemetry; there is no network behind them.",
      "The graph: four units, two classes, four sites, a barrier, a procedure type, five groups.",
      "The demo clock and the channels. No real network, channel or person.",
    ]],
    ["Not built, on purpose", [
      "Sending the question to the expert: it is drafted, with a budget; a person sends it.",
      "Matching Elisa's own inventory graph; its schema is not known here.",
      "A semantic symptom match; symptoms are matched by plain words.",
      "Acting on a real network: the policy's action is an event in the synthetic stream, with no write path to any device.",
      "Live connectors to Teams and Slack, a chat with the agent, search by meaning: each a connector or a model away.",
    ]],
  ];
  const cw = (CW - 0.5) / 3, ch = 4.65;
  cols.forEach(([head, items], i) => {
    const x = ML + i * (cw + 0.25), y = 2.0;
    panel(s, x, y, cw, ch);
    label(s, head, x + 0.25, y + 0.18, cw - 0.5);
    bullets(s, items, x + 0.25, y + 0.55, cw - 0.5, ch - 0.7, { size: 13.5, after: 6 });
  });
  s.addNotes("Real: Elisa's two files unchanged; the model's reading, recorded; binding, dating and merging in code; the agent and the policy, live; the exports. Simulated: every other source, the dates, the event stream, the telemetry, the graph, the clock, the channels, and the agent's own action. No real network, channel or person. Not built on purpose: sending the question, matching Elisa's own graph, a semantic symptom match, acting on a real network, live connectors and a chat with the agent.");
}

// ---------------------------------------------------------------- 9. What comes next
{
  const s = content("What was measured, and what it is not", "What comes next", "Sending the question, more of the policy, live sources");
  const cells = [
    ["Sending the question", "The question is drafted now, with a budget of three a week per group; a person sends it. The next step is a connector that sends it when the budget and the situation allow, a 20-second call when Erkki is driving away from the site. Synthetic data cannot show it is not extra work, so it is a step for real data."],
    ["More of the policy", "The first table covers one reversible step. Next: more action classes, a limit on blast radius, and a review of the agent's own actions, so that certainty stays necessary and never sufficient."],
    ["Live sources", "Connectors to Teams and Slack that read as the messages arrive, a ticketing system's own export, and a chat with the agent on top of the same calls."],
    ["For production at Elisa", "Schema matching against the inventory graph, Finnish inflections from the inventory or a lemmatiser, and a semantic symptom match."],
  ];
  const cw = (CW - 0.3) / 2, ch = 2.2;
  cells.forEach(([head, text], i) => {
    const x = ML + (i % 2) * (cw + 0.3), y = 2.0 + Math.floor(i / 2) * (ch + 0.25);
    panel(s, x, y, cw, ch);
    label(s, head, x + 0.25, y + 0.18, cw - 0.5);
    para(s, text, x + 0.25, y + 0.55, cw - 0.5, ch - 0.7, { size: 15 });
  });
  s.addNotes("What comes next: sending the drafted question through a connector when the budget and the situation allow; more of the policy, with more action classes and a limit on blast radius; live sources, connectors to Teams and Slack and a chat with the agent on the same calls; and for production, schema matching against the inventory graph, Finnish inflections from the inventory, and a semantic symptom match.");
}

// ---------------------------------------------------------------- 10. The limits, said plainly
{
  const s = content("What was measured, and what it is not", "The limits, said plainly", "What this demo does not claim");
  const limits = [
    "The system never sends a message itself. It drafts; a person sends.",
    "It shows the origin of a claim and what was reported about it, not the truth.",
    "It scores claims, not people: no personal assessment and no figure shown per person.",
    "Telling apart which units a claim applies to, before someone narrows it down, rests on synthetic data.",
    "The network here is simulated, and so is every file but Elisa's two; the agent acts only in that stream.",
    "Left out on purpose: live connectors, a chat with the agent, search by meaning, Elisa's inventory graph.",
  ];
  limits.forEach((text, i) => {
    const y = 2.0 + i * 0.68;
    s.addText(String(i + 1).padStart(2, "0"), { x: ML, y, w: 0.6, h: 0.5, fontFace: MONO, fontSize: 16, bold: true, color: C.accent1, margin: 0, valign: "middle", isTextBox: true, objectName: named("number") });
    para(s, text, ML + 0.7, y, CW - 0.7, 0.5, { size: 19, valign: "middle" });
    if (i < limits.length - 1) s.addShape(pres.ShapeType.line, { x: ML + 0.7, y: y + 0.6, w: CW - 0.7, h: 0, line: { color: LINE, width: 0.75 }, objectName: named("rule") });
  });
  s.addText([
    { text: "github.com/pkorrrhonen-cmd/silent-context", options: { color: C.accent1, bold: true } },
    { text: "   MIT   Petri Korhonen", options: { color: C.text2 } },
  ], { x: ML, y: 6.3, w: CW, h: 0.4, fontFace: MONO, fontSize: 13, charSpacing: 1, margin: 0, valign: "middle", isTextBox: true, objectName: "repository" });
  s.addNotes("What this does not claim. It never sends a message itself; it drafts, and a person sends. It shows where a claim came from and what was reported, not the truth. It scores claims, never people. Telling apart which units a claim applies to rests on synthetic data. The network is simulated, and so is every file but Elisa's two; the agent acts only in that stream. Left out on purpose: live connectors, a chat with the agent, search by meaning, Elisa's inventory graph.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
