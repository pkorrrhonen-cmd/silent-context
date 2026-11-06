"use strict";

const SYMPTOM = "link up, counters zero after SFP replacement";

// The demo as a sequence. Each scene sets the clock, and may ask the agent or open a source.
const SCENES = [
  {
    title: "The gap",
    clock: "2026-10-14T22:00:00",
    fresh: true,
    caption: "A unit has a fault nobody documented. The agent has nothing to go on, and says so.",
    ask: { unit: "TRN-051", symptom: SYMPTOM },
    lit: ["agent"],
  },
  {
    title: "Capture",
    clock: "2026-10-15T00:00:00",
    caption: "Elisa's conversation and email are read as they are. Nobody wrote anything for the system.",
    source: "teams_trn042.json",
    lit: ["sources", "timeline"],
  },
  {
    title: "Bind",
    clock: "2026-10-15T00:00:00",
    caption: "One claim with two sources, bound to TRN-042, in the expert's own words about scope.",
    selectUnit: "TRN-042",
    lit: ["claims", "graph"],
  },
  {
    title: "Use",
    clock: "2026-10-21T10:50:00",
    caption: "The same fault on another old unit. The agent reads the counters itself and proposes the step.",
    ask: { unit: "TRN-051", symptom: SYMPTOM },
    lit: ["agent"],
  },
  {
    title: "Learn",
    clock: "2026-10-21T11:15:00",
    caption: "What the person did and what happened comes from the devices. Nobody reported it.",
    // The line needs the earlier proposal, also when this scene is opened directly.
    askedBefore: { clock: "2026-10-21T10:50:00", entity: "TRN-051", symptom: SYMPTOM },
    lit: ["agent"],
  },
  {
    title: "Ageing",
    clock: "2026-10-29T00:00:00",
    caption: "A firmware update on TRN-042 alone puts the advice in doubt for that unit, and no other.",
    ask: { unit: "TRN-042", symptom: SYMPTOM, counters: "zero" },
    lit: ["agent", "timeline"],
  },
  {
    title: "Not for all",
    clock: "2026-10-31T00:00:00",
    caption: "The advice failed on a newer unit. The expert narrowed it, and the agent does not offer it there.",
    ask: { unit: "TRN-100", symptom: SYMPTOM, counters: "zero" },
    lit: ["agent", "graph"],
  },
  {
    title: "Disagree",
    clock: "2026-11-03T00:00:00",
    caption: "Two experts disagree. Both stay visible, the agent does not choose, and it reads first.",
    ask: { unit: "TRN-051", symptom: SYMPTOM, counters: "zero" },
    lit: ["agent", "claims"],
  },
  {
    title: "The barrier",
    clock: "2026-11-03T00:00:00",
    caption: "Where the key is, before anyone drives there, with how old that information is.",
    ask: { unit: "SITE-NILO" },
    lit: ["agent", "timeline"],
  },
  {
    title: "The limits",
    clock: "2026-11-03T00:00:00",
    caption: "What this demo does not claim.",
    limits: true,
    lit: [],
  },
];

const PRESETS = [
  { label: "Another old unit", ask: { unit: "TRN-051", symptom: SYMPTOM } },
  { label: "Where it was seen", ask: { unit: "TRN-042", symptom: SYMPTOM } },
  { label: "Newer generation", ask: { unit: "TRN-100", symptom: SYMPTOM } },
  { label: "A different symptom", ask: { unit: "TRN-051", symptom: "intermittent CRC errors on uplink" } },
  { label: "Before driving to Nilo", ask: { unit: "SITE-NILO" } },
  { label: "The key on 10.10.?", ask: { unit: "SITE-NILO", at: "2026-10-10" } },
];

const TIER_LABEL = { propose: "PROPOSE", check_first: "CHECK FIRST", unknown: "I DON'T KNOW" };
const SVG_NS = "http://www.w3.org/2000/svg";
// The axis is compressed before the knee, because nearly everything happens after it. It is marked.
const AXIS = {
  from: Date.parse("2026-08-30T00:00:00"),
  knee: Date.parse("2026-10-12T00:00:00"),
  to: Date.parse("2026-11-07T00:00:00"),
  kneeShare: 0.16,
};
const AXIS_TICKS = ["2026-09-01", "2026-10-01", "2026-10-14", "2026-10-21", "2026-10-28", "2026-11-01"];
const GUTTER = 166;
const LABEL_CHAR_WIDTH = 7;

let state = null;
let scene = 0;
let answer = null;
let selected = null;
let busy = false;

const $ = (id) => document.getElementById(id);

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function shortTime(iso, withClock = false) {
  if (!iso) return "unknown";
  const [day, clock] = iso.split("T");
  const [, month, date] = day.split("-");
  const text = `${Number(date)}.${Number(month)}.`;
  return withClock && clock ? `${text} ${clock.slice(0, 5)}` : text;
}

function svgEl(name, attrs = {}, parent = null, text = null) {
  const el = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== null) el.textContent = text;
  if (parent) parent.appendChild(el);
  return el;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `${path}: ${response.status}`);
  }
  return response.json();
}

// The time axis: the layers of the reference picture, live

function drawTimeline() {
  const svg = $("timeline-svg");
  const { width, height } = svg.getBoundingClientRect();
  if (!width || !state) return;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.replaceChildren();
  const toX = (iso) => {
    const t = Date.parse(iso);
    const share =
      t <= AXIS.knee
        ? (AXIS.kneeShare * (t - AXIS.from)) / (AXIS.knee - AXIS.from)
        : AXIS.kneeShare + ((1 - AXIS.kneeShare) * (t - AXIS.knee)) / (AXIS.to - AXIS.knee);
    return GUTTER + share * (width - GUTTER - 10);
  };

  const eventsY = 42;
  const sourcesY = 74;
  const contextTop = 92;

  const bands = [
    [0, 24, 58, "EVENT STREAM", "as-observed"],
    [1, 60, 28, "SOURCES", "as-received"],
    [2, 90, height - 92, "CONTEXT", "as-experienced"],
  ];
  for (const [, y, h, name, sub] of bands) {
    svgEl("rect", { x: 0, y, width, height: h, class: "t-band" }, svg);
    svgEl("text", { x: 10, y: y + 15, class: "t-layer" }, svg, name);
    svgEl("text", { x: 10, y: y + 29, class: "t-sublayer" }, svg, sub);
  }

  for (const day of AXIS_TICKS) {
    const iso = `${day}T00:00:00`;
    const x = toX(iso);
    svgEl("line", { x1: x, x2: x, y1: 18, y2: height, class: "t-grid" }, svg);
    svgEl("text", { x: x + 3, y: 14, class: "t-tick" }, svg, shortTime(iso));
  }
  svgEl("text", { x: toX("2026-10-12T00:00:00") - 7, y: 14, class: "t-tick" }, svg, "//");

  const labels = { module_replaced: "SFP", firmware_updated: "firmware" };
  let lastLabelX = -999;
  let row = 0;
  for (const event of state.events) {
    if (Date.parse(event.event_time) < AXIS.from) continue;
    const x = toX(event.event_time);
    const future = event.known ? "" : " future";
    svgEl(
      "polygon",
      {
        points: `${x},${eventsY - 7} ${x + 7},${eventsY} ${x},${eventsY + 7} ${x - 7},${eventsY}`,
        class: `t-event${future}`,
      },
      svg
    );
    if (labels[event.type]) {
      row = x - lastLabelX < 130 ? (row + 1) % 2 : 0;
      lastLabelX = x;
      svgEl(
        "text",
        { x: x + 10, y: eventsY - 3 + row * 14, class: `t-event-label${future}` },
        svg,
        `${event.entity} ${labels[event.type]}`
      );
    }
  }

  for (const source of state.sources) {
    const x = toX(source.received_at);
    const rect = svgEl(
      "rect",
      {
        x: x - 5,
        y: sourcesY - 5,
        width: 10,
        height: 10,
        class: `t-source ${source.channel}${source.known ? "" : " future"}${source.origin === "elisa" ? " elisa" : ""}`,
      },
      svg
    );
    rect.addEventListener("click", () => openSource(source.file));
    svgEl("title", {}, rect, source.file);
  }

  const claims = state.claims;
  const barHeight = Math.min(17, (height - contextTop - 3) / Math.max(claims.length, 1) - 2);
  claims.forEach((claim, index) => {
    const y = contextTop + index * (barHeight + 2);
    const startIso = claim.valid_from
      ? (claim.valid_from.length === 10 ? `${claim.valid_from}T00:00:00` : claim.valid_from)
      : claim.received_at;
    const endIso = claim.valid_to ? `${claim.valid_to}T00:00:00` : state.as_of || new Date().toISOString().slice(0, 19);
    const x1 = toX(startIso);
    const x2 = Math.max(toX(endIso), x1 + 6);
    const classes = ["t-bar"];
    if (claim.binding_status === "waiting") classes.push("waiting");
    if (claim.superseded_at) classes.push("ended");
    if (claim.id === selected) classes.push("t-bar-selected");
    const bar = svgEl("rect", { x: x1, y, width: x2 - x1, height: barHeight, rx: 1, class: classes.join(" ") }, svg);
    bar.addEventListener("click", () => selectClaim(claim.id));
    svgEl("title", {}, bar, claim.claim_text);
    if (!claim.valid_to && !claim.superseded_at) {
      svgEl("line", { x1: x2, x2: width - 8, y1: y + barHeight / 2, y2: y + barHeight / 2, class: "t-bar-open" }, svg);
    }
    if (!claim.valid_from) {
      svgEl("line", { x1: x1 - 14, x2: x1, y1: y + barHeight / 2, y2: y + barHeight / 2, class: "t-bar-unknown" }, svg);
    }
    const unit = claim.observed_entity || "no unit yet";
    const from = claim.valid_from ? shortTime(claim.valid_from) : "unknown";
    const to = claim.valid_to ? shortTime(claim.valid_to) : claim.superseded_at ? "unknown" : "still believed true";
    const label = `${unit}  valid_from ${from}  valid_to ${to}`;
    const fits = x1 + 6 + label.length * LABEL_CHAR_WIDTH < width - 8;
    svgEl(
      "text",
      {
        x: fits ? x1 + 6 : x1 - 18,
        y: y + barHeight / 2 + 4,
        "text-anchor": fits ? "start" : "end",
        class: "t-bar-label",
      },
      svg,
      label
    );
  });

  const nowIso = state.as_of || new Date().toISOString().slice(0, 19);
  const nowX = Math.min(toX(nowIso), width - 10);
  const group = svgEl("g", { id: "t-line" }, svg);
  group.style.transform = `translateX(${nowX}px)`;
  svgEl("line", { x1: 0, x2: 0, y1: 16, y2: height, class: "t-now" }, group);
  svgEl("text", { x: -5, y: 13, class: "t-now-label", "text-anchor": "end" }, group, "t=x");
}

// Sources and the extra-work panel

function drawSources() {
  const m = state.metrics;
  $("proof").innerHTML = `
    <div><b>${m.conversations_started}</b>conversations started by the system</div>
    <div><b>${m.actions_asked_of_specialists}</b>actions asked of specialists</div>`;
  $("source-list").replaceChildren(
    ...state.sources.map((source) => {
      const li = document.createElement("li");
      li.className = `${source.channel}${source.known ? "" : " future"}${source.origin === "elisa" ? " elisa" : ""}`;
      let note = "not yet";
      if (source.known) {
        if (source.unchanged) note = `unchanged ${source.sha256.slice(0, 7)}`;
        else if (source.claim_ids.length) note = `${source.claim_ids.length === 1 ? "a claim" : "claims"}`;
        else note = "no claim";
      }
      li.innerHTML = `
        <span class="channel">${source.channel === "teams" ? "T" : "E"}</span>
        <span class="name">${esc(source.file.replace(/\.(json|txt)$/, ""))}</span>
        <span class="note">${esc(note)}</span>`;
      li.title = `${source.file}, received ${source.received_at}`;
      li.addEventListener("click", () => openSource(source.file));
      return li;
    })
  );
  const groups = Object.entries(m.gaps_by_group)
    .map(([group, count]) => `${esc(group)} <b>${count}</b>`)
    .join(", ");
  const wrong = m.held_out_wrong_per_run;
  $("metrics").innerHTML = `
    <p>Bound <b>${m.bound}</b>, waiting with a reason <b>${m.waiting}</b>${groups ? `. "I don't know": ${groups}` : ""}</p>
    ${wrong ? `<p>Held-out binding test, wrong of 16 per run: <b>${wrong.join(" ")}</b></p>` : ""}`;
}

// Claims

function usedByAnswer() {
  return new Set((answer?.claims || []).map((claim) => claim.id));
}

function statusFor(claim) {
  const inAnswer = (answer?.claims || []).find((c) => c.id === claim.id);
  return inAnswer?.status_for_entity || claim.status_for_entity;
}

function drawClaims() {
  const used = usedByAnswer();
  $("claim-count").textContent = state.claims.length
    ? `${state.claims.length} at this time, from what people already wrote`
    : "none yet";
  // What the agent just used or the viewer picked comes first, so it is on screen without scrolling.
  const rank = (claim) => (claim.id === selected ? 2 : used.has(claim.id) ? 1 : 0);
  const ordered = [...state.claims].sort((a, b) => rank(b) - rank(a));
  $("claim-list").replaceChildren(
    ...ordered.map((claim) => {
      const card = document.createElement("article");
      const status = statusFor(claim);
      card.className = `claim ${claim.binding_status}${claim.superseded_at ? " superseded" : ""}${claim.id === selected ? " selected" : ""}${used.has(claim.id) ? " used" : ""}`;
      const sources = claim.sources.map((s) => `${s.channel}/${s.role || "role unknown"}`);
      const uniqueSources = [...new Set(sources)].join(", ");
      card.innerHTML = `
        <p>${esc(claim.claim_text)}</p>
        <div class="meta">
          <span class="chip ${esc(status)}">${esc(status.replace("_", " "))}</span>
          <span>on <b>${esc(claim.observed_entity || claim.binding_reason)}</b></span>
          <span>scope <b>${esc(claim.scope_text || "not stated")}</b> (${esc(claim.scope_status)})</span>
          <span>${esc(uniqueSources)}</span>
          <span>age <b>${claim.info_age_days}</b> d</span>
        </div>
        <pre class="evidence">${esc(claim.evidence_rendered)}</pre>`;
      card.addEventListener("click", () => selectClaim(claim.id));
      return card;
    })
  );
}

function selectClaim(id) {
  selected = selected === id ? null : id;
  drawClaims();
  drawGraph();
  drawTimeline();
}

// The graph, laid out by kind so it stays still from scene to scene

const NODE_LABEL = {
  "cls-trn-gen1": "gen 1, 4.x",
  "cls-trn-gen2": "gen 2, 6.x",
  "PROC-SFP-REPLACE": "SFP replacement",
  "BAR-NILO-1": "barrier",
  "SITE-NILO": "Nilo",
  "SITE-RAUTA": "Rauta",
  "SITE-KOSKI": "Koski",
};
const COLUMN = { claims: 0.15, units: 0.46, classes: 0.73, barrier: 0.92 };
const FIXED = {
  "TRN-042": [COLUMN.units, 0.2],
  "TRN-051": [COLUMN.units, 0.41],
  "TRN-100": [COLUMN.units, 0.62],
  "PROC-SFP-REPLACE": [COLUMN.units, 0.88],
  "cls-trn-gen1": [COLUMN.classes, 0.16],
  "cls-trn-gen2": [COLUMN.classes, 0.38],
  "SITE-NILO": [COLUMN.classes, 0.58],
  "SITE-RAUTA": [COLUMN.classes, 0.74],
  "SITE-KOSKI": [COLUMN.classes, 0.9],
  "BAR-NILO-1": [COLUMN.barrier, 0.58],
};

function drawGraph() {
  const svg = $("graph-svg");
  const { width, height } = svg.getBoundingClientRect();
  if (!width || !state) return;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.replaceChildren();

  const claimNodes = state.graph.nodes.filter((n) => n.kind === "claim");
  const positions = {};
  for (const [id, [fx, fy]] of Object.entries(FIXED)) positions[id] = [fx * width, 14 + fy * (height - 26)];
  claimNodes.forEach((node, index) => {
    positions[node.id] = [
      COLUMN.claims * width,
      22 + ((index + 0.5) / Math.max(claimNodes.length, 1)) * (height - 34),
    ];
  });

  [["claims", COLUMN.claims], ["units", COLUMN.units], ["classes, sites", COLUMN.classes]].forEach(
    ([text, fx]) =>
      svgEl("text", { x: fx * width, y: 10, class: "g-column", "text-anchor": "middle" }, svg, text)
  );

  const used = usedByAnswer();
  const focus = selected ? new Set([selected]) : used;
  const relClass = {
    ABOUT: "about",
    APPLIES_TO: "applies",
    SUPERSEDES: "supersedes",
    CONFLICTS_WITH: "conflicts",
  };
  const relLabel = { APPLIES_TO: "applies to", SUPERSEDES: "supersedes", CONFLICTS_WITH: "conflicts" };
  for (const edge of state.graph.edges) {
    const a = positions[edge.src];
    const b = positions[edge.dst];
    if (!a || !b) continue;
    const classes = ["g-edge", relClass[edge.rel] || ""];
    if (focus.has(edge.src) || focus.has(edge.dst)) classes.push("lit");
    const sameColumn = a[0] === b[0];
    let d;
    if (sameColumn) {
      // Between two claims: bow out to the left of the column, where nothing else runs.
      const out = a[0] - 34;
      d = `M${out},${a[1]} C${out - 30},${a[1]} ${out - 30},${b[1]} ${out},${b[1]}`;
    } else {
      const mid = (a[0] + b[0]) / 2;
      d = `M${a[0]},${a[1]} C${mid},${a[1]} ${mid},${b[1]} ${b[0]},${b[1]}`;
    }
    svgEl("path", { d, class: classes.join(" ") }, svg);
    if (relLabel[edge.rel]) {
      const midY = (a[1] + b[1]) / 2;
      const midX = sameColumn ? 11 : (a[0] + b[0]) / 2;
      svgEl(
        "text",
        {
          x: midX,
          y: sameColumn ? midY : midY - 3,
          class: "g-edge-label",
          "text-anchor": "middle",
          ...(sameColumn ? { transform: `rotate(-90 ${midX} ${midY})` } : {}),
        },
        svg,
        relLabel[edge.rel]
      );
    }
  }

  const asked = answer?.entity;
  for (const node of state.graph.nodes) {
    const position = positions[node.id];
    if (!position) continue;
    const isClaim = node.kind === "claim";
    const label = isClaim ? node.id : NODE_LABEL[node.id] || node.name;
    const w = Math.max(48, label.length * 7.4 + 12);
    const classes = ["g-node", node.kind];
    if (isClaim && node.binding_status === "waiting") classes.push("waiting");
    if (isClaim && node.superseded_at) classes.push("superseded");
    if (isClaim && focus.has(node.id)) classes.push("lit");
    if (node.id === asked) classes.push("unit-lit");
    const group = svgEl("g", { class: classes.join(" "), transform: `translate(${position[0]},${position[1]})` }, svg);
    svgEl("rect", { x: -w / 2, y: -11, width: w, height: 22, rx: 4 }, group);
    svgEl("text", {}, group, label);
    if (isClaim) {
      svgEl("title", {}, group, node.claim_text);
      group.addEventListener("click", () => selectClaim(node.id));
    }
  }
}

// The agent

let askedAt = null;

function setQuestion(ask) {
  askedAt = ask.at || null;
  $("unit").value = ask.unit;
  if (ask.symptom) $("symptom").value = ask.symptom;
  const counters = ask.counters || "unknown";
  document.querySelector(`input[name="counters"][value="${counters}"]`).checked = true;
  $("bounce-failed").checked = Boolean(ask.bounce_failed);
  showSymptomField();
}

function showSymptomField() {
  const access = $("unit").value.startsWith("SITE");
  $("symptom-field").hidden = access;
  $("observed").hidden = access;
}

async function askAgent() {
  const unit = $("unit").value;
  try {
    if (unit.startsWith("SITE")) {
      const at = askedAt ? `&at=${encodeURIComponent(askedAt)}` : "";
      answer = await api(`/access_for?place=${encodeURIComponent(unit)}${at}`);
      answer.asked_at_time = askedAt;
    } else {
      const counters = document.querySelector('input[name="counters"]:checked').value;
      answer = await api("/claims_for", {
        method: "POST",
        body: JSON.stringify({
          entity: unit,
          symptom: $("symptom").value,
          observed: { counters, bounce_failed: $("bounce-failed").checked },
        }),
      });
    }
    answer.entity = unit;
    drawAnswer();
    drawClaims();
    drawGraph();
    // An answer can log a gap, so the numbers beside it should follow.
    state = await api("/state");
    drawSources();
  } catch (error) {
    $("answer").innerHTML = `<p class="empty">${esc(error.message)}</p>`;
  }
}

function drawAnswer() {
  const box = $("answer");
  if (!answer) {
    const line = state?.log[0];
    box.innerHTML = line
      ? `
      <div class="answer-head"><span class="tier learned">FROM THE DEVICES</span>
        <span class="match">${esc(line.entity)} · nobody wrote this down</span></div>
      <dl class="log">
        <dt>The agent proposed</dt><dd>${esc(line.next_step)}</dd>
        <dt>A person did</dt><dd>${esc(line.human_did)}</dd>
        <dt>The outcome</dt><dd>${esc(line.outcome || "Not known")}</dd>
      </dl>
      <p class="empty">This is the record a later decision about autonomy would need, and it took nobody's time.</p>`
      : '<p class="empty">Ask something, or move through the scenes with the arrow keys.</p>';
    return;
  }
  const rows = [];
  if (answer.prohibition) rows.push(`<dt>Not yet</dt><dd class="no">${esc(answer.prohibition)}</dd>`);
  const used = answer.observed_used;
  if (used?.counters_from === "telemetry") {
    rows.push(`<dt>Counters</dt><dd class="read">${esc(used.counters)}, read from the device by the agent</dd>`);
  } else if (used?.counters_from === "reported") {
    rows.push(`<dt>Counters</dt><dd>${esc(used.counters)}, as reported</dd>`);
  }
  if (answer.match_note) rows.push(`<dt>Reach</dt><dd>${esc(answer.match_note)}</dd>`);
  if (answer.ask_group) rows.push(`<dt>Ask</dt><dd>${esc(answer.ask_group)}. The gap is logged.</dd>`);
  rows.push(`<dt>What would change this</dt><dd>${esc(answer.what_would_change)}</dd>`);
  if (answer.boundary_known === false) rows.push("<dt>Boundary</dt><dd>Not known</dd>");
  const shown = (answer.claims || []).filter((claim) => claim.status_for_entity !== "not_yet_valid");
  const side = shown
    .map(
      (claim) => `
      <div class="side">
        <div class="side-head">
          <span class="chip ${esc(claim.status_for_entity)}">${esc(claim.status_for_entity.replace("_", " "))}</span>
          <span>${esc(claim.claim_text)}</span>
        </div>
        ${claim.status_note ? `<p class="note">${esc(claim.status_note)}</p>` : ""}
        ${claim.status_for_entity === "disputed" && claim.binding_status === "waiting" ? `<p class="note">${esc(claim.match_note)}</p>` : ""}
        ${claim.status_for_entity === "not_applicable" ? `<p class="note">${esc(claim.match_note)}</p>` : ""}
        <pre class="evidence">${esc(claim.evidence_rendered)}</pre>
      </div>`
    )
    .join("");
  const when = answer.asked_at_time ? ` · as of ${esc(shortTime(answer.asked_at_time))}` : "";
  // Where a key is, is knowledge and not a proposal to do something.
  const tierLabel = answer.site && answer.tier === "propose" ? "KNOWN" : TIER_LABEL[answer.tier];
  box.innerHTML = `
    <div class="answer-head">
      <span class="tier ${esc(answer.tier)}">${tierLabel}</span>
      <span class="match">${esc(answer.entity)}${when}${answer.match_level ? ` · ${esc(answer.match_level)}` : ""}${answer.action_kind && answer.action_kind !== "none" ? ` · ${esc(answer.action_kind)}` : ""}</span>
    </div>
    <p class="next">${esc(answer.next_step)}</p>
    <dl>${rows.join("")}</dl>
    ${side ? `<div class="sides">${side}</div>` : ""}`;
}

// Overlays

function openOverlay(html) {
  $("overlay-body").innerHTML = html;
  $("overlay").hidden = false;
}

function closeOverlay() {
  $("overlay").hidden = true;
}

async function openSource(file) {
  const source = await api(`/source?file=${encodeURIComponent(file)}`);
  const origin =
    source.origin === "elisa"
      ? `Elisa's file ${esc(source.original_name)}, unchanged`
      : "Synthetic, written for this demo";
  const messages = source.messages
    .map(
      (m) => `
      <div class="message">
        <div class="who"><b>${esc(m.author)}</b> ${esc(m.role || "")} ${esc(m.time || "")}</div>
        <div class="body">${esc(m.text)}</div>
      </div>`
    )
    .join("");
  openOverlay(`
    <h3>${esc(source.subject || file)}</h3>
    <p class="sub">${origin}. sha256 ${esc(source.sha256)}</p>
    ${messages}`);
}

function showLimits() {
  openOverlay(`
    <h3>What this demo does not claim</h3>
    <p class="sub">Stated here, in the README and in the slides.</p>
    <ul class="limits">
      <li>The system never starts a conversation with a specialist.</li>
      <li>It shows the origin of a claim and what was reported about it, not the truth.</li>
      <li>It scores claims, not people: no personal assessment and no figure shown per person.</li>
      <li>Telling apart which units a claim applies to, before someone narrows it down, rests on synthetic data here.</li>
    </ul>
    <div class="two">
      <div><b>Real</b>The model reading the text, with its answers recorded. The binding, the rules and the agent's answers, running here and now.</div>
      <div><b>Simulated</b>All sources except Elisa's two files. The event stream, the telemetry, the graph and the clock. No real network, channel or person.</div>
    </div>`);
}

// Scenes

function drawScenes() {
  $("scenes").replaceChildren(
    ...SCENES.map((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `<b>${index + 1}</b>${esc(item.title)}`;
      if (index === scene) button.setAttribute("aria-current", "step");
      button.addEventListener("click", () => goTo(index));
      return button;
    })
  );
}

function drawAll() {
  $("clock").textContent = state.as_of ? shortTime(state.as_of, true) : "now";
  drawTimeline();
  drawSources();
  drawClaims();
  drawGraph();
  drawAnswer();
}

async function goTo(index) {
  if (busy) return;
  busy = true;
  closeOverlay();
  scene = Math.max(0, Math.min(index, SCENES.length - 1));
  const item = SCENES[scene];
  drawScenes();
  $("caption").textContent = item.caption;
  for (const panel of document.querySelectorAll(".panel")) {
    const lit = item.lit.includes(panel.id);
    panel.classList.toggle("lit", lit);
    panel.classList.toggle("dim", item.lit.length > 0 && !lit);
  }
  try {
    const before = item.askedBefore;
    if (before) {
      await api("/clock", { method: "POST", body: JSON.stringify({ as_of: before.clock }) });
      await api("/claims_for", {
        method: "POST",
        body: JSON.stringify({ entity: before.entity, symptom: before.symptom }),
      });
    }
    state = await api("/clock", {
      method: "POST",
      body: JSON.stringify({ as_of: item.clock, fresh: Boolean(item.fresh) }),
    });
    answer = null;
    selected = null;
    if (item.selectUnit) {
      selected = state.claims.find((claim) => claim.observed_entity === item.selectUnit)?.id ?? null;
    }
    drawAll();
    if (item.ask) {
      setQuestion(item.ask);
      await askAgent();
    }
    if (item.source) await openSource(item.source);
    if (item.limits) showLimits();
  } catch (error) {
    $("caption").textContent = error.message;
  } finally {
    busy = false;
  }
}

// Wiring

$("symptom").value = SYMPTOM;
$("unit").addEventListener("change", showSymptomField);
$("ask").addEventListener("submit", (event) => {
  event.preventDefault();
  askedAt = null;
  askAgent();
});
$("presets").replaceChildren(
  ...PRESETS.map((preset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      setQuestion(preset.ask);
      askAgent();
    });
    return button;
  })
);
$("overlay-close").addEventListener("click", closeOverlay);
$("overlay").addEventListener("click", (event) => {
  if (event.target === $("overlay")) closeOverlay();
});
document.addEventListener("keydown", (event) => {
  const typing = ["INPUT", "SELECT"].includes(document.activeElement?.tagName);
  if (event.key === "Escape") closeOverlay();
  if (typing) return;
  if (event.key === "ArrowRight") goTo(scene + 1);
  if (event.key === "ArrowLeft") goTo(scene - 1);
});
window.addEventListener("resize", () => {
  drawTimeline();
  drawGraph();
});

goTo(0);
