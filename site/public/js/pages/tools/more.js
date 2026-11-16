const TOOLS = [
  {id:"diff", label:"Text diff"},
  {id:"md",   label:"Markdown preview"},
  {id:"mdtable", label:"MD table"},
  {id:"uni", label:"Unicode"},
  {id:"aitext", label:"AI-text tells"},
  {id:"toc", label:"MD TOC"},
  {id:"html2md", label:"HTML→MD"},
];
const tabsEl = document.getElementById("tabs");
tabsEl.innerHTML = TOOLS.map((t,i) =>
  `<button class="tab${i===0?" active":""}" data-t="${t.id}">${t.label}</button>`).join("");
tabsEl.addEventListener("click", ev => {
  const b = ev.target.closest(".tab"); if (!b) return;
  tabsEl.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x===b));
  document.querySelectorAll(".tool").forEach(d =>
    d.classList.toggle("active", d.dataset.tool === b.dataset.t));
  location.hash = b.dataset.t;
});
const start = new URLSearchParams(location.search).get("t") || location.hash.slice(1);
const t0 = TOOLS.some(t => t.id === start) ? start : "diff";
document.querySelectorAll(".tool").forEach(d =>
  d.classList.toggle("active", d.dataset.tool === t0));
tabsEl.querySelectorAll(".tab").forEach(x =>
  x.classList.toggle("active", x.dataset.t === t0));

// ---- Diff (jsdiff library) ----
function esc(s) { return s.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function diffGo() {
  const a = document.getElementById("diff-a").value;
  const b = document.getElementById("diff-b").value;
  const ops = [];
  for (const p of Diff.diffLines(a, b)) {
    const k = p.added ? "add" : p.removed ? "del" : "ctx";
    for (const line of p.value.replace(/\n$/, "").split("\n")) ops.push([k, line]);
  }
  const adds = ops.filter(o => o[0] === "add").length;
  const dels = ops.filter(o => o[0] === "del").length;
  document.getElementById("diff-stat").innerHTML =
    adds + dels === 0 ? `<span class="ok">identical — ${a.split("\n").length} lines</span>`
                      : `<span class="ok">+${adds}</span> / <span class="bad">−${dels}</span> lines`;
  document.getElementById("diff-out").innerHTML = ops.map(([k, line]) =>
    `<span class="diff-${k}">${k === "add" ? "+ " : k === "del" ? "− " : "  "}${esc(line) || " "}</span>`).join("");
}
function diffSwap() {
  const a = document.getElementById("diff-a"), b = document.getElementById("diff-b");
  [a.value, b.value] = [b.value, a.value]; diffGo();
}
["diff-a","diff-b"].forEach(id => document.getElementById(id).addEventListener("input", diffGo));

// ---- Markdown (minimal, escape-first) ----
function mdGo() {
  document.getElementById("md-out").innerHTML = marked.parse(document.getElementById("md-in").value, { gfm: true, breaks: false });
}
document.getElementById("md-in").addEventListener("input", mdGo);
mdGo();

/* --- Markdown table builder --- */
function mtGo() {
  const raw = document.getElementById("mt-in").value;
  const out = document.getElementById("mt-out");
  const lines = raw.trim().split("\n").filter(l => l.trim());
  if (!lines.length) { out.textContent = "paste TSV/CSV rows"; return; }
  // split on tab, else comma (outside quotes)
  const rows = Papa.parse(raw.trim(), { delimiter: "", skipEmptyLines: "greedy" }).data
    .map(r => r.map(c => String(c).trim()));
  const ncol = Math.max(...rows.map(r => r.length));
  rows.forEach(r => { while (r.length < ncol) r.push(""); });
  const w = Array.from({length: ncol}, (_, i) =>
    Math.max(3, ...rows.map(r => r[i].length)));
  const fmt = r => "| " + r.map((c, i) => c.padEnd(w[i])).join(" | ") + " |";
  const header = rows[0], sep = w.map(x => "-".repeat(x));
  out.textContent = [fmt(header), fmt(sep), ...rows.slice(1).map(fmt)].join("\n");
}
// ---- Unicode inspector ----
const UNI_BLOCKS=[[0,127,"Basic Latin"],[128,255,"Latin-1 Supplement"],[256,383,"Latin Extended-A"],[384,591,"Latin Extended-B"],[592,687,"IPA Extensions"],[880,1023,"Greek and Coptic"],[1024,1279,"Cyrillic"],[1280,1327,"Armenian"],[1424,1535,"Hebrew"],[1536,1791,"Arabic"],[3584,3711,"Thai"],[3840,4095,"Tibetan"],[4096,4255,"Georgian"],[7424,7551,"Phonetic Extensions"],[7680,7935,"Latin Extended Additional"],[8192,8303,"General Punctuation"],[8304,8351,"Super/Subscripts"],[8352,8399,"Currency Symbols"],[8448,8527,"Letterlike Symbols"],[8592,8703,"Arrows"],[8704,8959,"Math Operators"],[9312,9471,"Enclosed Alphanumerics"],[9472,9599,"Box Drawing"],[9632,9727,"Geometric Shapes"],[9728,9983,"Misc Symbols"],[9984,10175,"Dingbats"],[10240,10495,"Braille"],[11904,12031,"CJK Radicals"],[12288,12351,"CJK Punctuation"],[12352,12447,"Hiragana"],[12448,12543,"Katakana"],[19968,40959,"CJK Unified"],[44032,55215,"Hangul Syllables"],[63744,64255,"CJK Compat Ideographs"],[64256,64335,"Alphabetic Presentation"],[65072,65103,"CJK Compat Forms"],[65136,65278,"Arabic Presentation-B"],[65279,65279,"BOM/ZWNBSP"],[65536,66175,"Linear B"],[119808,120831,"Math Alphanumeric"],[126976,127023,"Mahjong/Domino"],[127024,127151,"Enclosed Alphanum Suppl"],[127744,128511,"Misc Symbols+Pictographs"],[128512,128591,"Emoticons"],[128592,128639,"Transport+Map"],[128640,128767,"Transport+Map Suppl"],[129024,129279,"Suppl Arrows-C"],[131072,173791,"CJK Ext B"],[917760,917999,"Tags"]];
function uniBlock(cp){for(const b of UNI_BLOCKS)if(cp>=b[0]&&cp<=b[1])return b[2];return "Unassigned/Private";}
function uniCat(ch){for(const[re,n]of[[/\p{Lu}/u,"uppercase letter"],[/\p{Ll}/u,"lowercase letter"],[/\p{Lt}/u,"titlecase letter"],[/\p{Lm}/u,"modifier letter"],[/\p{Lo}/u,"other letter"],[/\p{Nd}/u,"decimal digit"],[/\p{N}/u,"number"],[/\p{P}/u,"punctuation"],[/\p{M}/u,"mark"],[/\p{Sm}/u,"math symbol"],[/\p{Sc}/u,"currency symbol"],[/\p{Sk}/u,"modifier symbol"],[/\p{So}/u,"other symbol"],[/\p{Zs}/u,"space"],[/\p{Cc}/u,"control"],[/\p{Cf}/u,"format (invisible)"],[/\p{Co}/u,"private use"],[/\p{S}/u,"symbol"],[/\p{Z}/u,"separator"]])if(re.test(ch))return n;return "?";}
function uniInspect(){
  const t=document.getElementById("uni-in").value,out=document.getElementById("uni-out");
  if(!t){out.textContent="";return;}
  const enc=new TextEncoder(),rows=[["char","codepoint","UTF-8","UTF-16","block","category"]];
  let i=0;
  for(const ch of t){
    const cp=ch.codePointAt(0);
    const hex="U+"+cp.toString(16).toUpperCase().padStart(cp>0xFFFF?6:4,"0");
    const u8=[...enc.encode(ch)].map(b=>b.toString(16).toUpperCase().padStart(2,"0")).join(" ");
    const u16=[...ch].map(c=>"0x"+c.charCodeAt(0).toString(16).toUpperCase()).join(" ");
    const disp=cp<32||cp===127?["NUL","SOH","STX","ETX","EOT","ENQ","ACK","BEL","BS","TAB","LF","VT","FF","CR","SO","SI","DLE","DC1","DC2","DC3","DC4","NAK","SYN","ETB","CAN","EM","SUB","ESC","FS","GS","RS","US","DEL"][cp]:(cp===32?"␣":ch);
    rows.push([disp,hex,u8,u16,uniBlock(cp),uniCat(ch)]);
    if(++i>=500){rows.push(["…","truncated at 500 chars","","","",""]);break;}
  }
  const w=rows[0].map((_,c)=>Math.max(...rows.map(r=>r[c].length)));
  out.textContent=rows.map(r=>r.map((c,j)=>c.padEnd(w[j])).join("  ")).join("\n");
}
document.getElementById("uni-in").addEventListener("input",uniInspect);
// ---- AI-text tells ----
const AI_WORDS=["delve","leverage","tapestry","realm","bustling","testament","crucial","pivotal","vibrant","furthermore","moreover","notably","landscape","nuanced","elevate","unleash","embark","journey","streamline","robust","seamless","comprehensive","cutting-edge","game-changer","harness","foster","underscore","paramount","myriad","plethora","meticulous","intricate","resonate","beacon","transformative","synergy","holistic","profound","endeavor","facilitate","navigate the","rich tapestry","ever-evolving","fast-paced"];
const AI_PHRASES=["it's important to note","it is important to note","it's worth noting","in today's","in conclusion","whether you're a","whether you are a","not only","but also","first and foremost","at the end of the day","when it comes to","one thing is clear","the bottom line","in a world where","as we navigate","look no further","rest assured","in the realm of","a testament to","unlock the power","take it to the next level","dive into","deep dive","let's explore","buckle up"];
function aiInspect(){
  const t=document.getElementById("ai-in").value,out=document.getElementById("ai-out"),
        stat=document.getElementById("ai-stat"),hl=document.getElementById("ai-hl");
  if(!t.trim()){out.textContent="";stat.textContent="";hl.textContent="";return;}
  const words=t.toLowerCase().split(/\s+/),lines=[];
  let score=0;
  // 1. telltale words
  const hits=[];
  for(const w of AI_WORDS){const re=new RegExp("\\b"+w.replace(/\s/g,"\\s+")+"\\b","gi");const m=t.match(re);if(m)hits.push(w+" ×"+m.length);}
  if(hits.length){const wpts=Math.min(4,hits.length);score+=wpts;lines.push(`🔸 telltale words (+${wpts}): ${hits.slice(0,12).join(", ")}${hits.length>12?" …":""}`);}
  // 2. phrases
  const ph=AI_PHRASES.filter(x=>t.toLowerCase().includes(x));
  if(ph.length){const ppts=Math.min(3,ph.length);score+=ppts;lines.push(`🔸 formulaic phrases (+${ppts}): ${ph.slice(0,8).join(", ")}`);}
  // 3. em-dash density
  const dashes=(t.match(/[—–]/g)||[]).length,dd=dashes/Math.max(1,words.length)*100;
  if(dd>1.5){score+=2;lines.push(`🔸 em-dash density ${dd.toFixed(1)}/100w (+2) — ${dashes} dashes`);}
  else if(dd>0.7){score+=1;lines.push(`🔹 em-dash density ${dd.toFixed(1)}/100w (+1)`);}
  // 4. sentence length uniformity
  const sents=t.split(/[.!?]+/).map(x=>x.trim()).filter(x=>x.split(/\s+/).length>3);
  if(sents.length>=4){
    const lens=sents.map(x=>x.split(/\s+/).length),mean=lens.reduce((a,b)=>a+b)/lens.length;
    const sd=Math.sqrt(lens.reduce((a,b)=>a+(b-mean)**2,0)/lens.length);
    if(sd<4){score+=2;lines.push(`🔸 uniform sentences σ=${sd.toFixed(1)}w (+2) — human writing varies more`);}
    else if(sd<7){score+=1;lines.push(`🔹 fairly uniform sentences σ=${sd.toFixed(1)}w (+1)`);}
  }
  // 5. bullet/formal structure density
  const bullets=(t.match(/^\s*[-*•]\s|\d+\.\s/gm)||[]).length;
  if(bullets>=4){score+=1;lines.push(`🔹 listicle structure ${bullets} bullets (+1)`);}
  // 6. zero first-person & zero contractions (formality tells)
  const fp=(t.match(/\b(I|me|my|we|our|us)\b/g)||[]).length;
  const contr=(t.match(/\b\w+'(t|re|ll|ve|d|s|m)\b/gi)||[]).length;
  if(words.length>60&&fp===0&&contr===0){score+=1;lines.push("🔹 zero first-person & zero contractions (+1) — detached register");}
  const verdict=score>=6?"🔴 strong AI-style signals":score>=3?"🟠 mixed signals":"🟢 few AI-style tells";
  stat.textContent=`${verdict} — score ${score} · ${words.length} words`;
  out.textContent=lines.length?lines.join("\n"):"no heuristic flags";
  // highlight
  let h=t.replace(/&/g,"&amp;").replace(/</g,"&lt;");
  for(const w of AI_WORDS){h=h.replace(new RegExp("\\b("+w.replace(/\s/g,"\\s+")+")\\b","gi"),"<mark>$1</mark>");}
  for(const ph2 of AI_PHRASES){h=h.replace(new RegExp("("+ph2.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")","gi"),"<mark>$1</mark>");}
  hl.innerHTML=h.replace(/\n/g,"<br>");
}
document.getElementById("ai-in").addEventListener("input",aiInspect);
// ---- Markdown TOC ----
function ghAnchor(t){
  return t.trim().toLowerCase().replace(/[`*_~^\[\]()]/g,"")
    .replace(/[^\w\- \u4e00-\u9fff]/g,"").replace(/ /g,"-");
}
function tocGo(){
  const t=document.getElementById("toc-in").value,
        out=document.getElementById("toc-out"),
        dep=+document.getElementById("toc-depth").value||3,
        noh1=document.getElementById("toc-noh1").checked;
  const lines=t.split("\n"); let inCode=false; const hs=[];
  for(const l of lines){
    if(/^```/.test(l.trim())) inCode=!inCode;
    if(inCode) continue;
    const m=l.match(/^(#{1,6})\s+(.+)/);
    if(m && m[1].length<=dep && !(noh1 && m[1].length===1)) hs.push([m[1].length,m[2]]);
  }
  out.textContent = hs.map(([d,t])=>{
    const tt=t.replace(/\s*#+\s*$/,"");
    return "  ".repeat(Math.max(0,d-(noh1?2:1))) + `- [${tt}](#${ghAnchor(tt)})`;
  }).join("\n");
}
if(document.getElementById("toc-in")){
  ["toc-in","toc-depth","toc-noh1"].forEach(id=>
    document.getElementById(id).addEventListener("input",tocGo));
  document.getElementById("toc-copy").onclick=()=>{
    navigator.clipboard?.writeText(document.getElementById("toc-out").textContent)
      .then(()=>{const b=document.getElementById("toc-copy");b.textContent="✓";setTimeout(()=>b.textContent="copy",1200);});};
  document.getElementById("toc-in").value="# My Project\n\n## Getting started\n### Install\n### Configure\n## Usage\n## License";
  tocGo();
}

// ---- html2md ----
{
  const $ = id => document.getElementById(id);
  const tds = new TurndownService({ headingStyle: "atx", codeBlockStyle: "fenced" });
  tds.use(turndownPluginGfm.gfm);
  function go() {
    const src = $("h2m-in").value;
    try {
      $("h2m-out").textContent = tds.turndown(src) || "(no output)";
    } catch (e) { $("h2m-out").textContent = "parse error: " + e.message; }
  }
  $("h2m-in").addEventListener("input", go);
  $("h2m-copy").onclick = () => {
    navigator.clipboard?.writeText($("h2m-out").textContent)
      .then(() => { const b = $("h2m-copy"); b.textContent = "✓"; setTimeout(() => b.textContent = "copy", 1200); }); };
  $("h2m-dl").onclick = () => {
    const blob = new Blob([$("h2m-out").textContent], {type:"text/markdown"});
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = "converted.md"; a.click(); URL.revokeObjectURL(a.href); };
  $("h2m-in").value = '<h2>Example</h2><p>A <strong>bold</strong> <a href="https://x.dev">link</a> and <code>code()</code></p><ul><li>one</li><li>two</li></ul><table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>';
  go();
}
