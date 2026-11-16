const fmt = n => n >= 1000 ? (n/1000).toFixed(1) + "k" : String(n);
const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (const c of text) {
    if (inQ) { if (c === '"') inQ = false; else field += c; }
    else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}
async function load(path) {
  const t = await fetch(path, {cache:"no-cache"}).then(r => r.text());
  return parseCSV(t).slice(1).filter(r => r.length >= 8 && r[0]).map(r => ({
    month: r[0], rank: +r[1], title: r[2], url: r[3], points: +r[4] || 0,
    comments: +r[5] || 0, author: r[6], hn: r[8] }));
}
const [story, launch, ask] = await Promise.all([
  load("data/hn-canon-monthly.csv"), load("data/show-hn-monthly.csv"), load("data/ask-hn-monthly.csv")]);
const months = [...new Set([...story.map(c=>c.month), ...launch.map(c=>c.month), ...ask.map(c=>c.month)])].sort();

document.getElementById("stats").innerHTML = `
  <div class="stat"><b>${months.length}</b><small>months</small></div>
  <div class="stat"><b>${fmt(story.length + launch.length + ask.length)}</b><small>ritual entries</small></div>
  <div class="stat"><b>${fmt(Math.max(...story.map(c=>c.points)))}</b><small>peak story</small></div>
  <div class="stat"><b>${fmt(Math.max(...launch.map(c=>c.points)))}</b><small>peak launch</small></div>
  <div class="stat"><b>${fmt(Math.max(...ask.map(c=>c.points)))}</b><small>peak question</small></div>`;

const row = (c, linkTitle=true) =>
  `<li><span class="r">${c.rank}</span><span class="it">
   <a href="${linkTitle && c.url ? c.url : c.hn}">${esc(c.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(c.title)}" title="trajectory">⤳</a></span>
   <span class="sc"><b>${fmt(c.points)}</b> pts</span></li>`;

const mpick = document.getElementById("mpick");
mpick.innerHTML = [...months].reverse().map(m => `<option>${m}</option>`).join("");
function render(m) {
  const pick = (arr) => arr.filter(c => c.month === m).sort((a,b) => a.rank - b.rank);
  document.getElementById("story").innerHTML = pick(story).map(c => row(c, false)).join("") ||
    '<li class="it" style="color:var(--dim)">no data this month</li>';
  document.getElementById("launch").innerHTML = pick(launch).map(c => row(c)).join("") ||
    '<li class="it" style="color:var(--dim)">Show HN starts 2012</li>';
  document.getElementById("ask").innerHTML = pick(ask).map(c => row(c, false)).join("") ||
    '<li class="it" style="color:var(--dim)">no data this month</li>';
}
mpick.onchange = () => render(mpick.value);
const P = new URLSearchParams(location.search);
mpick.value = months.includes(P.get("m")) ? P.get("m") : months[months.length - 1];
render(mpick.value);
