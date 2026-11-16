const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i+1] === '"') { field += '"'; i++; } else inQ = false; }
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const [domsApi, crossApi] = await Promise.all([
  fetch("docs/api/domains.json", {cache:"no-cache"}).then(r => r.json()),
  fetch("docs/api/crossovers.json", {cache:"no-cache"}).then(r => r.json())]);

const list = domsApi.domains
  .map(d => ({ h: d.hostname, hits: d.items, srcs: d.sources, top: d.top_hit,
               ndays: d.days_on_board }))
  .sort((a,b) => b.ndays - a.ndays || b.hits - a.hits)
  .slice(0, 40);

const cross = crossApi.crossovers
  .map(c => ({ url: c.url, title: c.title, srcs: c.sources, score: c.best.score }))
  .sort((a,b) => b.srcs.length - a.srcs.length || b.score - a.score);

$("out").innerHTML =
  `<table><tr><th>domain</th><th class="num">days</th><th class="num">items</th><th>sources</th><th>top hit</th></tr>` +
  list.map(d =>
    `<tr><td><a class="dom" href="domain.html?d=${encodeURIComponent(d.h)}">${esc(d.h)}</a></td>
     <td class="num">${d.ndays}</td><td class="num">${d.hits}</td>
     <td class="srcs">${d.srcs.join(", ")}</td>
     <td class="last"><a href="${d.top.url}">${esc(d.top.title.length>70?d.top.title.slice(0,70)+"…":d.top.title)}</a><a href="item.html?q=${encodeURIComponent(d.top.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></td></tr>`
  ).join("") + `</table>` +
  (cross.length ? `<h2 style="margin-top:28px">crossovers — same url on 2+ sources &nbsp;<a href="docs/api/crossovers.json" style="font-size:12px;font-weight:400">↓ json</a></h2><ol>` +
    cross.map(c =>
      `<li><span class="it"><a href="${c.url}">${esc(c.title.length>80?c.title.slice(0,80)+"…":c.title)}</a>` +
      `<span class="srcs" style="margin-left:6px">${c.srcs.join(" + ")}</span>` +
      `<a href="item.html?q=${encodeURIComponent(c.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>` +
      `<span class="sc">${fmt(c.score)}</span></li>`).join("") + `</ol>` : "") +
  // source-pair overlap: how many URLs each pair of sources shared
  (() => {
    const pairs = {};
    for (const e of cross) {
      const arr = [...e.srcs].sort();
      for (let i = 0; i < arr.length; i++)
        for (let j = i+1; j < arr.length; j++)
          pairs[arr[i]+"|"+arr[j]] = (pairs[arr[i]+"|"+arr[j]]||0) + 1;
    }
    const top = Object.entries(pairs).sort((a,b) => b[1]-a[1]).slice(0, 12);
    return top.length
      ? `<h2 style="margin-top:28px">source overlap — who shares stories</h2><ol>` +
        top.map(([k,n]) => `<li><span class="it">${k.replace("|", " ↔ ")}</span><span class="sc">${n} url${n>1?"s":""}</span></li>`).join("") + `</ol>`
      : "";
  })();
