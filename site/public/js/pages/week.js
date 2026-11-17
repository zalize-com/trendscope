const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M"
             : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const SKIP = new Set(["news.ycombinator.com","github.com","lobste.rs","dev.to",
  "producthunt.com","techmeme.com","slashdot.org","crates.io","pypi.org","npmjs.com"]);

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

fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json()).then(ser => {
  const recs = [];
  for (const [url, it] of Object.entries(ser.items)) {
    for (const [date, [score, rank]] of Object.entries(it.days)) {
      recs.push({title: it.title, url, source: it.source, metric: it.metric,
                 date, score, rank});
    }
  }
  const WIN = Math.min(30, Math.max(2, +new URLSearchParams(location.search).get("d") || 7));
  document.getElementById("wjson").innerHTML =
    `<a href="docs/api/${WIN >= 30 ? "month" : "week"}.json">↓ json</a>`;
  document.getElementById("h1").innerHTML = `last <span>${WIN} days</span>`;
  document.title = `last ${WIN} days — trendscope`;
  const days = [...new Set(recs.map(r => r.date))].sort();
  const win = new Set(days.slice(-WIN));
  const wk = recs.filter(r => win.has(r.date));
  // per-day per-source max score → heat = score/max (rolling-window metrics like
  // pypi monthly downloads would otherwise swamp cumulative raw-score ranking)
  const mx = {};
  for (const r of wk) {
    const k = r.date + "|" + r.source;
    mx[k] = Math.max(mx[k] || 0, +r.score || 0);
  }
  // aggregate by url (dedup a story appearing across days)
  const byUrl = {};
  for (const r of wk) {
    const k = r.url || r.title;
    const e = byUrl[k] || (byUrl[k] = {title: r.title, url: r.url, source: r.source,
      total: 0, days: new Set(), bestRank: 99, metric: r.metric});
    e.total += (+r.score || 0) / (mx[r.date + "|" + r.source] || 1);
    e.days.add(r.date);
    e.bestRank = Math.min(e.bestRank, +r.rank || 99);
  }
  const items = Object.values(byUrl);
  const wdays = [...win];
  const perDay = wdays.map(d => wk.filter(r => r.date === d).length);
  const pmax = Math.max(...perDay, 1);
  document.getElementById("daystrip").innerHTML = wdays.map((d, i) =>
    `<span class="db" title="${d}: ${perDay[i]} items"><i style="height:${Math.max(2, Math.round(perDay[i] / pmax * 26))}px"></i><s>${d.slice(8)}</s></span>`).join("");
  document.getElementById("sub").textContent =
    `${wdays[0]} → ${wdays[wdays.length - 1]} · ${items.length} unique items · ${wk.length} rows`;
  const srcCounts = {};
  items.forEach(e => srcCounts[e.source] = (srcCounts[e.source] || 0) + 1);
  const selSrc = new URLSearchParams(location.search).get("s") || "";
  const chips = [`<span class="chip ${!selSrc ? "on" : ""}" data-s="">all</span>`]
    .concat(Object.keys(srcCounts).sort((a,b) => srcCounts[b] - srcCounts[a])
      .map(s => `<span class="chip ${s === selSrc ? "on" : ""}" data-s="${s}">${srcName(s)} ${srcCounts[s]}</span>`))
    .join("");
  const items2 = selSrc ? items.filter(e => e.source === selSrc) : items;
  const top = items2.sort((a,b) => b.total - a.total).slice(0, 50);
  const multi = items.filter(e => e.days.size >= Math.min(3, WIN))
    .sort((a,b) => b.days.size - a.days.size || b.total - a.total).slice(0, 15);
  document.getElementById("out").innerHTML = `
    <h2>top of the window — by cumulative heat</h2>
    <p id="chips" class="src-chips">${chips}</p>
    <p style="margin:4px 0 10px;font-size:12px"><a id="wk-csv" style="cursor:pointer">⤓ download window as CSV</a> <span class="muted">· top-50 by cumulative heat</span></p>
    <ol>${top.map((e,i) => `<li><span class="sc" style="min-width:16px;text-align:right">${i+1}</span>
      <span class="it"><a href="${e.url}">${esc(e.title)}</a><span class="src">${srcName(e.source)}</span>
      <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
      <span class="sc">${e.total.toFixed(1)} heat</span></li>`).join("")
      || `<li><span id="err">no ${selSrc} items in window</span></li>`}</ol>
    <h2>staying power — on the board 3+ days</h2>
    <ol>${multi.map(e => `<li><span class="it"><a href="${e.url}">${esc(e.title)}</a><span class="src">${srcName(e.source)}</span>
      <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
      <span class="sc"><span class="days">${e.days.size}d</span> · ${e.total.toFixed(1)} heat</span></li>`).join("")
      || `<li><span id="err">none yet — the dataset needs a few more days</span></li>`}</ol>`;
  document.getElementById("chips").onclick = ev => {
    const c = ev.target.closest(".chip");
    if (!c) return;
    const u = new URL(location.href);
    c.dataset.s ? u.searchParams.set("s", c.dataset.s) : u.searchParams.delete("s");
    location.href = u;
  };
  document.getElementById("wk-csv").onclick = () => {
    const esc2 = v => '"' + String(v ?? "").replace(/"/g, '""') + '"';
    const rows = [["rank","title","url","source","days_on_board","total_heat"]]
      .concat(top.map((e, i) => [i + 1, e.title, e.url, e.source, e.days.size, e.total.toFixed(2)].map(esc2).join(",")));
    const blob = new Blob([rows.join("\n") + "\n"], {type: "text/csv"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `trendscope-week-${wdays[0]}_${WIN}d.csv`;
    a.click(); URL.revokeObjectURL(a.href);
  };
}).catch(e => { document.getElementById("err").textContent = "history unavailable"; });
