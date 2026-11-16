const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const PAGES = "https://trendscope--plov6nur.preview.devinapps.com";
const RAW   = "https://raw.githubusercontent.com/zalize-com/trendscope/main";

const BADGES = [
  { name: "items tracked", file: "badge.json",
    blurb: "Total history rows and days tracked — a live dataset-size counter." },
  { name: "today's #1 story", file: "badge-top.json",
    blurb: "The current top item on the board. Changes every snapshot." },
  { name: "sources tracked", file: "badge-sources.json",
    blurb: "How many attention sources the pipeline currently covers." },
];

const out = document.getElementById("out");
out.innerHTML = BADGES.map(b => {
  const endpoint = `${PAGES}/docs/api/${b.file}`;
  const rawEndpoint = `${RAW}/docs/api/${b.file}`;
  const shields = `https://img.shields.io/endpoint?url=${encodeURIComponent(endpoint)}`;
  const shieldsRaw = `https://img.shields.io/endpoint?url=${encodeURIComponent(rawEndpoint)}`;
  const md = `[![${b.name}](${shields})](${PAGES})`;
  const mdRaw = `[![${b.name}](${shieldsRaw})](${PAGES})`;
  const html = `<a href="${PAGES}"><img src="${shields}" alt="${b.name}"></a>`;
  return `<div class="card">
    <h3>${esc(b.name)}</h3>
    <div class="lbl">${esc(b.blurb)}</div>
    <img src="${shieldsRaw}" alt="${esc(b.name)} badge"
         onerror="this.outerHTML='<span style=\\'color:var(--dim)\\'>badge preview unavailable</span>'">
    <div class="lbl">markdown (GitHub Pages endpoint)</div>
    <pre>${esc(md)}</pre>
    <div class="lbl">markdown (raw endpoint — works before Pages is enabled)</div>
    <pre>${esc(mdRaw)}</pre>
    <div class="lbl">endpoint JSON: <code>docs/api/${esc(b.file)}</code> · <a href="${rawEndpoint}">view</a></div>
  </div>`;
}).join("");
