const CATS = [
  { name: "Crawlability — can AI bots even reach you?", items: [
    ["robots.txt doesn't block GPTBot", 4],
    ["robots.txt doesn't block ClaudeBot", 4],
    ["robots.txt doesn't block PerplexityBot / OAI-SearchBot", 4],
    ["no CDN/WAF rule mass-blocking AI crawlers (Cloudflare 'block AI bots' off)", 4],
    ["key pages return 200 without login or JS-render requirements", 3],
  ]},
  { name: "Machine legibility — can they read what you publish?", items: [
    ["content is in server-rendered HTML, not only behind JS hydration", 5],
    ["semantic structure: real h1/h2, lists, tables (AI cites structured chunks)", 4],
    ["each page has a unique, descriptive <title> and meta description", 3],
    ["JSON-LD or microdata marks up your key entities (Product, Dataset, Article, FAQ)", 4],
    ["sitemap.xml exists and is referenced from robots.txt", 3],
  ]},
  { name: "Citability — do they have a reason to cite you?", items: [
    ["you publish original data/research nobody else has (the #1 citation magnet)", 6],
    ["stable, URL-per-entity pages (a page per product/statistic/tool, not one giant dashboard)", 4],
    ["clear author/organization identity (About, bylines, contact)", 3],
    ["content is dated and kept fresh — AI engines prefer recent", 3],
    ["third-party mentions exist (forums, docs, awesome lists, Wikipedia-adjacent)", 4],
  ]},
  { name: "AI-native surfaces — the new stuff most sites miss", items: [
    ["llms.txt exists at the domain root (the emerging standard)", 5],
    ["an RSS/Atom feed exists and is linked via autodiscovery", 2],
    ["raw data/API is downloadable — models trained on it mention you", 4],
    ["your docs/readme answer questions verbatim (question-shaped headings)", 3],
  ]},
];
const cats = document.getElementById("cats");
const boxes = [];
CATS.forEach((c, ci) => {
  const div = document.createElement("div"); div.className = "cat";
  div.innerHTML = `<h2>${ci+1}. ${c.name} <em>— ${c.items.reduce((a,i)=>a+i[1],0)} pts</em></h2>`;
  c.items.forEach(([label, w], ii) => {
    const l = document.createElement("label"); l.className = "chk";
    l.innerHTML = `<input type="checkbox" id="c${ci}_${ii}"><span>${label} <span class="w">+${w}</span></span>`;
    div.appendChild(l);
    const cb = l.querySelector("input");
    boxes.push({cb, w, label, cat: c.name});
    cb.onchange = score;
  });
  cats.appendChild(div);
});
const TOTAL = boxes.reduce((a,b)=>a+b.w,0);
function score() {
  const n = boxes.filter(b=>b.cb.checked).reduce((a,b)=>a+b.w,0);
  document.getElementById("score").textContent = n;
  document.getElementById("barfill").style.width = (n/TOTAL*100)+"%";
  const v = document.getElementById("verdict");
  v.textContent = n>=60 ? "Strong — AI engines can probably see and cite you" :
    n>=35 ? "Mixed — you're visible but leaking citations" :
    n>0 ? "Weak — likely invisible to AI answers" : "Check the boxes that are already true on your site";
  v.style.color = n>=60 ? "var(--green)" : n>=35 ? "var(--accent)" : "#f85149";
}
document.getElementById("export").onclick = () => {
  const out = document.getElementById("out");
  const missing = boxes.filter(b=>!b.cb.checked);
  let md = `# GEO audit — ${new Date().toISOString().slice(0,10)}\n\n` +
    `Score: ${boxes.reduce((a,b)=>a+(b.cb.checked?b.w:0),0)} / ${TOTAL}\n\n## To fix\n`;
  missing.forEach(b => { md += `- [ ] **${b.cat}**: ${b.label}\n`; });
  if (!missing.length) md += "- nothing — you're fully covered\n";
  out.textContent = md; out.style.display = "block";
};
score();

document.getElementById("ll-go").onclick = () => {
  const name = document.getElementById("ll-name").value.trim() || "Untitled";
  const desc = document.getElementById("ll-desc").value.trim();
  const groups = {};
  for (const line of document.getElementById("ll-links").value.split("\n")) {
    const parts = line.split("|").map(s => s.trim()).filter(Boolean);
    if (parts.length < 3) continue;
    const [sec, text, url, note] = parts;
    (groups[sec] = groups[sec] || []).push(`- [${text}](${url})${note ? `: ${note}` : ""}`);
  }
  let md = `# ${name}\n\n${desc ? `> ${desc}\n\n` : ""}`;
  for (const [sec, items] of Object.entries(groups))
    md += `## ${sec}\n\n${items.join("\n")}\n\n`;
  document.getElementById("ll-out").value = md.trim() + "\n";
};
