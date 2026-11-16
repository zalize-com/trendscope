const $ = id => document.getElementById(id);
const esc = s => { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const QP = new URLSearchParams(location.search);
let CORPS = [], activeCorp = "all";

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (const c of text) {
    if (inQ) {
      if (c === '"') inQ = false; else field += c;
    }
    else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

async function load(name, url, map) {
  const text = await fetch(url, {cache:"no-cache"}).then(r => r.text());
  const rows = parseCSV(text), hdr = rows.shift();
  return rows.filter(r => r.length >= 4 && r[0]).map(r => map(r, hdr)).map(x => ({...x, corp: name}));
}

const files = await Promise.all([
  load("canon", "data/hn-canon-monthly.csv",
       r => ({ title: r[2], url: r[3] || r[8], pts: +r[4] || 0, when: r[0], author: r[6] })),
  load("showhn", "data/show-hn-monthly.csv",
       r => ({ title: r[2], url: r[3] || r[8], pts: +r[4] || 0, when: r[0], author: r[6] })),
  load("askhn", "data/ask-hn-monthly.csv",
       r => ({ title: r[2], url: r[8] || r[3], pts: +r[4] || 0, when: r[0], author: r[6] })),
  load("recent", "data/history.csv",
       r => ({ title: r[3], url: r[4], pts: +r[5] || 0, when: r[0], author: r[8], src: r[1] })),
]);
CORPS = files.flat();
// corpus counts on chips
document.querySelectorAll("button[data-c]").forEach(b => {
  const n = b.dataset.c === "all" ? CORPS.length : files[["canon","showhn","askhn","recent"].indexOf(b.dataset.c)]?.length || 0;
  b.innerHTML += ` <small style="opacity:.6">${n.toLocaleString()}</small>`;
});

const qEl = $("q");
qEl.value = QP.get("q") || "";

function highlight(title, terms) {
  let out = esc(title);
  for (const t of terms) {
    if (!t) continue;
    const rx = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
    out = out.replace(rx, "<mark>$1</mark>");
  }
  return out;
}

function render() {
  const q = qEl.value.trim().toLowerCase();
  const terms = q.split(/\s+/).filter(Boolean);
  const pool = activeCorp === "all" ? CORPS : CORPS.filter(x => x.corp === activeCorp);
  if (!terms.length) {
    $("meta").textContent = `${CORPS.length.toLocaleString()} records loaded — type to search`;
    $("res").innerHTML = "";
    return;
  }
  const hits = pool.filter(x =>
    terms.every(t => (x.title + " " + (x.author||"") + " " + (x.src||"") + " " + x.when).toLowerCase().includes(t)));
  hits.sort((a, b) => b.pts - a.pts);
  const shown = hits.slice(0, 200);
  $("meta").textContent = `${hits.length.toLocaleString()} matches${hits.length > 200 ? " — top 200 by score" : ""}`;
  $("res").innerHTML = shown.map((x, i) =>
    `<li><span class="r">${i+1}</span>
      <span class="it"><a href="${x.url}" target="_blank" rel="noopener">${highlight(x.title, terms)}</a>
        <span class="yr">${x.when}${x.author ? " · " + esc(x.author) : ""}</span><span class="tag">${x.corp}${x.src ? "/" + x.src : ""}</span>${x.corp === "recent" ? `<a href="item.html?q=${encodeURIComponent(x.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a>` : ""}</span>
      <span class="sc"><b>${fmt(x.pts)}</b></span></li>`).join("");
}

let deb = null;
qEl.addEventListener("input", () => {
  clearTimeout(deb);
  deb = setTimeout(() => {
    const u = new URL(location.href);
    qEl.value.trim() ? u.searchParams.set("q", qEl.value.trim()) : u.searchParams.delete("q");
    history.replaceState(null, "", u);
    render();
  }, 120);
});
$("corp").addEventListener("click", e => {
  const c = e.target.dataset?.c; if (!c) return;
  activeCorp = c;
  document.querySelectorAll("#corp button").forEach(b => b.classList.toggle("on", b === e.target));
  render();
});
render();
