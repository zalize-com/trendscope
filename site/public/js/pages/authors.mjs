const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
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

const aApi = await fetch("docs/api/authors.json", {cache:"no-cache"}).then(r => r.json());
const list = aApi.authors
  .map(a => ({ who: a.author, hits: a.items, srcs: a.sources, top: a.top_hit,
               ndays: a.days_on_board }))
  .sort((x, y) => y.ndays - x.ndays || y.hits - x.hits)
  .slice(0, 40);

$("out").innerHTML = list.length
  ? `<table><tr><th>author</th><th class="num">days</th><th class="num">items</th><th>sources</th><th>top hit</th></tr>` +
    list.map(a =>
      `<tr><td><a class="who" href="author.html?u=${encodeURIComponent(a.who)}">${esc(a.who)}</a></td>
       <td class="num">${a.ndays}</td><td class="num">${a.hits}</td>
       <td class="srcs">${a.srcs.map(srcName).join(", ")}</td>
       <td class="last"><a href="${a.top.url}">${esc(a.top.title.length>70?a.top.title.slice(0,70)+"…":a.top.title)}</a><a href="item.html?q=${encodeURIComponent(a.top.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></td></tr>`).join("") +
    `</table>`
  : `<p id="err">No author data yet — only some sources carry an author field.</p>`;
