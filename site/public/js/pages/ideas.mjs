const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = id => document.getElementById(id);

// Supply-side context: this month's HN hiring threads.
fetch("data/hiring.json").then(r => r.ok ? r.json() : null).then(hp => {
  const t = (hp && hp.threads) || {};
  if (!t.hiring && !t.seeking) return;
  const b = (k, lbl) => t[k] ? `<a href="${t[k].url}">${lbl}: <b>${t[k].comments}</b></a>` : "";
  $("hiring").innerHTML = `Labor market · ${(t.hiring || t.seeking).month} — ` +
    [b("hiring", "who's hiring"), b("seeking", "wants to be hired")].filter(Boolean).join(" · ");
}).catch(() => {});

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i+1] === '"') { field += '"'; i++; } else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const STOP = new Set(("a an the is are was were be been what which who whom how when where why do does did " +
  "can could should would will shall may might must i you he she it we they me him her us them my your its our their " +
  "this that these those there here to of in on at for with about as by from or and but if not no so too very just " +
  "any some all one two get got have has had hn ask tell show self best new more much most now today use used using " +
  "name something anything everything nothing someone anyone everyone like make made take look people really also " +
  "start started down done doing run running want wanted stuff thing things way ways good great big small old " +
  "advice ideas idea question questions anyone advice build builds built state future 2026").split(" "));
const SKIP = /^(ask hn|tell hn|show hn|hn)[:?]?\s*/i;

function tokens(title) {
  const words = title.toLowerCase().replace(SKIP, "").split(/[^a-z0-9]+/)
    .filter(w => w.length > 2 && !STOP.has(w) && !/^\d+$/.test(w));
  const out = [];
  for (const w of words) out.push(w);
  for (let i = 0; i < words.length - 1; i++) out.push(words[i] + " " + words[i+1]);
  return out;
}

const ser = await fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json());

// dedupe ask_hn items by url: max score, days seen
const items = {}, allDates = new Set();
for (const [url, o] of Object.entries(ser.items)) {
  if (o.source !== "ask_hn") continue;
  const it = items[url] ||= { title: o.title, days: new Set(), maxScore: 0 };
  for (const [d, [sc]] of Object.entries(o.days)) {
    it.days.add(d); allDates.add(d);
    it.maxScore = Math.max(it.maxScore, sc);
  }
}
const recs = Object.entries(items).map(([url, it]) => ({ url, ...it, nDays: it.days.size }));
const sorted = [...allDates].sort(); allDates.clear(); for (const d of sorted) allDates.add(d);
const datesArr = sorted;
const latest = datesArr[datesArr.length-1];

// demand volume: ask_hn threads per day
const perDay = {};
for (const it of Object.values(items)) for (const d of it.days) perDay[d] = (perDay[d]||0) + 1;
const pdays = datesArr.slice(-14);
const pmax = Math.max(...pdays.map(d => perDay[d]||0), 1);
const strip = pdays.map(d => `<span class="db" title="${d}: ${perDay[d]||0} threads"><i style="height:${Math.max(2, Math.round((perDay[d]||0)/pmax*26))}px"></i><s>${d.slice(8)}</s></span>`).join("");

// everything ELSE on our radar — used to mark themes as "already built" or "gap"
const others = [];
for (const [url, o] of Object.entries(ser.items)) {
  if (o.source === "ask_hn") continue;
  const sc = Math.max(...Object.values(o.days).map(v => v[0]));
  others.push({ title: o.title || "", url, source: o.source, score: sc });
}
// does anything already address this theme? title contains the theme words
const coverage = theme =>
  others.filter(o => theme.split(" ").every(w => o.title.toLowerCase().includes(w)))
        .sort((a, b) => b.score - a.score);

// theme clustering: map token -> urls; keep tokens spanning ≥2 threads
const tokMap = new Map();
for (const r of recs) for (const t of new Set(tokens(r.title))) {
  if (!tokMap.has(t)) tokMap.set(t, new Set());
  tokMap.get(t).add(r.url);
}
const themes = [...tokMap.entries()]
  // bigrams always allowed; single words need ≥3 threads to be a theme
  .filter(([t, us]) => us.size >= (t.includes(" ") ? 2 : 3))
  .map(([t, us]) => ({
    name: t,
    urls: us,
    score: [...us].reduce((s,u) => s + (items[u] ? items[u].maxScore : 0), 0),
  }))
  // drop themes fully contained in a bigger theme on the same urls
  .sort((a,b) => b.score - a.score);
const seen = new Set();
const topThemes = themes.filter(th => {
  const fresh = [...th.urls].filter(u => !seen.has(u));
  if (fresh.length < 2) return false; // a "theme" needs ≥2 visible threads
  th.urls = new Set(fresh);
  return true;
}).slice(0, 8);
topThemes.forEach(th => th.urls.forEach(u => seen.add(u)));

// today's board
const snap = await fetch("data/latest.json", {cache:"no-cache"}).then(r => r.json());
const today = (snap.items?.ask_hn || []).slice(0, 12);

$("stats").innerHTML =
  `<div class="stat"><b>${recs.length}</b><small>unique ask/tell threads</small></div>
   <div class="stat"><b>${datesArr.length}</b><small>days of demand data</small></div>
   <div class="stat"><b>${topThemes.length}</b><small>recurring themes</small></div>
   <div class="stat"><b>${latest}</b><small>latest snapshot</small></div>`;

const row = (r, badge = "") =>
  `<li><span class="it"><a href="${r.url}" target="_blank" rel="noopener">${esc(r.title)}</a><a href="item.html?q=${encodeURIComponent(r.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
   <span class="sc">${badge} <span class="pts">${r.maxScore ?? r.score} pts</span>${r.nDays > 1 ? ` <span class="days">· ${r.nDays}d on board</span>` : ""}</span></li>`;

$("out").innerHTML =
  `<h2>demand volume — threads per day</h2><p id="vol" class="strip">${strip}</p>` +
  `<h2>today's ask board (${snap.date})</h2><ol>` +
    today.map(i => row({...i, maxScore: i.score, nDays: (items[i.url]?.nDays)||1}, "")).join("") + `</ol>` +
  `<h2>recurring demand themes</h2>` +
    (topThemes.length ? topThemes.map(th => {
      const cov = coverage(th.name);
      const tag = cov.length
        ? `<span class="sc" style="margin-left:8px">built: <a href="${cov[0].url}" target="_blank" rel="noopener">${esc(cov[0].title.slice(0, 42))}</a> <span class="src">${srcName(cov[0].source)}</span></span>`
        : `<span class="sc" style="margin-left:8px;color:var(--green)">◆ gap — nothing on our radar addresses it</span>`;
      return `<div class="theme"><h3>${esc(th.name)} <b>×${th.urls.size}</b>${tag}</h3><ul>` +
        [...th.urls].map(u => row({...items[u], url: u})).join("") +
        `</ul></div>`;
    }).join("")
    : `<p style="color:var(--dim)">needs 2+ days of ask_hn data — check back soon.</p>`) +
  `<h2>top asks of all time</h2><ol>` +
    [...recs].sort((a,b) => b.maxScore - a.maxScore).slice(0, 15).map(r => row(r)).join("") + `</ol>`;
