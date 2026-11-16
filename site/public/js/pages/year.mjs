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

const MN = { "01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
             "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec" };
const row = (m, c, linkTitle) => c ?
  `<li><span class="r">${MN[m.slice(5)]}</span><span class="it">
   <a href="${linkTitle && c.url ? c.url : c.hn}">${esc(c.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(c.title)}" title="trajectory">⤳</a></span>
   <span class="sc"><b>${fmt(c.points)}</b> pts</span></li>` : "";

const mpick = document.getElementById("mpick");
const years = [...new Set(months.map(m => m.slice(0,4)))].sort().reverse();
mpick.innerHTML = years.map(y => `<option>${y}</option>`).join("");
function render(y) {
  const top1 = (arr) => {
    const byMonth = {};
    arr.filter(c => c.month.startsWith(y) && c.rank === 1).forEach(c => byMonth[c.month] = c);
    return byMonth;
  };
  const s1 = top1(story), l1 = top1(launch), a1 = top1(ask);
  const mlist = months.filter(m => m.startsWith(y));
  document.getElementById("story").innerHTML = mlist.map(m => row(m, s1[m], false)).join("") ||
    '<li class="it" style="color:var(--dim)">no data</li>';
  document.getElementById("launch").innerHTML = mlist.map(m => row(m, l1[m], true)).join("") ||
    '<li class="it" style="color:var(--dim)">Show HN starts 2012</li>';
  document.getElementById("ask").innerHTML = mlist.map(m => row(m, a1[m], false)).join("") ||
    '<li class="it" style="color:var(--dim)">no data</li>';
}
mpick.onchange = () => { render(mpick.value); history.replaceState(null,"","?y="+mpick.value); };
const P = new URLSearchParams(location.search);
mpick.value = years.includes(P.get("y")) ? P.get("y") : years[0];
render(mpick.value);
