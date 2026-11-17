const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
function parseCSV(txt) {
  const rows = []; let f = "", row = [], q = false;
  for (let i = 0; i <= txt.length; i++) {
    const c = txt[i];
    if (q) {
      if (c === '"') { if (txt[i+1] === '"') { f += '"'; i++; } else q = false; }
      else if (c === undefined) {} else f += c;
    } else if (c === '"') q = true;
    else if (c === ',' ) { row.push(f); f = ""; }
    else if (c === '\n' || c === undefined) { row.push(f); f = ""; rows.push(row); row = []; }
    else if (c !== '\r') f += c;
  }
  return rows.filter(r => r.length > 1);
}
Promise.all([
  fetch("data/latest-lite.json", {cache:"no-cache"}).then(r=>r.ok?r:Promise.reject()).catch(()=>fetch("data/latest.json",{cache:"no-cache"})).then(r => r.json()),
  fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json()),
  loadKinds(),
]).then(([snap, txt]) => {
  const today = (snap.date || snap.generated_at || "").slice(0,10);
  const seenBefore = new Set();
  for (const [url, it] of Object.entries(txt.items)) {
    for (const d of Object.keys(it.days)) if (d < today) { seenBefore.add(it.source + "|" + url); break; }
  }
  const items = Array.isArray(snap.items) ? snap.items
    : Object.entries(snap.items || {}).flatMap(([src, list]) =>
        (Array.isArray(list) ? list : []).map(i => ({...i, source: i.source || src})));
  const fresh = items.filter(i => i.url && !seenBefore.has(i.source + "|" + i.url));
  const bySrc = {};
  for (const i of fresh) (bySrc[i.source] = bySrc[i.source]||[]).push(i);
  document.getElementById("sub").innerHTML =
    `<b>${fresh.length}</b> of ${items.length} board items are first-seen today (${(100*fresh.length/Math.max(items.length,1)).toFixed(0)}%) · snapshot ${today}`;
  document.getElementById("out").innerHTML = Object.entries(bySrc)
    .sort((a,b)=>b[1].length-a[1].length).map(([src,list]) =>
      `<li style="display:block;padding:8px 0"><b style="color:var(--dim)">${esc(srcName(src))} · ${list.length} new</b>` +
      list.map(i => `<div style="display:flex;gap:8px;padding:3px 0 3px 14px;border-bottom:1px solid var(--border)">
        <a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title)}</a>${kindChip(i.url)}
        <span style="margin-left:auto;color:var(--dim);font-size:12px;white-space:nowrap">${scoreText(i, fmt)}</span></div>`).join("") + `</li>`).join("")
    || `<li id="err">nothing new — every board item has been seen before</li>`;
}).catch(() => { document.getElementById("err").textContent = "data unavailable"; });
