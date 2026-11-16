const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);

const tabs = document.getElementById("tabs");
const tools = ["qr","og","robots","squat","http","hash","pxrem","utm","aifree","meta","aibots","spage","feed","badge","ogimg","favicon","sitemapgen","llmstxt","manifest","serp"];

// ---- status-page checker ----
function spreset(u){ const i=document.getElementById("sp-in"); if(i){ i.value=u; i.dispatchEvent(new Event("input")); } return false; }
(function(){
  const i = $("sp-in"), o = $("sp-out"); if(!i||!o) return;
  let deb=null;
  async function go(){
    const base=(i.value||"").trim().replace(/\/+$/,"");
    if(!/^https?:\/\//.test(base)) { o.innerHTML=""; return; }
    o.innerHTML='<span style="color:var(--dim)">checking…</span>';
    try {
      const d = await fetch(base+"/api/v2/summary.json").then(r=>r.json());
      const ind = d.status?.indicator || "none";
      const col = {none:"var(--green)",minor:"#f0883e",major:"#f85149",critical:"#f85149"}[ind]||"var(--dim)";
      const bad = (d.components||[]).filter(c=>c.status!=="operational");
      const incs = (d.incidents||[]);
      o.innerHTML = `<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
          <span style="width:10px;height:10px;border-radius:5px;background:${col}"></span>
          <b>${d.page?.name||base}</b> — ${d.status?.description||"unknown"}</div>`
        + (incs.length?`<h3 style="font-size:12px;color:var(--dim);margin:8px 0 4px">ACTIVE INCIDENTS (${incs.length})</h3>`
          + incs.map(x=>`<div style="padding:6px 0;border-bottom:1px solid var(--border)">
            <a href="${x.shortlink||'#'}" target="_blank" rel="noopener">${x.name}</a>
            <span style="color:var(--dim);font-size:12px"> · ${x.status} · ${x.impact||''}</span></div>`).join(""):"")
        + (bad.length?`<h3 style="font-size:12px;color:var(--dim);margin:8px 0 4px">DEGRADED (${bad.length})</h3>`
          + bad.map(c=>`<div style="font-size:13px">${c.name} — <span style="color:#f0883e">${c.status}</span></div>`).join("")
          :'<div style="color:var(--dim);font-size:12px;margin-top:6px">all components operational</div>');
    } catch(e){ o.innerHTML='<span style="color:var(--dim)">not a statuspage.io page (or fetch blocked)</span>'; }
  }
  i.addEventListener("input",()=>{ clearTimeout(deb); deb=setTimeout(go,400); });
  go();
})();

// ---- AI-free badge ----
function afSvg(label, style) {
  const w = 190, h = 32, rx = 5;
  const pal = {
    dark:   {bg:"#0f1115", fg:"#7ee2a8", bd:"#2a2e37"},
    light:  {bg:"#f5f5f0", fg:"#1a7a4a", bd:"#d0d0c8"},
    outline:{bg:"none",    fg:"#7ee2a8", bd:"#7ee2a8"},
  }[style] || {};
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
  <rect x="1" y="1" width="${w-2}" height="${h-2}" rx="${rx}" fill="${pal.bg}" stroke="${pal.bd}" stroke-width="1.5"/>
  <text x="${w/2}" y="${h/2+4}" font-family="ui-monospace,monospace" font-size="13" fill="${pal.fg}" text-anchor="middle">\u2726 ${label} \u2726</text>
</svg>`;
}
function afGo() {
  const label = document.getElementById("af-label").value;
  const style = document.getElementById("af-style").value;
  const svg = afSvg(label, style);
  document.getElementById("af-view").innerHTML = svg;
  document.getElementById("af-out").textContent =
    `<a href="https://trendscope--plov6nur.preview.devinapps.com/about.html" title="declared human-made">\n  ${svg.replace(/\n/g, "\n  ")}\n</a>`;
}
document.getElementById("af-label").addEventListener("change", afGo);
document.getElementById("af-style").addEventListener("change", afGo);
document.getElementById("af-copy").addEventListener("click", () => {
  navigator.clipboard.writeText(document.getElementById("af-out").textContent);
  document.getElementById("af-copy").textContent = "copied";
  setTimeout(() => document.getElementById("af-copy").textContent = "copy snippet", 1200);
});
afGo();

// ---- UTM builder ----
function utmGo() {
  const url = document.getElementById("ut-url").value.trim();
  const params = {};
  for (const k of ["source","medium","campaign","term","content"]) {
    const v = document.getElementById("ut-"+k).value.trim();
    if (v) params["utm_"+k] = v;
  }
  const out = document.getElementById("ut-out");
  if (!url) { out.value = ""; return; }
  try {
    const u = new URL(url);
    for (const [k,v] of Object.entries(params)) u.searchParams.set(k, v);
    out.value = u.toString();
  } catch {
    const sep = url.includes("?") ? "&" : "?";
    out.value = url + (Object.keys(params).length ? sep + new URLSearchParams(params).toString() : "");
  }
}
for (const k of ["url","source","medium","campaign","term","content"])
  document.getElementById("ut-"+k).addEventListener("input", utmGo);
// ---- social card audit ----
document.getElementById("ma-go").addEventListener("click", () => {
  const src = document.getElementById("ma-in").value;
  const out = document.getElementById("ma-out");
  if (!src.trim()) { out.innerHTML = ""; return; }
  const doc = new DOMParser().parseFromString(src, "text/html");
  const get = sel => (doc.querySelector(sel) || {}).content || "";
  const M = {
    title: doc.querySelector("title")?.textContent?.trim() || get('meta[name="twitter:title"]'),
    description: get('meta[name="description"]') || get('meta[property="og:description"]'),
    og_title: get('meta[property="og:title"]'),
    og_desc: get('meta[property="og:description"]'),
    og_image: get('meta[property="og:image"]'),
    og_url: get('meta[property="og:url"]'),
    og_type: get('meta[property="og:type"]'),
    tw_card: get('meta[name="twitter:card"]'),
    tw_title: get('meta[name="twitter:title"]'),
    tw_image: get('meta[name="twitter:image"]'),
    canonical: (doc.querySelector('link[rel="canonical"]') || {}).href || "",
    site_name: get('meta[property="og:site_name"]'),
  };
  const img = M.og_image || M.tw_image;
  const checks = [
    ["title", !!M.title], ["description", !!M.description],
    ["og:title", !!M.og_title], ["og:description", !!M.og_desc],
    ["og:image", !!img], ["og:url", !!M.og_url], ["og:type", !!M.og_type],
    ["twitter:card", !!M.tw_card], ["canonical", !!M.canonical],
    ["og:site_name", !!M.site_name],
  ];
  const miss = checks.filter(c => !c[1]);
  const mark = ok => ok ? '<b style="color:var(--green)">✓</b>' : '<b style="color:#e5534b">✗</b>';
  const row = (k, v) => `<div class="row" style="font-size:12px"><span style="color:var(--dim);width:110px;display:inline-block">${k}</span> <span>${v ? v.replace(/</g,"&lt;") : "<i style=color:var(--dim)>—</i>"}</span></div>`;
  out.innerHTML = `<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:10px">
    <div style="border:1px solid var(--border);border-radius:10px;overflow:hidden;width:330px;flex-shrink:0">
      ${img ? `<img src="${img}" style="width:100%;height:170px;object-fit:cover;display:block" onerror="this.outerHTML='<div style=\\'height:170px;background:#161b22;display:flex;align-items:center;justify-content:center;color:var(--dim)\\'>image failed to load</div>'">`
            : `<div style="height:170px;background:#161b22;display:flex;align-items:center;justify-content:center;color:var(--dim)">no og:image</div>`}
      <div style="padding:10px;background:var(--panel)">
        <div style="font-size:13px;font-weight:600">${(M.og_title || M.tw_title || M.title || "untitled").replace(/</g,"&lt;")}</div>
        <div style="font-size:12px;color:var(--dim);margin-top:3px">${(M.og_desc || M.description || "").replace(/</g,"&lt;").slice(0, 140)}</div>
        <div style="font-size:11px;color:var(--dim);margin-top:6px">${(M.og_url || "").replace(/</g,"&lt;")}</div>
      </div>
    </div>
    <div style="flex:1;min-width:260px">
      <p style="margin:0 0 6px">${mark(!miss.length)} ${miss.length ? miss.length + " missing" : "all key tags present"}</p>
      ${checks.map(c => `<span style="display:inline-block;margin:2px 8px 2px 0;font-size:12px">${mark(c[1])} ${c[0]}</span>`).join("")}
      <div style="margin-top:10px">${row("twitter:card", M.tw_card)}${row("og:type", M.og_type)}${row("canonical", M.canonical)}</div>
    </div></div>`;
});
/* ---------- manifest.json builder ---------- */
(function () {
  function go() {
    const v = id => $(id).value.trim();
    const name = v("mf-name"), short = v("mf-short"), start = v("mf-start"),
          disp = v("mf-display"), theme = v("mf-theme"), bg = v("mf-bg");
    const icons = v("mf-icons").split(",").map(x => x.trim()).filter(Boolean).map(fn => {
      const m = fn.match(/(\d+)/);
      const sz = m ? m[1] : "192";
      return { src: fn, sizes: sz + "x" + sz, type: "image/png" };
    });
    if (!name && !short && !icons.length) { $("mf-out").textContent = ""; $("mf-err").textContent = ""; return; }
    const man = {
      name: name || "My App",
      short_name: short || name || "App",
      start_url: start || "/",
      display: disp,
      background_color: bg || "#ffffff",
      theme_color: theme || "#ffffff",
      icons,
    };
    $("mf-out").textContent = JSON.stringify(man, null, 2);
    $("mf-err").textContent = icons.length ? "" : "⚠ no icons — add file names like android-chrome-192.png";
  }
  for (const id of ["mf-name","mf-short","mf-start","mf-display","mf-theme","mf-bg","mf-icons"])
    $(id).addEventListener("input", go);
  $("mf-copy").onclick = () => navigator.clipboard?.writeText($("mf-out").textContent).then(() => { $("mf-copy").textContent = "copied"; setTimeout(() => $("mf-copy").textContent = "copy manifest.json", 1200); });
  $("mf-name").value = "trendscope"; $("mf-short").value = "trendscope";
  $("mf-start").value = "/"; $("mf-theme").value = "#0d1117"; $("mf-bg").value = "#0d1117";
  $("mf-icons").value = "favicon-16.png,android-chrome-192.png,android-chrome-512.png";
  go();
})();

/* ---------- SERP + social card preview ---------- */
(function () {
  function render() {
    const src = $("sv-in").value;
    const out = $("sv-out"); out.innerHTML = "";
    if (!src.trim()) return;
    const doc = new DOMParser().parseFromString(src, "text/html");
    const g = sel => (doc.querySelector(sel) || {}).content || "";
    const title = doc.querySelector("title")?.textContent?.trim() || "(no title)";
    const desc = g('meta[name="description"]') || "(no description)";
    const url = $("sv-url").value.trim() || "https://example.com";
    const host = (() => { try { return new URL(url).hostname; } catch { return "example.com"; } })();
    const img = g('meta[property="og:image"]') || g('meta[name="twitter:image"]');
    const tlen = title.length, dlen = desc.length;
    const lenNote = (n, lo, hi) => n > hi ? ` <span style="color:#f85149">${n} chars — over ${hi}, likely truncated</span>` : ` <span class="muted">${n} chars</span>`;
    out.innerHTML = `
      <div style="background:#fff;color:#202124;border-radius:8px;padding:14px 16px;max-width:600px;font-family:arial,sans-serif">
        <div style="font-size:12px;color:#4d5156">${host} › …</div>
        <div style="font-size:20px;color:#1a0dab;line-height:1.3">${title.replace(/</g,"&lt;")}</div>
        <div style="font-size:13px;color:#4d5156">${desc.replace(/</g,"&lt;")}</div>
      </div>
      <div class="hint" style="margin-top:4px">title${lenNote(tlen,50,60)} · description${lenNote(dlen,140,160)}</div>
      <div style="border:1px solid var(--border);border-radius:10px;overflow:hidden;max-width:500px;margin-top:14px">
        ${img ? `<img src="${img.replace(/"/g,"&quot;")}" style="width:100%;aspect-ratio:1200/630;object-fit:cover;background:var(--bg)" onerror="this.style.display='none'">` : `<div style="height:120px;display:flex;align-items:center;justify-content:center;color:var(--dim)">no og:image</div>`}
        <div style="padding:10px 12px;background:var(--bg)">
          <div class="muted" style="font-size:11px;text-transform:uppercase">${host}</div>
          <div style="font-weight:600">${(g('meta[property="og:title"]') || title).replace(/</g,"&lt;")}</div>
          <div class="muted" style="font-size:12px">${(g('meta[property="og:description"]') || desc).replace(/</g,"&lt;").slice(0,140)}</div>
        </div>
      </div>`;
  }
  $("sv-in").addEventListener("input", render);
  $("sv-url").addEventListener("input", render);
  $("sv-go").onclick = async () => {
    const u = $("sv-url").value.trim(); $("sv-err").textContent = "";
    try {
      const html = await fetch(u).then(r => { if (!r.ok) throw 0; return r.text(); });
      const head = html.match(/<head[\s\S]*?<\/head>/i);
      $("sv-in").value = head ? head[0] : html.slice(0, 8000);
      render();
    } catch { $("sv-err").textContent = "fetch failed (CORS?) — paste the page <head> manually"; }
  };
  $("sv-in").value = '<head><title>trendscope — daily trend radar for builders</title><meta name="description" content="One page that watches HN, GitHub, Product Hunt, dev.to, Lobsters, npm, PyPI and 8 more — and keeps a permanent, queryable archive."><meta property="og:title" content="trendscope"><meta property="og:image" content="https://trendscope--plov6nur.preview.devinapps.com/og.jpg"></head>';
  $("sv-url").value = "https://trendscope--plov6nur.preview.devinapps.com/";
  render();
})();

const t0 = params.get("t") || location.hash.slice(1);
tools.forEach(t => {
  const active = t === (tools.includes(t0) ? t0 : "qr");
  document.getElementById("p-"+t).classList.toggle("active", active);
  tabs.querySelector(`[data-tool=${t}]`).classList.toggle("active", active);
});
tabs.onclick = e => {
  const t = e.target?.dataset?.tool; if (!t) return;
  tools.forEach(x => {
    document.getElementById("p-"+x).classList.toggle("active", x===t);
    tabs.querySelector(`[data-tool=${x}]`).classList.toggle("active", x===t);
  });
  history.replaceState(null,"","#"+t);
};
addEventListener("hashchange", () => {
  const t = location.hash.slice(1);
  if (tools.includes(t)) tabs.querySelector(`[data-tool=${t}]`)?.click();
});

/* ---------- QR ---------- */
function qr() {
  $("qr-err").textContent = ""; $("qr-box").innerHTML = ""; $("qr-dl").innerHTML = "";
  const txt = $("qr-in").value.trim();
  if (!txt) return;
  if (typeof QRCode === "undefined") {
    $("qr-err").textContent = "QR library failed to load (offline?) — everything else on this page still works.";
    return;
  }
  try {
    const size = +$("qr-size").value, ecc = QRCode.CorrectLevel[$("qr-ecc").value];
    const q = new QRCode($("qr-box"), { text: txt, width: size, height: size, correctLevel: ecc });
    // qrcodejs appends an <img> (table) or <canvas>; normalise to a downloadable PNG
    setTimeout(() => {
      const cv = $("qr-box").querySelector("canvas");
      const img = $("qr-box").querySelector("img");
      let url = null;
      if (cv) url = cv.toDataURL("image/png");
      else if (img && img.src.startsWith("data:")) url = img.src;
      if (url) {
        const a = document.createElement("a");
        a.href = url; a.download = "qr.png"; a.textContent = "⤓ download PNG";
        a.style.cssText = "display:inline-block;margin-top:8px;color:var(--accent);font-size:13px";
        $("qr-dl").appendChild(a);
      }
    }, 60);
  } catch (e) { $("qr-err").textContent = "✕ " + e.message; }
}
["qr-in","qr-size","qr-ecc"].forEach(id => $(id).oninput = qr);
qr();

/* ---------- OG card ---------- */
const escAttr = s => s.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;");
function og() {
  const t=$("og-t").value.trim(), d=$("og-d").value.trim(), u=$("og-u").value.trim(), i=$("og-i").value.trim();
  let host = ""; try { host = new URL(u).hostname; } catch {}
  $("og-card-dom").textContent = host || "example.com";
  $("og-card-t").textContent = t || "(no title)";
  $("og-card-d").textContent = d;
  const im = $("og-card-img");
  if (i) { im.style.background = `#ced0d4 center/cover no-repeat url('${CSS.escape ? i.replace(/'/g,"\\'") : i}')`; im.textContent=""; }
  else { im.style.background = "#ced0d4"; im.textContent = "no image set"; }
  $("og-out").textContent =
`<meta property="og:title" content="${escAttr(t)}">
<meta property="og:description" content="${escAttr(d)}">
<meta property="og:url" content="${escAttr(u)}">
<meta property="og:image" content="${escAttr(i)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${escAttr(t)}">
<meta name="twitter:description" content="${escAttr(d)}">
<meta name="twitter:image" content="${escAttr(i)}">`;
}
["og-t","og-d","og-u","og-i"].forEach(id => $(id).oninput = og);
$("og-copy").onclick = () => { navigator.clipboard?.writeText($("og-out").textContent); $("og-copy").textContent="copied"; setTimeout(()=>$("og-copy").textContent="copy meta tags",1200); };
og();

/* ---------- robots.txt ---------- */
function robots() {
  const lines = [];
  if ($("rb-all").checked) {
    lines.push("User-agent: *");
    const dis = $("rb-dis").value.split("\n").map(s=>s.trim()).filter(Boolean);
    lines.push(dis.length ? dis.map(p=>"Disallow: "+p).join("\n") : "Disallow:");
  }
  for (const row of $("rb-extra").value.split("\n")) {
    const m = row.match(/^\s*([A-Za-z0-9_-]+)\s*:\s*(.+)$/);
    if (m) lines.push("", `User-agent: ${m[1]}`, `Disallow: ${m[2].trim()}`);
  }
  const sm = $("rb-map").value.trim();
  if (sm) lines.push("", "Sitemap: " + sm);
  $("rb-out").textContent = lines.join("\n") + "\n";
}
["rb-all","rb-dis","rb-map","rb-extra"].forEach(id => $(id).oninput = robots);
$("rb-copy").onclick = () => { navigator.clipboard?.writeText($("rb-out").textContent); $("rb-copy").textContent="copied"; setTimeout(()=>$("rb-copy").textContent="copy robots.txt",1200); };
robots();

/* ---------- typosquat ---------- */
const HOMO = {l:"1",o:"0",e:"3",s:"5",i:"1",t:"7",g:"9",a:"4"};
const HOMO_SEQ = [["rn","m"],["vv","w"],["cl","d"],["nn","m"]];
const TLDS = ["com","net","io","co","dev","app","org"];
function squat() {
  const raw = $("sq-in").value.trim().toLowerCase().replace(/^https?:\/\//,"").replace(/\/.*$/,"");
  const out = $("sq-out"); out.innerHTML = "";
  if (!raw || !raw.includes(".")) { out.textContent = "enter a domain like example.com"; return; }
  const parts = raw.split("."), name = parts[0], tld = parts.slice(1).join(".");
  const seen = new Set(), cands = [];
  const add = (d, why) => { if (d !== raw && !seen.has(d)) { seen.add(d); cands.push({d, why}); } };
  // omissions / doubles / swaps / substitutions
  for (let i = 0; i < name.length; i++) {
    add(name.slice(0,i) + name.slice(i+1) + "." + tld, "missing letter");
    add(name.slice(0,i) + name[i] + name.slice(i) + "." + tld, "doubled letter");
    if (i < name.length-1)
      add(name.slice(0,i) + name[i+1] + name[i] + name.slice(i+2) + "." + tld, "swapped letters");
    const sub = HOMO[name[i]];
    if (sub) add(name.slice(0,i) + sub + name.slice(i+1) + "." + tld, "character substitution");
  }
  for (const [seq, repl] of HOMO_SEQ)
    if (name.includes(seq)) add(name.replace(seq, repl) + "." + tld, "letter-pair lookalike");
  if (name.length > 2) add(name.slice(0, -1) + "-" + name.slice(-1) + "." + tld, "hyphen insertion");
  for (const t of TLDS) if (t !== tld) add(name + "." + t, "different TLD");
  const rows = cands.slice(0, 40).map(c => {
    const span = document.createElement("span");
    span.innerHTML = `<a href="https://who.is/whois/${c.d}" target="_blank" rel="noopener">${c.d}</a> <span style="color:var(--dim)">— ${c.why}</span>`;
    return span;
  });
  out.textContent = `${cands.length} candidates (showing ${rows.length}) — click to check whois:\n`;
  rows.forEach(r => { out.appendChild(r); out.appendChild(document.createTextNode("\n")); });
}
$("sq-in").oninput = squat;
squat();

/* --- HTTP status codes --- */
const HTTP = [
[100,"Continue","the server received the request headers; client may send the body"],
[101,"Switching Protocols","server agrees to switch protocols (e.g. HTTP/1.1 → WebSocket)"],
[102,"Processing","WebDAV: request received, still being processed"],
[103,"Early Hints","preload hints sent before the final response"],
[200,"OK","request succeeded"],
[201,"Created","request succeeded and a resource was created"],
[202,"Accepted","request received but not yet acted on"],
[203,"Non-Authoritative Information","response modified by a transforming proxy"],
[204,"No Content","success, no body to send"],
[205,"Reset Content","success — client should reset the document view"],
[206,"Partial Content","response to a Range request"],
[207,"Multi-Status","WebDAV: multiple statuses for multiple sub-requests"],
[208,"Already Reported","WebDAV: members already enumerated"],
[226,"IM Used","response is a delta-encoding result (instance manipulation)"],
[300,"Multiple Choices","several possible representations; client should choose"],
[301,"Moved Permanently","resource permanently moved — update bookmarks/links"],
[302,"Found","temporary redirect; historically misused like 303"],
[303,"See Other","redirect to another resource with a GET"],
[304,"Not Modified","cache hit — conditional request, nothing changed"],
[305,"Use Proxy","deprecated — must access resource via the given proxy"],
[307,"Temporary Redirect","same method + body, different URI temporarily"],
[308,"Permanent Redirect","same method + body, resource permanently moved"],
[400,"Bad Request","server can't understand the request (syntax)"],
[401,"Unauthorized","authentication required or failed"],
[402,"Payment Required","reserved; rarely used"],
[403,"Forbidden","authenticated or not, server refuses"],
[404,"Not Found","no resource at that URI"],
[405,"Method Not Allowed","method unsupported for this resource"],
[406,"Not Acceptable","no representation matching Accept headers"],
[407,"Proxy Authentication Required","auth required by the proxy"],
[408,"Request Timeout","server timed out waiting for the request"],
[409,"Conflict","request conflicts with current state (e.g. version clash)"],
[410,"Gone","resource permanently deleted, no forwarding address"],
[411,"Length Required","Content-Length header missing"],
[412,"Precondition Failed","If-* conditional header failed"],
[413,"Payload Too Large","request body exceeds server limits"],
[414,"URI Too Long","request-target too long"],
[415,"Unsupported Media Type","Content-Type not accepted"],
[416,"Range Not Satisfiable","requested byte range can't be served"],
[417,"Expectation Failed","Expect header can't be met"],
[418,"I'm a teapot","RFC 2324 joke, kept as an Easter egg"],
[421,"Misdirected Request","request sent to a server that can't produce a response"],
[422,"Unprocessable Content","well-formed but semantically invalid (validation errors)"],
[423,"Locked","WebDAV: resource is locked"],
[424,"Failed Dependency","WebDAV: a previous request failed"],
[425,"Too Early","replayable request rejected (0-RTT protection)"],
[426,"Upgrade Required","client must switch protocols"],
[428,"Precondition Required","server requires a conditional request (lost-update prevention)"],
[429,"Too Many Requests","rate limiting — slow down"],
[431,"Request Header Fields Too Large","headers exceed server limits"],
[451,"Unavailable For Legal Reasons","content blocked for legal demands (ref. Fahrenheit 451)"],
[500,"Internal Server Error","generic server-side failure"],
[501,"Not Implemented","server doesn't support the functionality"],
[502,"Bad Gateway","gateway/proxy got an invalid upstream response"],
[503,"Service Unavailable","server overloaded or down for maintenance"],
[504,"Gateway Timeout","upstream didn't respond in time"],
[505,"HTTP Version Not Supported","request HTTP version rejected"],
[506,"Variant Also Negotiates","transparent content negotiation misconfiguration"],
[507,"Insufficient Storage","WebDAV: server can't store the representation"],
[508,"Loop Detected","WebDAV: infinite loop in a Depth request"],
[510,"Not Extended","request needs further extensions"],
[511,"Network Authentication Required","captive portal intercepts the request"],
];
const HT_CLS = {1:"#58a6ff",2:"#3fb950",3:"#d29922",4:"#f85149",5:"#da3633"};
function htRender() {
  const q = $("ht-in").value.trim().toLowerCase();
  const terms = q.split(/\s+/).filter(Boolean);
  const rows = HTTP.filter(([c,n,d]) => !terms.length ||
    terms.every(t => String(c).startsWith(t) || (n+" "+d).toLowerCase().includes(t)));
  $("ht-out").innerHTML = rows.map(([c,n,d]) =>
    `<div style="display:flex;gap:10px;align-items:baseline;padding:5px 0;border-bottom:1px solid var(--line)">
      <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/${c}" target="_blank" rel="noopener"
         style="font-weight:700;min-width:44px;color:${HT_CLS[String(c)[0]]}">${c}</a>
      <span style="min-width:180px">${n}</span>
      <span style="color:var(--dim);font-size:13px">${d}</span></div>`).join("")
    || `<span class="err">no matching status codes</span>`;
}
$("ht-in").oninput = htRender;
htRender();

// ---- file checksum ----
async function hsGo(file) {
  if (!file) return;
  $("hs-out").innerHTML = `<span class="err">hashing ${escAttr(file.name)}…</span>`;
  const buf = await file.arrayBuffer();
  const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2,"0")).join("");
  const [s256, s1] = await Promise.all([
    crypto.subtle.digest("SHA-256", buf), crypto.subtle.digest("SHA-1", buf)]);
  $("hs-out").innerHTML =
    `<div style="margin-bottom:6px"><b>${escAttr(file.name)}</b> <span style="color:var(--dim)">${file.size.toLocaleString()} bytes</span></div>` +
    `<div style="font-family:monospace;font-size:12px;word-break:break-all;margin:4px 0"><b>SHA-256</b> ${hex(s256)}</div>` +
    `<div style="font-family:monospace;font-size:12px;word-break:break-all"><b>SHA-1&nbsp;&nbsp;&nbsp;</b> ${hex(s1)}</div>`;
}
$("hs-in").onchange = e => hsGo(e.target.files[0]);
const drop = $("hs-drop");
drop.ondragover = e => { e.preventDefault(); drop.style.borderColor = "var(--accent)"; };
drop.ondragleave = () => drop.style.borderColor = "";
drop.ondrop = e => { e.preventDefault(); drop.style.borderColor = ""; hsGo(e.dataTransfer.files[0]); };

// px <-> rem
function pxTable() {
  const b = parseFloat(document.getElementById("base").value) || 16;
  const vals = [8,10,12,13,14,16,18,20,24,28,32,40,48,56,64,80,96,120,160,200,240,320,480,768,1024];
  document.getElementById("pr-table").innerHTML =
    `<table style="width:100%;border-collapse:collapse;font-size:13px"><tr style="color:var(--dim)"><td>px</td><td>rem</td><td>px</td><td>rem</td></tr>` +
    vals.reduce((acc,v,i)=>{ if(i%2===0) acc.push([]); acc[acc.length-1].push(v); return acc;},[])
      .map(pair => `<tr>${pair.map(v => `<td style="padding:3px 6px;border-top:1px solid var(--border)">${v}</td><td style="padding:3px 6px;border-top:1px solid var(--border)">${(v/b).toFixed(3).replace(/0+$/,"").replace(/\.$/,"")}</td>`).join("")}${pair.length<2?'<td></td><td></td>':''}</tr>`).join("") +
    `</table>`;
}
function pxGo(from) {
  const b = parseFloat(document.getElementById("base").value) || 16;
  const px = document.getElementById("px"), rm = document.getElementById("rm");
  if (from === "px" && px.value !== "") rm.value = (parseFloat(px.value) / b).toFixed(4);
  else if (from === "rm" && rm.value !== "") px.value = (parseFloat(rm.value) * b).toFixed(2);
  pxTable();
}
["px","rm","base"].forEach(id => document.getElementById(id).addEventListener("input", () => pxGo(id)));
pxTable();

/* ---------- AI bots checker ---------- */
const AI_BOTS = [["GPTBot","OpenAI"],["ChatGPT-User","OpenAI"],["OAI-SearchBot","OpenAI"],["ClaudeBot","Anthropic"],["Claude-User","Anthropic"],["PerplexityBot","Perplexity"],["Perplexity-User","Perplexity"],["Google-Extended","Google AI"],["CCBot","Common Crawl"],["Bytespider","ByteDance"],["Amazonbot","Amazon"],["meta-externalagent","Meta"],["Applebot-Extended","Apple"],["cohere-ai","Cohere"],["Diffbot","Diffbot"]];
function aibots() {
  const lines = $("ab-in").value.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#"));
  // group rules: user-agent -> [rules]
  const groups = []; let cur = null;
  for (const l of lines) {
    const m = l.match(/^user-agent:\s*(.+)$/i);
    if (m) { cur = { agents: m[1].split(",").map(a => a.trim().toLowerCase()), rules: [] }; groups.push(cur); continue; }
    if (cur) { const r = l.match(/^(disallow|allow):\s*(.*)$/i); if (r) cur.rules.push([r[1].toLowerCase(), r[2].trim()]); }
  }
  const verdict = bot => {
    const lb = bot.toLowerCase();
    let specific = null, star = null;
    for (const g of groups) {
      if (g.agents.includes(lb)) specific = g;
      if (g.agents.includes("*")) star = g;
    }
    const g = specific || star;
    if (!g) return ["allow", "no robots rules at all"];
    // apply longest-match on "/" path: any "Disallow: /" (whole-site) blocks;
    // explicit empty Disallow or Allow wins per most specific rule
    const exact = g.rules.filter(([k, p]) => p === "/");
    const hasDisAll = exact.some(([k]) => k === "disallow");
    const hasAllowAll = exact.some(([k]) => k === "allow");
    if (hasDisAll && !hasAllowAll) return ["block", specific ? `own rule: Disallow: /` : `wildcard: Disallow: /`];
    if (g.rules.some(([k, p]) => k === "disallow" && p && p !== "/"))
      return ["partial", (specific ? "own" : "wildcard") + " rules — some paths blocked"];
    return ["allow", specific ? "own rule — no block" : "wildcard — no block"];
  };
  $("ab-out").innerHTML = lines.length
    ? `<table class="tbl"><tr><th>bot</th><th>org</th><th>verdict</th><th>why</th></tr>` +
      AI_BOTS.map(([b, o]) => {
        const [v, why] = verdict(b);
        const col = v === "allow" ? "var(--green)" : v === "block" ? "var(--red)" : "#e3b341";
        return `<tr><td><b>${b}</b></td><td>${o}</td><td style="color:${col};font-weight:600">${v.toUpperCase()}</td><td style="color:var(--dim)">${why}</td></tr>`;
      }).join("") + `</table>
      <p class="hint" style="margin-top:8px">15 AI crawlers · BLOCK means the bot should not read your site at all. Generate fixes with the <a href="?t=robots" style="color:var(--accent)">robots.txt builder</a> above.</p>`
    : `<span style="color:var(--dim)">paste a robots.txt above</span>`;
}
$("ab-in").oninput = aibots;
$("ab-in").value = "User-agent: *\nDisallow: /private/\n\nUser-agent: GPTBot\nDisallow: /\n\nUser-agent: ClaudeBot\nAllow: /";
aibots();

// ---- feed finder ----
(function(){
  const esc2 = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
  const COMMON = ["/feed", "/feed/", "/rss", "/rss.xml", "/feed.xml", "/atom.xml",
                  "/index.xml", "/feed.json", "/blog/feed", "/blog/rss", "/?feed=rss2"];
  function abs(href, base){
    try { return base ? new URL(href, base).href : href; } catch { return href; }
  }
  function run(){
    const base = $("fd-base").value.trim();
    const html = $("fd-in").value;
    const out = $("fd-out");
    if (!html.trim() && !base) { out.innerHTML = '<span style="color:var(--dim)">paste a URL and/or page source</span>'; return; }
    const found = [];
    if (html.trim()) {
      const doc = new DOMParser().parseFromString(html, "text/html");
      doc.querySelectorAll('link[rel="alternate"]').forEach(l => {
        const t = (l.getAttribute("type")||"").toLowerCase();
        if (t.includes("rss") || t.includes("atom") || t.includes("json"))
          found.push({url: l.getAttribute("href"), kind: t, via: "link[rel=alternate] · " + (l.getAttribute("title")||"")});
      });
      doc.querySelectorAll('a[href]').forEach(a => {
        const h = a.getAttribute("href")||"";
        if (/\/(feed|rss|atom)(\.xml)?(\/)?(\?|$)/i.test(h) || /\.(rss|atom|xml)$/i.test(h) && /feed|rss|atom/i.test(h))
          found.push({url: h, kind: "guessed", via: "<a> href pattern"});
      });
    }
    const baseOk = base && /^https?:\/\//.test(base);
    if (baseOk) COMMON.forEach(p => found.push({url: p, kind: "candidate", via: "well-known path guess"}));
    const seen = new Set();
    const list = found.map(f => ({...f, url: abs(f.url, base)}))
      .filter(f => f.url && !seen.has(f.url) && seen.add(f.url));
    out.innerHTML = !list.length
      ? '<span style="color:var(--dim)">no feeds found — try the well-known guesses or check for a "/feed" link in the footer</span>'
      : `<div style="font-size:12px;color:var(--dim);margin-bottom:6px">${list.length} candidate${list.length>1?"s":""} (link tags = declared, rest = guesses to try)</div>` +
        list.map(f => `<div style="padding:4px 0;border-bottom:1px solid var(--border);display:flex;gap:8px;align-items:baseline">
          <a href="${esc2(f.url)}" target="_blank" rel="noopener" style="word-break:break-all">${esc2(f.url)}</a>
          <span style="color:${f.kind==="candidate"?"var(--dim)":"var(--green)"};font-size:11px;margin-left:auto;white-space:nowrap">${esc2(f.kind)}${f.via?" · "+esc2(f.via):""}</span></div>`).join("");
  }
  $("fd-in").oninput = run; $("fd-base").oninput = run;
  $("fd-base").value = "https://simonwillison.net";
  $("fd-in").value = '<head><link rel="alternate" type="application/atom+xml" title="Simon Willison" href="/atom/everything/"><link rel="search" type="application/opensearchdescription+xml" title="trendscope" href="../opensearch.xml"><link rel="alternate" type="application/rss+xml" href="/rss/"></head>';
  run();
})();

/* ---------- shields badge builder ---------- */
(function(){
  const ids = ["bd-label","bd-msg","bd-color","bd-style","bd-logo","bd-link"];
  const o = $("bd-out"); if(!o || !$(ids[0])) return;
  const escSeg = t => encodeURIComponent(t.trim().replace(/-/g,"--").replace(/_/g,"__").replace(/\s/g,"_"));
  const row = (k, txt) => `<div style="display:flex;gap:8px;align-items:baseline;margin:4px 0">
    <span style="color:var(--dim);font-size:12px;width:78px;flex-shrink:0">${k}</span>
    <code style="flex:1;font-size:12px;word-break:break-all;background:var(--bg);padding:4px 6px;border-radius:6px;border:1px solid var(--border)">${txt.replace(/</g,"&lt;")}</code>
    <button class="bd-cp" data-t="${txt.replace(/"/g,"&quot;")}" style="padding:2px 8px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--fg);cursor:pointer;font-size:11px">copy</button></div>`;
  function go(){
    const label = $("bd-label").value, msg = $("bd-msg").value;
    if(!label.trim() && !msg.trim()){ o.innerHTML=""; return; }
    const color = ($("bd-color").value||"brightgreen").trim().replace(/^#/,"");
    const style = $("bd-style").value, logo = $("bd-logo").value.trim(), link = $("bd-link").value.trim();
    let url = `https://img.shields.io/badge/${escSeg(label)||"-"}-${escSeg(msg)||"-"}-${escSeg(color)}?style=${style}`;
    if(logo) url += `&logo=${encodeURIComponent(logo)}&logoColor=white`;
    const alt = (label.trim()+" "+msg.trim()).trim() || "badge";
    const md = link ? `[![${alt}](${url})](${link})` : `![${alt}](${url})`;
    const html = link ? `<a href="${link}"><img src="${url}" alt="${alt}"></a>` : `<img src="${url}" alt="${alt}">`;
    o.innerHTML = `<div style="padding:10px 0"><img src="${url}" alt="${alt}"></div>` +
      row("url", url) + row("markdown", md) + row("html", html);
    o.querySelectorAll(".bd-cp").forEach(b => b.onclick = () => {
      navigator.clipboard?.writeText(b.dataset.t).then(() => { b.textContent="✓"; setTimeout(()=>b.textContent="copy",1200); });
    });
  }
  ids.forEach(id => { const el=$(id); el.oninput = go; el.onchange = go; });
  go();
})();
/* ---------- og image sizer ---------- */
(function(){
  const cv = $("ogimg-cv"), ctx = cv.getContext("2d");
  function draw(img){
    const sw = img.width, sh = img.height, TW = 1200, TH = 630;
    const scale = Math.max(TW/sw, TH/sh);
    const dw = sw*scale, dh = sh*scale;
    ctx.fillStyle = "#0d1117"; ctx.fillRect(0,0,TW,TH);
    ctx.drawImage(img, (TW-dw)/2, (TH-dh)/2, dw, dh);
    cv.style.display = "block"; $("ogimg-dl").style.display = "inline-block";
    $("ogimg-info").textContent = `${sw}×${sh} → 1200×630 (center crop)`;
  }
  function load(file){
    if (!file || !file.type.startsWith("image/")) return;
    const img = new Image();
    img.onload = () => { draw(img); URL.revokeObjectURL(img.src); };
    img.src = URL.createObjectURL(file);
  }
  $("ogimg-file").addEventListener("change", e => load(e.target.files[0]));
  const dz = $("ogimg-drop");
  ["dragover","dragenter"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.style.borderColor="var(--accent)";}));
  ["dragleave","drop"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.style.borderColor="var(--border)";}));
  dz.addEventListener("drop", e => load(e.dataTransfer.files[0]));
  $("ogimg-dl").onclick = () => {
    const a = document.createElement("a");
    a.href = cv.toDataURL("image/png"); a.download = "og.png"; a.click();
  };
})();

/* ---------- favicon pack ---------- */
(function () {
  const SIZES = [
    {n: "favicon-16.png", s: 16, label: "browser tab"},
    {n: "favicon-32.png", s: 32, label: "retina tab / taskbar"},
    {n: "favicon-48.png", s: 48, label: "site icon"},
    {n: "apple-touch-icon.png", s: 180, label: "iOS home screen"},
    {n: "android-chrome-192.png", s: 192, label: "Android"},
    {n: "android-chrome-512.png", s: 512, label: "Android splash"},
  ];
  function render(img) {
    const out = $("fav-out");
    out.innerHTML = "";
    const head = document.createElement("div");
    head.style.margin = "8px 0";
    head.innerHTML = `<div class="muted" style="font-size:12px;margin-bottom:6px">${img.naturalWidth}×${img.naturalHeight} → ${SIZES.length} files</div>`;
    out.appendChild(head);
    for (const f of SIZES) {
      const c = document.createElement("canvas");
      c.width = c.height = f.s;
      const cx = c.getContext("2d");
      cx.imageSmoothingQuality = "high";
      const sc = Math.max(f.s / img.naturalWidth, f.s / img.naturalHeight);
      const w = img.naturalWidth * sc, h = img.naturalHeight * sc;
      cx.drawImage(img, (f.s - w) / 2, (f.s - h) / 2, w, h);
      const url = c.toDataURL("image/png");
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:10px;margin:4px 0";
      const prv = document.createElement("img");
      prv.src = url; prv.width = Math.min(32, f.s); prv.height = Math.min(32, f.s);
      prv.style.cssText = "image-rendering:pixelated;border:1px solid var(--border);border-radius:4px";
      const a = document.createElement("a");
      a.href = url; a.download = f.n; a.textContent = `↓ ${f.n} (${f.s}×${f.s})`;
      const lab = document.createElement("span");
      lab.className = "muted"; lab.style.fontSize = "12px"; lab.textContent = f.label;
      row.append(prv, a, lab);
      out.appendChild(row);
    }
    const manifest = JSON.stringify({icons: [{src: "/android-chrome-192.png", sizes: "192x192", type: "image/png"},
      {src: "/android-chrome-512.png", sizes: "512x512", type: "image/png"}]}, null, 2);
    const mrow = document.createElement("div");
    mrow.style.marginTop = "10px";
    const btn = document.createElement("button");
    btn.className = "copy"; btn.textContent = "copy manifest icons";
    btn.onclick = () => navigator.clipboard?.writeText(manifest).then(() => { btn.textContent = "copied"; setTimeout(() => btn.textContent = "copy manifest icons", 1200); });
    mrow.appendChild(btn);
    out.appendChild(mrow);
    $("fav-err").textContent = "";
  }
  function load(f) {
    if (!f) return;
    const img = new Image();
    img.onload = () => render(img);
    img.onerror = () => { $("fav-err").textContent = "✗ not an image"; };
    img.src = URL.createObjectURL(f);
  }
  $("fav-file").addEventListener("change", e => load(e.target.files[0]));
  const dz = $("fav-drop");
  dz.addEventListener("dragover", e => { e.preventDefault(); dz.style.borderColor = "var(--accent)"; });
  dz.addEventListener("dragleave", () => dz.style.borderColor = "");
  dz.addEventListener("drop", e => { e.preventDefault(); dz.style.borderColor = ""; load(e.dataTransfer.files[0]); });
})();

/* ---------- sitemap.xml generator ---------- */
(function () {
  const esc = t => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function go() {
    const lines = $("smg-in").value.split("\n").map(l => l.trim()).filter(Boolean);
    if (!lines.length) { $("smg-out").textContent = ""; $("smg-err").textContent = ""; return; }
    const bad = [], urls = [];
    for (const l of lines) {
      const [u, lm, pr] = l.split(",").map(x => x.trim());
      if (!/^https?:\/\//i.test(u)) { bad.push(u); continue; }
      let e = `  <url>\n    <loc>${esc(u)}</loc>`;
      if (lm) {
        if (/^\d{4}-\d{2}-\d{2}/.test(lm)) e += `\n    <lastmod>${lm.slice(0,10)}</lastmod>`;
        else bad.push("lastmod: " + lm);
      }
      if (pr) {
        const p = parseFloat(pr);
        if (!isNaN(p) && p >= 0 && p <= 1) e += `\n    <priority>${p.toFixed(1)}</priority>`;
        else bad.push("priority: " + pr);
      }
      urls.push(e + "\n  </url>");
    }
    $("smg-out").textContent =
      `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
      urls.join("\n") + "\n</urlset>";
    $("smg-err").textContent = bad.length ? "⚠ skipped: " + bad.join(", ") : "";
  }
  $("smg-in").addEventListener("input", go);
  $("smg-copy").onclick = () => navigator.clipboard?.writeText($("smg-out").textContent).then(() => { $("smg-copy").textContent = "copied"; setTimeout(() => $("smg-copy").textContent = "copy xml", 1200); });
  $("smg-in").value = "https://trendscope--plov6nur.preview.devinapps.com/\nhttps://trendscope--plov6nur.preview.devinapps.com/index.html, 2026-11-15, 0.8\nnot-a-url";
  go();
})();

/* ---------- llms.txt generator ---------- */
(function () {
  function go() {
    const name = $("lt-name").value.trim(), desc = $("lt-desc").value.trim();
    const lines = $("lt-links").value.split("\n").map(l => l.trim()).filter(Boolean);
    if (!name && !desc && !lines.length) { $("lt-out").textContent = ""; $("lt-err").textContent = ""; return; }
    const bad = [], links = [];
    for (const l of lines) {
      const [t, u, note] = l.split("|").map(x => x.trim());
      if (!t || !u) { bad.push(l.slice(0, 40)); continue; }
      links.push(`- [${t}](${u})${note ? ": " + note : ""}`);
    }
    let out = `# ${name || "Site name"}\n\n` +
      `> ${desc || "One-paragraph description."}\n\n`;
    if (links.length) out += `## Links\n\n${links.join("\n")}\n`;
    if (bad.length) $("lt-err").textContent = "⚠ skipped lines: " + bad.join(" · "); else $("lt-err").textContent = "";
    $("lt-out").textContent = out;
  }
  for (const id of ["lt-name","lt-desc","lt-links"]) $(id).addEventListener("input", go);
  $("lt-copy").onclick = () => navigator.clipboard?.writeText($("lt-out").textContent).then(() => { $("lt-copy").textContent = "copied"; setTimeout(() => $("lt-copy").textContent = "copy llms.txt", 1200); });
  $("lt-name").value = "trendscope"; $("lt-desc").value = "Daily cross-source trend snapshots for builders.";
  $("lt-links").value = "API | https://trendscope--plov6nur.preview.devinapps.com/api.html | 16 JSON endpoints\nllms.txt | https://trendscope--plov6nur.preview.devinapps.com/llms.txt";
  go();
})();
