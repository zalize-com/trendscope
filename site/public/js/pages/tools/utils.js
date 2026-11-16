const TOOLS = [
  {id:"color", label:"Color converter"},
  {id:"text",  label:"Text inspector"},
  {id:"yaml",  label:"YAML ↔ JSON"},
  {id:"tree",  label:"Outline → tree"},
  {id:"url",   label:"URL query editor"},
  {id:"contrast", label:"Contrast checker"},
  {id:"slug",   label:"Slug generator"},
  {id:"date",   label:"Date calculator"},
  {id:"tz",     label:"Timezone converter"},
  {id:"freq",   label:"Word frequency"},
  {id:"opml",   label:"OPML → YAML"},
  {id:"opmlbundle", label:"OPML starter pack"},
  {id:"cron",   label:"Crontab explainer"},
  {id:"chmod",  label:"chmod calculator"},
  {id:"csv",    label:"CSV ↔ JSON"},
  {id:"semver", label:"semver compare"},
  {id:"pwgen",  label:"password gen"},
  {id:"case",   label:"case converter"},
  {id:"sortlines",label:"sort & dedupe lines"},
  {id:"uuid",  label:"uuid v4 generator"},
  {id:"bytes",label:"file-size converter"},
  {id:"lorem",label:"lorem ipsum generator"},
  {id:"aspect",label:"aspect ratio calc"},
  {id:"morse",label:"morse code"},
  {id:"roman",label:"roman numerals"},
  {id:"mime",  label:"mime types"},
  {id:"semver",label:"semver"},
  {id:"regex", label:"regex tester"},
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
const t0 = TOOLS.some(t => t.id === start) ? start : "color";
document.querySelectorAll(".tool").forEach(d =>
  d.classList.toggle("active", d.dataset.tool === t0));
tabsEl.querySelectorAll(".tab").forEach(x =>
  x.classList.toggle("active", x.dataset.t === t0));
function esc(s){const d=document.createElement('div');d.textContent=s||'';return d.innerHTML}

// ---- Color ----
const NAMED = {black:[0,0,0],white:[255,255,255],red:[255,0,0],green:[0,128,0],blue:[0,0,255],
  rebeccapurple:[102,51,153],orange:[255,165,0],gray:[128,128,128],grey:[128,128,128],
  yellow:[255,255,0],purple:[128,0,128],pink:[255,192,203],cyan:[0,255,255],magenta:[255,0,255]};
function rgb2hsl(r,g,b){
  r/=255;g/=255;b/=255;
  const mx=Math.max(r,g,b),mn=Math.min(r,g,b);let h=0,s=0;const l=(mx+mn)/2;
  if(mx!==mn){const d=mx-mn;s=l>.5?d/(2-mx-mn):d/(mx+mn);
    h=mx===r?((g-b)/d+(g<b?6:0)):mx===g?(b-r)/d+2:(r-g)/d+4;h*=60;}
  return [Math.round(h), Math.round(s*100), Math.round(l*100)];
}
function parseColor(s){
  s=s.trim().toLowerCase();
  let m=s.match(/^#?([0-9a-f]{6})$/); if(m){const n=parseInt(m[1],16);return [n>>16,(n>>8)&255,n&255,1]}
  m=s.match(/^#?([0-9a-f]{3})$/); if(m)return [...m[1]].map(c=>parseInt(c+c,16)).concat(1);
  m=s.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$/);
  if(m)return [+m[1],+m[2],+m[3],m[4]?+m[4]:1];
  m=s.match(/^hsla?\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*(?:,\s*([\d.]+)\s*)?\)$/);
  if(m){const h=(+m[1]%360)/360, sat=+m[2]/100, l=+m[3]/100;
    const q=l<.5?l*(1+sat):l+sat-l*sat, p=2*l-q;
    const f=t=>{t=(t%1+1)%1;
      if(t<1/6)return p+(q-p)*6*t; if(t<1/2)return q; if(t<2/3)return p+(q-p)*(2/3-t)*6; return p};
    return [Math.round(f(h+1/3)*255),Math.round(f(h)*255),Math.round(f(h-1/3)*255),m[4]?+m[4]:1];}
  if(NAMED[s])return NAMED[s].concat(1);
  return null;
}
function cGo(){
  const v=document.getElementById("c-in").value.trim();
  const out=document.getElementById("c-out"),sw=document.getElementById("c-sw");
  if(!v){sw.style.background="transparent";out.innerHTML='<span style="color:var(--dim)">type a color…</span>';return}
  const c=parseColor(v);
  if(!c){sw.style.background="transparent";out.innerHTML='<span class="err">unrecognized color</span>';return}
  const [r,g,b,a]=c, [h,s,l]=rgb2hsl(r,g,b);
  const hex="#"+[r,g,b].map(x=>x.toString(16).padStart(2,"0")).join("");
  sw.style.background=`rgba(${r},${g},${b},${a})`;
  out.innerHTML=
    `<span class="k">hex</span><span>${hex}</span>`+
    `<span class="k">rgb</span><span>rgb(${r}, ${g}, ${b})</span>`+
    (a<1?`<span class="k">rgba</span><span>rgba(${r}, ${g}, ${b}, ${a})</span>`:"")+
    `<span class="k">hsl</span><span>hsl(${h}, ${s}%, ${l}%)</span>`;
}
document.getElementById("c-in").addEventListener("input", cGo);

// ---- Text inspector ----
const WORDS = s => (s.match(/\S+/g)||[]);
function tStat(){
  const s=document.getElementById("t-in").value;
  document.getElementById("t-stat").textContent =
    `${s.length} chars · ${WORDS(s).length} words · ${s?s.split("\n").length:0} lines · ${[...s].length} codepoints`;
}
function tGo(op){
  const el=document.getElementById("t-in"); let s=el.value;
  if(op==="upper")s=s.toUpperCase();
  else if(op==="lower")s=s.toLowerCase();
  else if(op==="title")s=s.replace(/\b\w/g,c=>c.toUpperCase());
  else if(op==="camel")s=WORDS(s.toLowerCase()).map((w,i)=>i?w[0].toUpperCase()+w.slice(1):w).join("");
  else if(op==="snake"||op==="kebab"){
    const sep=op==="snake"?"_":"-";
    s=s.replace(/([a-z0-9])([A-Z])/g,"$1 $2").toLowerCase().replace(/[\s_]+/g,sep);
  }
  else if(op==="trim")s=s.split("\n").map(l=>l.trim()).join("\n");
  else if(op==="dedupe")s=[...new Set(s.split("\n"))].join("\n");
  else if(op==="sort")s=s.split("\n").sort().join("\n");
  el.value=s; tStat();
  document.getElementById("t-out").textContent=s;
}
document.getElementById("t-in").addEventListener("input",()=>{tStat();document.getElementById("t-out").textContent=document.getElementById("t-in").value});

// ---- YAML <-> JSON ----
function j2y(v, ind){
  ind = ind || "";
  if (v === null) return "null";
  if (Array.isArray(v)){
    if (!v.length) return "[]";
    return v.map(x => {
      if (x && typeof x === "object"){
        const s = j2y(x, ind + "  ");
        return ind + "-" + s.slice(ind.length);
      }
      return ind + "- " + j2y(x, ind + "  ");
    }).join("\n");
  }
  if (typeof v === "object"){
    const ks = Object.keys(v);
    if (!ks.length) return "{}";
    return ks.map(k => {
      const val = v[k];
      if (val && typeof val === "object")
        return ind + k + ":\n" + j2y(val, ind + "  ");
      return ind + k + ": " + j2y(val, ind + "  ");
    }).join("\n");
  }
  if (typeof v === "string"){
    return /^[\w .-]*$/.test(v) && v !== "" ? v : JSON.stringify(v);
  }
  return String(v);
}
function yGo(dir){
  const inp = document.getElementById("y-in").value;
  const out = document.getElementById("y-out"), st = document.getElementById("y-stat");
  try {
    if (dir === "j2y"){
      out.textContent = j2y(JSON.parse(inp));
      st.textContent = "";
    } else {
      if (window.jsyaml && window.jsyaml.load){
        out.textContent = JSON.stringify(window.jsyaml.load(inp), null, 2);
        st.textContent = "";
      } else {
        out.textContent = "";
        st.textContent = "js-yaml CDN unavailable (offline?) — YAML→JSON needs the network once.";
      }
    }
  } catch(e){
    out.textContent = "";
    st.textContent = "error: " + e.message;
  }
}
document.getElementById("y-in").addEventListener("input", () => {
  const s = document.getElementById("y-in").value.trim();
  if (s.startsWith("{") || s.startsWith("[")) yGo("j2y");
});

// ---- Outline -> tree ----
function parseOutline(src){
  const root={label:"",children:[]},stack=[root];
  for(const raw of src.split("\n")){
    if(!raw.trim())continue;
    const ind=(raw.match(/^[ \t]*/)[0].replace(/\t/g,"  ")).length;
    const lvl=Math.floor(ind/2)+1;
    const node={label:raw.trim(),children:[]};
    stack.length=Math.min(stack.length,lvl);
    stack[stack.length-1].children.push(node);
    stack.push(node);
  }
  return root.children;
}
function layoutTree(nodes){
  // tidy layout: assign each leaf a y slot, parents at midpoint
  let y=0;const pos=[];const links=[];
  function walk(n,depth,parentY){
    let my;
    if(!n.children.length){my=y++;}
    else{
      const kids=n.children.map(c=>walk(c,depth+1));
      my=(kids[0]+kids[kids.length-1])/2;
    }
    pos.push({n,x:depth,y:my});
    if(parentY!==undefined)links.push([depth-1,parentY,depth,my]);
    return my;
  }
  nodes.forEach(n=>walk(n,0,undefined));
  return {pos,links,leaves:y};
}
function trGo(){
  const src=document.getElementById("tr-in").value;
  const nodes=parseOutline(src);
  const out=document.getElementById("tr-out"),st=document.getElementById("tr-stat");
  if(!nodes.length){out.innerHTML='<span style="color:var(--dim)">paste an outline…</span>';st.textContent="";return}
  const {pos,links,leaves}=layoutTree(nodes);
  const XW=150,YH=34,LW=8,W=Math.max(...pos.map(p=>p.x))*XW+220,H=leaves*YH+20;
  const cx=p=>p.x*XW+20, cy=p=>p.y*YH+26;
  const posOf=(d,y)=>pos.find(p=>p.x===d&&Math.abs(p.y-y)<1e-6)||{x:d,y};
  let svg=`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%">`;
  for(const [d0,y0,d1,y1] of links){
    const a=posOf(d0,y0),b=posOf(d1,y1);
    const x0=cx(a)+140,y0c=cy(a)+8,x1=cx(b),y1c=cy(b)+8;
    svg+=`<path d="M ${x0} ${y0c} C ${x0+40} ${y0c}, ${x1-40} ${y1c}, ${x1} ${y1c}" fill="none" stroke="var(--border)" stroke-width="1.5"/>`;
  }
  for(const p of pos){
    const x=cx(p),y=cy(p);
    svg+=`<rect x="${x}" y="${y-8}" rx="6" ry="6" width="140" height="24" fill="var(--panel)" stroke="var(--border)"/>`
       +`<text x="${x+8}" y="${y+8}" font-size="12" fill="var(--fg)">${esc(p.n.label.length>18?p.n.label.slice(0,17)+"…":p.n.label)}</text>`;
  }
  svg+="</svg>";
  out.innerHTML=svg;
  st.textContent=`${pos.length} nodes · ${leaves} leaves`;
}
document.getElementById("tr-in").addEventListener("input",trGo);

// ---- URL editor ----
function uGo(){
  const v=document.getElementById("u-in").value.trim();
  const parts=document.getElementById("u-parts"), pp=document.getElementById("u-params"), out=document.getElementById("u-out");
  let u; try{u=new URL(v)}catch(e){
    parts.innerHTML='<span class="err">not a valid URL</span>';pp.textContent="";out.textContent="";return}
  parts.innerHTML=
    `<span class="k">protocol</span><span>${esc(u.protocol)}</span>`+
    `<span class="k">host</span><span>${esc(u.host)}</span>`+
    `<span class="k">pathname</span><span>${esc(u.pathname)}</span>`+
    (u.hash?`<span class="k">hash</span><span>${esc(u.hash)}</span>`:"");
  const rows=[...u.searchParams.entries()];
  pp.innerHTML = rows.length
    ? '<table class="params">'+rows.map(([k,val],i)=>
      `<tr><td>${esc(k)}</td><td><input data-k="${esc(k)}" value="${esc(val)}"></td></tr>`).join("")+'</table>'
    : '<span style="color:var(--dim)">no query params</span>';
  pp.querySelectorAll("input").forEach(inp=>inp.addEventListener("input",()=>{
    u.searchParams.set(inp.dataset.k, inp.value); out.textContent=u.toString();
  }));
  out.textContent=u.toString();
}
document.getElementById("u-in").addEventListener("input", uGo);

// ---- Contrast checker (WCAG 2.1) ----
function ccParse(s){
  s=(s||"").trim().toLowerCase();
  if(NAMED[s]) return NAMED[s];
  let m=s.match(/^#?([0-9a-f]{3}|[0-9a-f]{6})$/);
  if(m){const h=m[1];return h.length===3?[0,1,2].map(i=>parseInt(h[i]+h[i],16))
      :[0,2,4].map(i=>parseInt(h.substr(i,2),16));}
  m=s.match(/rgba?\(([^)]+)\)/);
  if(m){const p=m[1].split(",").map(x=>parseFloat(x));return p.length>=3?p.slice(0,3):null;}
  return null;
}
function ccLum(rgb){
  const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
  return 0.2126*f(rgb[0])+0.7152*f(rgb[1])+0.0722*f(rgb[2]);
}
function ccGo(){
  const fg=ccParse(document.getElementById("cc-fg").value);
  const bg=ccParse(document.getElementById("cc-bg").value);
  const sw=document.getElementById("cc-sw"), out=document.getElementById("cc-out");
  if(!fg||!bg){sw.style.background="";sw.style.color="";sw.textContent="Aa preview";
    out.innerHTML='<span style="color:var(--dim)">enter two colors (hex, rgb(), or named)</span>';return;}
  const l1=ccLum(fg),l2=ccLum(bg);
  const r=(Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05);
  const hx=c=>"#"+c.map(v=>v.toString(16).padStart(2,"0")).join("");
  sw.style.background=hx(bg);sw.style.color=hx(fg);sw.textContent="Aa preview — the quick brown fox";
  const grade=v=>v?"✓ pass":"✗ fail";
  out.innerHTML=
    `<span class="k">ratio</span><span><b>${r.toFixed(2)}</b> : 1</span>`+
    `<span class="k">AA normal text (≥4.5)</span><span style="color:${r>=4.5?"var(--green)":"var(--orange)"}">${grade(r>=4.5)}</span>`+
    `<span class="k">AA large text (≥3)</span><span style="color:${r>=3?"var(--green)":"var(--orange)"}">${grade(r>=3)}</span>`+
    `<span class="k">AAA normal text (≥7)</span><span style="color:${r>=7?"var(--green)":"var(--orange)"}">${grade(r>=7)}</span>`+
    `<span class="k">AAA large text (≥4.5)</span><span style="color:${r>=4.5?"var(--green)":"var(--orange)"}">${grade(r>=4.5)}</span>`;
}
document.getElementById("cc-fg").addEventListener("input",ccGo);
document.getElementById("cc-bg").addEventListener("input",ccGo);

cGo(); tStat(); uGo(); ccGo();

// ---- Slug ----
function sgGo(){
  const lines = document.getElementById("sg-in").value.split("\n");
  const slugs = lines.map(l => l
    .normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[''’]/g, "")
    .replace(/[^a-z0-9\u4e00-\u9fff_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-"));
  document.getElementById("sg-out").innerHTML =
    slugs.map((s,i) => s ? `<div class="kv"><code>${esc(s)}</code></div>` : "").join("") || "…";
}
document.getElementById("sg-in").addEventListener("input", sgGo);

// date calculator
(function(){
  const a=document.getElementById("dc-a"), b=document.getElementById("dc-b"),
        c=document.getElementById("dc-c"), n=document.getElementById("dc-n"),
        span=document.getElementById("dc-span"), res=document.getElementById("dc-res");
  if(!a) return;
  const iso=d=>d.format("YYYY-MM-DD");
  const today=dayjs(); const t7=dayjs().add(7,"day");
  a.value=iso(today); b.value=iso(t7); c.value=iso(today);
  function spanGo(){
    const A=dayjs(a.value), B=dayjs(b.value);
    if(!A.isValid()||!B.isValid()){span.textContent="";return}
    const dd=B.diff(A,"day");
    const wk=Math.abs(dd)/7;
    span.innerHTML = `<b>${Math.abs(dd)}</b> days (${Math.abs(dd)+1} inclusive) ≈ <b>${wk.toFixed(1)}</b> weeks` +
      `<span style="color:var(--dim)"> · ${a.value} is ${A.format("ddd")} · ${b.value} is ${B.format("ddd")} · business days ≈ ${Math.round(Math.abs(dd)*5/7)}</span>`;
  }
  function plusGo(sign){
    const C=dayjs(c.value), N=parseInt(n.value)||0;
    if(!C.isValid()){res.textContent="";return}
    const R=C.add(sign*N,"day");
    res.innerHTML=`<b>${iso(R)}</b> (${R.format("ddd")})`;
  }
  a.addEventListener("input",spanGo); b.addEventListener("input",spanGo);
  document.getElementById("dc-plus").addEventListener("click",()=>plusGo(1));
  document.getElementById("dc-minus").addEventListener("click",()=>plusGo(-1));
  c.addEventListener("input",()=>plusGo(1)); n.addEventListener("input",()=>plusGo(1));
  spanGo(); plusGo(1);
})();

// timezone converter
(function(){
  const inp=document.getElementById("tz-in"), out=document.getElementById("tz-out");
  if(!inp) return;
  const ZONES=[
    ["Pacific/Auckland","Auckland"],["Australia/Sydney","Sydney"],["Asia/Tokyo","Tokyo"],
    ["Asia/Shanghai","Shanghai/China"],["Asia/Singapore","Singapore"],["Asia/Kolkata","India"],
    ["Europe/Berlin","Berlin/CET"],["Europe/London","London/GMT"],["Atlantic/Azores","Azores"],
    ["America/New_York","New York/ET"],["America/Chicago","Chicago/CT"],["America/Denver","Denver/MT"],
    ["America/Los_Angeles","Los Angeles/PT"],["America/Sao_Paulo","São Paulo"],["Pacific/Honolulu","Honolulu"],["UTC","UTC"]
  ];
  const fmtz=(d,z)=>new Intl.DateTimeFormat("en-GB",{timeZone:z,weekday:"short",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit",hour12:false}).format(d);
  function go(){
    const d = inp.value ? new Date(inp.value) : new Date();
    out.innerHTML = ZONES.map(([z,name])=>{ 
      let off="";
      try{ off = (new Intl.DateTimeFormat("en",{timeZone:z,timeZoneName:"shortOffset"}).formatToParts(d).find(p=>p.type==="timeZoneName")||{}).value||""; }catch(e){}
      return `<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border)"><span style="color:var(--dim)">${name}</span><span>${fmtz(d,z)} <span style="color:var(--dim)">${off}</span></span></div>`;
    }).join("");
  }
  inp.addEventListener("input",go);
  const now=new Date(); now.setMinutes(now.getMinutes()-now.getTimezoneOffset());
  inp.value=now.toISOString().slice(0,16);
  go();
})();

// -- word frequency ----------------------------------------------------------
(() => {
  const STOP = new Set(("the a an and or but of to in on for with at by from as is are was were be been being it its this that these those i you he she we they me him her us them my your his our their what which who whom when where why how not no nor so if then than too very can will just do does did done have has had having would should could shall may might must about above after again against all am any because before below between both down during each few further here there once only other out over own same some such under until up while into through".split(" ")));
  const esc = s2 => { const d=document.createElement("div"); d.textContent=s2||""; return d.innerHTML; };
  let lastCsv = "";
  function run() {
    const words = (document.getElementById("fq-in").value.toLowerCase().match(/[a-z0-9''-]+/g) || [])
      .map(w => w.replace(/^['-]+|['-]+$/g,"")).filter(Boolean);
    const hide = document.getElementById("fq-stop").checked;
    const counts = new Map();
    words.forEach(w => counts.set(w, (counts.get(w)||0)+1));
    const rows = [...counts.entries()].filter(([w]) => !hide || !STOP.has(w))
      .sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]));
    const top = rows.slice(0, 100);
    const total = words.length;
    document.getElementById("fq-out").innerHTML = !total ? '<span style="color:var(--dim)">no words</span>' :
      `<div style="font-size:12px;color:var(--dim);margin-bottom:6px">${total} words · ${counts.size} unique · showing ${Math.min(100,rows.length)}${hide?" (stopwords hidden)":""}</div>` +
      `<table class="tbl"><tr><th>word</th><th>count</th><th>%</th></tr>` +
      top.map(([w,c]) => `<tr><td>${esc(w)}</td><td class="num">${c}</td><td class="num">${(100*c/total).toFixed(1)}%</td></tr>`).join("") + `</table>`;
    lastCsv = "word,count,percent\n" + rows.map(([w,c]) => `${JSON.stringify(w)},${c},${(100*c/total).toFixed(2)}`).join("\n");
  }
  document.getElementById("fq-in").addEventListener("input", run);
  document.getElementById("fq-stop").addEventListener("change", run);
  document.getElementById("fq-csv").onclick = () => navigator.clipboard?.writeText(lastCsv).then(() => {
    const b = document.getElementById("fq-csv"); b.textContent = "copied"; setTimeout(() => b.textContent = "copy as CSV", 1200);
  });
  document.getElementById("fq-in").value = "the quick brown fox jumps over the lazy dog and the dog looks back at the fox the fox grins";
  run();
})();
// ---- line ops ----
(function(){
  const $ = id => document.getElementById(id);
  let out = [];
  function apply(op, lines){
    switch(op){
      case "az": return [...lines].sort((a,b)=>a.localeCompare(b));
      case "za": return [...lines].sort((a,b)=>b.localeCompare(a));
      case "uniq": return [...new Set(lines)];
      case "rev": return [...lines].reverse();
      case "shuf": { const l=[...lines]; for(let i=l.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[l[i],l[j]]=[l[j],l[i]];} return l; }
      case "num": return lines.map((l,i)=>`${i+1}. ${l}`);
      case "trim": return lines.map(l=>l.trim()).filter(l=>l!=="");
      case "empty": return lines.filter(l=>l.trim()!=="");
    }
  }
  function show(){
    $("ln-out").textContent = out.join("\n") || "(empty)";
    $("ln-stat").textContent = `${out.length} lines`;
  }
  document.querySelectorAll('[data-op]').forEach(b=>b.onclick=()=>{
    out = apply(b.dataset.op, $("ln-in").value.split("\n"));
    show();
  });
  $("ln-copy").onclick=()=>navigator.clipboard?.writeText($("ln-out").textContent)
    .then(()=>{const b=$("ln-copy");b.textContent="✓";setTimeout(()=>b.textContent="copy",1200);});
  $("ln-in").value = "banana\napple\ncherry\napple\n  fig  \n\ndate";
})();

// ---- OPML → feeds.yaml ----
(function () {
  function go() {
    const raw = document.getElementById("op-in").value.trim();
    if (!raw) { document.getElementById("op-out").textContent = ""; document.getElementById("op-err").textContent = ""; return; }
    const doc = new DOMParser().parseFromString(raw, "text/xml");
    if (doc.querySelector("parsererror")) { document.getElementById("op-out").textContent = ""; document.getElementById("op-err").textContent = "✗ not valid XML"; return; }
    const outs = [...doc.querySelectorAll("outline[xmlUrl], outline[xmlurl]")];
    if (!outs.length) { document.getElementById("op-out").textContent = ""; document.getElementById("op-err").textContent = "✗ no <outline xmlUrl> entries found"; return; }
    const yaml = outs.map(o => {
      const name = o.getAttribute("text") || o.getAttribute("title") || o.getAttribute("xmlUrl") || o.getAttribute("xmlurl");
      const url = o.getAttribute("xmlUrl") || o.getAttribute("xmlurl");
      return `  - name: ${name.replace(/"/g, '\\"')}\n    url: ${url}`;
    }).join("\n");
    document.getElementById("op-out").textContent = `feeds:\n${yaml}`;
    document.getElementById("op-err").textContent = `${outs.length} feeds`;
  }
  document.getElementById("op-in").addEventListener("input", go);
  document.getElementById("op-copy").onclick = () => navigator.clipboard?.writeText(document.getElementById("op-out").textContent).then(() => { document.getElementById("op-copy").textContent = "copied"; setTimeout(() => document.getElementById("op-copy").textContent = "copy yaml", 1200); });
  document.getElementById("op-in").value = '<opml version="2.0"><body><outline text="HN" xmlUrl="https://hnrss.org/frontpage"/><outline text="Simon" xmlUrl="https://simonwillison.net/atom/everything/"/></body></opml>';
  go();
})();


// ---- OPML starter pack ----
(function () {
  const LANE_NAMES = { br: "blogs / blogrolls", yt: "YouTube channels", nl: "newsletters",
    sec: "security", eb: "eng blogs", tb: "tech blogs", pb: "podcasts / personal",
    misc: "misc / community", tldr: "TLDR", github: "GitHub", aws: "AWS",
    gitlab: "GitLab", slack: "Slack", meta: "Meta" };
  const lanesEl = document.getElementById("ob-lanes");
  const errEl = document.getElementById("ob-err");
  const statEl = document.getElementById("ob-stat");
  let REG = null; // {key: feed}
  let DEAD = new Set(), DORM = new Set();

  function xmlEsc(s) {
    return String(s || "").replace(/[&<>"']/g, c =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" }[c]));
  }

  function selectedLanes() {
    return [...lanesEl.querySelectorAll("input[type=checkbox]:checked")].map(b => b.value);
  }

  function buildOpml() {
    const lanes = selectedLanes();
    const bodies = lanes.map(lane => {
      const outlines = Object.values(REG)
        .filter(f => (f.lane || (f.key || "").split("_")[0]) === lane)
        .filter(f => !DEAD.has(f.key) && !DORM.has(f.key))
        .map(f => `      <outline text="${xmlEsc(f.label || f.key)}" title="${xmlEsc(f.label || f.key)}" type="rss" xmlUrl="${xmlEsc(f.feed || f.url || "")}"/>`)
        .join("\n");
      return `    <outline text="${xmlEsc(LANE_NAMES[lane] || lane)}" title="${xmlEsc(LANE_NAMES[lane] || lane)}">\n${outlines}\n    </outline>`;
    }).join("\n");
    return `<?xml version="1.0" encoding="UTF-8"?>\n<opml version="2.0">\n  <head>\n    <title>trendscope starter pack</title>\n    <dateCreated>${new Date().toUTCString()}</dateCreated>\n  </head>\n  <body>\n${bodies}\n  </body>\n</opml>`;
  }

  function stat() {
    const lanes = selectedLanes();
    const sel = lanes.reduce((a, l) =>
      a + Object.values(REG || {}).filter(f => (f.lane || (f.key || "").split("_")[0]) === l).length, 0);
    const live = lanes.reduce((a, l) =>
      a + Object.values(REG || {}).filter(f => (f.lane || (f.key || "").split("_")[0]) === l)
        .filter(f => !DEAD.has(f.key) && !DORM.has(f.key)).length, 0);
    statEl.textContent = REG ? `${live.toLocaleString()} live feeds selected across ${lanes.length} lane(s)` +
      (sel - live ? ` — ${(sel - live).toLocaleString()} dead/dormant skipped` : "") : "";
  }

  fetch("../data/zerowatch.json").then(r => r.ok ? r.json() : {}).then(z => {
    for (const k of (z.persistent_empty || [])) DEAD.add(k);
  }).catch(() => {});
  fetch("../data/dormant.json").then(r => r.ok ? r.json() : []).then(d => {
    for (const k of (Array.isArray(d) ? d : [])) DORM.add(k);
    stat();
  }).catch(() => {});

  fetch("../data/feeds.json").then(r => r.json()).then(d => {
    const arr = Array.isArray(d) ? d : (d.feeds || []);
    REG = {};
    for (const f of arr) REG[f.key || f.feed] = f;
    const counts = {};
    for (const f of arr) {
      const l = f.lane || (f.key || "").split("_")[0] || "?";
      counts[l] = (counts[l] || 0) + 1;
    }
    const DEFAULT_ON = new Set(["sec", "eb", "tb"]);
    lanesEl.innerHTML = Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([l, n]) =>
      `<label style="display:inline-block;margin:3px 12px 3px 0;cursor:pointer"><input type="checkbox" value="${esc(l)}"${DEFAULT_ON.has(l) ? " checked" : ""}> ${esc(LANE_NAMES[l] || l)} <span style="opacity:.6">(${n.toLocaleString()})</span></label>`
    ).join("");
    lanesEl.addEventListener("change", stat);
    stat();
  }).catch(e => {
    lanesEl.textContent = "";
    errEl.textContent = "could not load ../data/feeds.json — " + e.message;
  });

  document.getElementById("ob-dl").onclick = () => {
    if (!REG) return;
    const blob = new Blob([buildOpml()], { type: "text/x-opml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "trendscope-starter-pack.opml";
    a.click();
    URL.revokeObjectURL(a.href);
  };
  document.getElementById("ob-copy").onclick = () => {
    if (!REG) return;
    navigator.clipboard?.writeText(buildOpml()).then(() => {
      const b = document.getElementById("ob-copy");
      b.textContent = "copied"; setTimeout(() => b.textContent = "copy xml", 1200);
    });
  };
})();


// ---- crontab explainer ----
const CR_NAMES={4:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],3:["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]};
function crGo(){
  const v=document.getElementById("cr-in").value.trim();
  const out=document.getElementById("cr-out"),err=document.getElementById("cr-err");
  out.innerHTML="";err.textContent="";
  if(!v)return;
  const f=v.split(/\s+/);
  if(f.length!==5){err.textContent="need exactly 5 fields (min hour dom mon dow)";return;}
  let hits;
  try { hits = new Cron(v).nextRuns(5); }
  catch(e) { err.textContent="could not parse one or more fields"; return; }
  out.innerHTML="<b>"+cronstrue.toString(v)+"</b><ul style='margin:6px 0 0;padding-left:18px'>"+
    hits.map(d=>"<li>"+d.toLocaleString()+"</li>").join("")+"</ul>"+
    (hits.length?"":"<li>no fire times in the next year — check dom/dow combination</li>");
}
document.getElementById("cr-in").addEventListener("input",crGo);


// ---- chmod calculator ----
const cmBoxes=[...document.querySelectorAll('#cm-t input')];
function cmGo(){
  const g=[0,0,0];
  cmBoxes.forEach(b=>{if(b.checked)g[+b.dataset.g]|= +b.dataset.b;});
  const oct=g.join('');
  const sym=['u','g','o'].map((u,i)=>
    u+'='+(g[i]&4?'r':'-')+(g[i]&2?'w':'-')+(g[i]&1?'x':'-')).join(', ');
  const ls=g.map(v=>'rwx'.split('').map((c,i)=>(v>>(2-i))&1?c:'-').join('')).join(' ');
  document.getElementById('cm-out').innerHTML=
    `<b>chmod ${oct}</b> · symbolic <code>${sym}</code> · ls -l <code>${ls}</code>`;
  const o=document.getElementById('cm-oct');if(o.value!==oct)o.value=oct;
}
cmBoxes.forEach(b=>b.addEventListener('change',cmGo));
document.getElementById('cm-oct').addEventListener('input',e=>{
  const v=e.target.value.trim();
  if(!/^[0-7]{3}$/.test(v))return;
  cmBoxes.forEach(b=>b.checked=((+v[+b.dataset.g])&+b.dataset.b)!==0);
  cmGo();
});


// --- csv <-> json ---
function cvParse(t){
  return Papa.parse(t, { skipEmptyLines: "greedy" }).data;
}
document.getElementById('cv-go').onclick=()=>{
  try{
    const rows=cvParse(document.getElementById('cv-in').value);
    if(rows.length<1) throw 'empty';
    const head=rows[0];
    let out;
    if(document.getElementById('cv-obj').checked){
      out=rows.slice(1).map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]??""])));
    } else out=rows.slice(1);
    document.getElementById('cv-out').value=JSON.stringify(out,null,2);
    document.getElementById('cv-outx').textContent=out.length+' rows · '+head.length+' cols';
  }catch(e){ document.getElementById('cv-outx').textContent='parse error: '+e; }
};
document.getElementById('cv-bk').onclick=()=>{
  try{
    const arr=JSON.parse(document.getElementById('cv-in').value);
    if(!Array.isArray(arr)||!arr.length) throw 'need a JSON array';
    let head,rows;
    if(typeof arr[0]==='object'&&arr[0]!==null&&!Array.isArray(arr[0])){
      head=[...new Set(arr.flatMap(o=>Object.keys(o)))];
      rows=arr.map(o=>head.map(h=>o[h]??""));
    } else { head=[];rows=arr; }
    document.getElementById('cv-out').value=Papa.unparse([...(head.length?[head]:[]),...rows]);
    document.getElementById('cv-outx').textContent=rows.length+' rows · '+(head.length||rows[0].length)+' cols';
  }catch(e){ document.getElementById('cv-outx').textContent='parse error: '+e; }
};

// --- semver compare ---
function svParse(v){
  v=v.trim().replace(/^v/,'');
  const m=v.match(/^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+.*)?$/);
  if(!m) return null;
  return {maj:+m[1],min:+m[2],pat:+m[3],pre:m[4]?m[4].split('.'):null};
}
function svCmpPre(a,b){
  if(!a&&!b) return 0; if(!a) return 1; if(!b) return -1;
  for(let i=0;i<Math.max(a.length,b.length);i++){
    if(i>=a.length) return -1; if(i>=b.length) return 1;
    const x=a[i],y=b[i],nx=/^\d+$/.test(x),ny=/^\d+$/.test(y);
    if(nx&&ny){const d=+x-+y;if(d)return d<0?-1:1;}
    else if(nx) return -1; else if(ny) return 1;
    else if(x!==y) return x<y?-1:1;
  }
  return 0;
}
function svLocalCmp(a,b){
  const pa=svParse(a),pb=svParse(b);
  if(!pa||!pb) return null;
  const d=pa.maj-pb.maj||pa.min-pb.min||pa.pat-pb.pat||svCmpPre(pa.pre,pb.pre);
  return Math.sign(d);
}
function svLib(){
  return (window.compareVersions&&compareVersions.compareVersions)?compareVersions:null;
}
function svCmp2(a,b){
  const lib=svLib();
  if(lib){try{return lib.compareVersions(a,b)}catch(e){return null}}
  return svLocalCmp(a,b);
}

// --- password generator ---
document.getElementById('pg-go').onclick=()=>{
  let chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  if(document.getElementById('pg-sym').checked) chars+='!@#$%^&*()-_=+[]{};:,.<>?';
  if(document.getElementById('pg-amb').checked) chars=chars.replace(/[0O1lI]/g,'');
  const n=Math.max(4,Math.min(128,+document.getElementById('pg-n').value||20));
  const rnd=crypto.getRandomValues(new Uint32Array(n));
  // rejection-sample to avoid modulo bias
  const out=[];
  let i=0;
  while(out.length<n){
    const v=rnd[i%rnd.length];i++;
    if(v<Math.floor(4294967296/chars.length)*chars.length) out.push(chars[v%chars.length]);
  }
  const pw=out.join('');
  document.getElementById('pg-out').textContent=pw;
  const bits=Math.round(n*Math.log2(chars.length));
  document.getElementById('pg-bits').textContent=`${n} chars · ${chars.length}-char alphabet · ~${bits} bits entropy`;
};

// --- case converter ---
function ccWords(t){
  return t.replace(/([a-z0-9])([A-Z])/g,'$1 $2')
          .replace(/[^A-Za-z0-9]+/g,' ')
          .trim().split(/\s+/).filter(Boolean).map(w=>w.toLowerCase());
}
document.getElementById('cc-in').addEventListener('input',()=>{
  const ws=ccWords(document.getElementById('cc-in').value);
  const out=document.getElementById('cc-out');
  if(!ws.length){out.textContent='';return;}
  const cap=w=>w[0].toUpperCase()+w.slice(1);
  const j=(a)=>a.join('');
  const rows={
    'camelCase': ws[0]+j(ws.slice(1).map(cap)),
    'PascalCase': j(ws.map(cap)),
    'snake_case': ws.join('_'),
    'SCREAMING_SNAKE': ws.join('_').toUpperCase(),
    'kebab-case': ws.join('-'),
    'TRAIN-CASE': ws.join('-').toUpperCase(),
    'dot.case': ws.join('.'),
    'Title Case': ws.map(cap).join(' '),
    'lower case': ws.join(' '),
    'UPPER CASE': ws.join(' ').toUpperCase(),
  };
  out.textContent=Object.entries(rows).map(([k,v])=>k.padEnd(16,' ')+v).join('\n');
});

// --- sort & dedupe lines ---
document.querySelectorAll('[data-sl]').forEach(b=>b.onclick=()=>{
  const ci=document.getElementById('sl-ci').checked, tr=document.getElementById('sl-trim').checked;
  let lines=document.getElementById('sl-in').value.split('\n');
  if(tr) lines=lines.map(l=>l.trim());
  const key=l=>ci?l.toLowerCase():l;
  const mode=b.dataset.sl;
  if(mode==='az') lines.sort((a,c)=>key(a).localeCompare(key(c)));
  else if(mode==='za') lines.sort((a,c)=>key(c).localeCompare(key(a)));
  else if(mode==='len') lines.sort((a,c)=>a.length-c.length||key(a).localeCompare(key(c)));
  else if(mode==='num') lines.sort((a,c)=>(parseFloat(a)||0)-(parseFloat(c)||0));
  else if(mode==='dedupe'){const seen=new Set();lines=lines.filter(l=>{const k=key(l);if(seen.has(k))return false;seen.add(k);return true;});}
  else if(mode==='rev') lines=lines.slice().reverse();
  else if(mode==='shuffle'){for(let i=lines.length-1;i>0;i--){const j=crypto.getRandomValues(new Uint32Array(1))[0]%(i+1);[lines[i],lines[j]]=[lines[j],lines[i]];}}
  document.getElementById('sl-out').value=lines.join('\n');
  document.getElementById('sl-stat').textContent=lines.length+' lines out';
});

// --- uuid v4 generator ---
document.getElementById('uu-go').onclick=()=>{
  const n=Math.max(1,Math.min(100,+document.getElementById('uu-n').value||5));
  const up=document.getElementById('uu-up').checked, nd=document.getElementById('uu-nodash').checked;
  let out=[];
  for(let i=0;i<n;i++){let u=crypto.randomUUID();if(nd)u=u.replaceAll('-','');if(up)u=u.toUpperCase();out.push(u);}
  document.getElementById('uu-out').value=out.join('\n');
};
document.getElementById('uu-copy').onclick=async()=>{
  await navigator.clipboard.writeText(document.getElementById('uu-out').value);
  document.getElementById('uu-copy').textContent='copied!';
  setTimeout(()=>document.getElementById('uu-copy').textContent='copy',1200);
};

// --- file-size unit converter ---
document.getElementById('by-go').onclick=()=>{
  const n=parseFloat(document.getElementById('by-n').value);
  const u=parseFloat(document.getElementById('by-u').value);
  if(!isFinite(n)){document.getElementById('by-out').textContent='enter a number';return;}
  const bytes=n*u;
  const fmt=(v,u)=>v.toLocaleString(undefined,{maximumFractionDigits:4})+' '+u;
  const rows=[
    ['B',fmt(bytes,'bytes')],
    ['SI',fmt(bytes/1e3,'KB')+' · '+fmt(bytes/1e6,'MB')+' · '+fmt(bytes/1e9,'GB')+' · '+fmt(bytes/1e12,'TB')],
    ['IEC',fmt(bytes/1024,'KiB')+' · '+fmt(bytes/1048576,'MiB')+' · '+fmt(bytes/1073741824,'GiB')+' · '+fmt(bytes/1099511627776,'TiB')],
    ['bits',fmt(bytes*8,'bits')+' = '+fmt(bytes*8/1e6,'Mbit')+' = '+fmt(bytes*8/1e9,'Gbit')],
  ];
  document.getElementById('by-out').innerHTML=rows.map(r=>'<div><b>'+r[0]+'</b>: '+r[1]+'</div>').join('');
};

// --- lorem ipsum ---
const LOREM_C='lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure in reprehenderit voluptate velit esse cillum fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum'.split(' ');
const LOREM_T='deploy refactor microservice kubernetes docker pipeline observability latency throughput idempotent schema migration graphql kubernetes ingress canary rollback feature-flag endpoint serializer cache invalidation protobuf grpc serverless lambda webhook pagination retry backoff circuit-breaker loadbalancer autoscaling shard replication consensus quorum quorum'.split(' ');
function loWord(pool){const r=crypto.getRandomValues(new Uint32Array(1))[0];return pool[r%pool.length];}
function loSent(pool,n){const w=[];for(let i=0;i<n;i++)w.push(loWord(pool));const s=w.join(' ');return s[0].toUpperCase()+s.slice(1)+'.';}
function loPara(pool){const n=3+crypto.getRandomValues(new Uint32Array(1))[0]%4;const s=[];for(let i=0;i<n;i++)s.push(loSent(pool,6+crypto.getRandomValues(new Uint32Array(1))[0]%12));return s.join(' ');}
document.getElementById('lo-go').onclick=()=>{
  const n=Math.max(1,Math.min(50,+document.getElementById('lo-n').value||3));
  const unit=document.getElementById('lo-unit').value;
  const pool=document.getElementById('lo-flavor').value==='tech'?LOREM_T:LOREM_C;
  let out;
  if(unit==='p') out=Array.from({length:n},()=>loPara(pool)).join('\n\n');
  else if(unit==='s') out=Array.from({length:n},()=>loSent(pool,8+crypto.getRandomValues(new Uint32Array(1))[0]%8)).join(' ');
  else out=Array.from({length:n},()=>loWord(pool)).join(' ')+'.';
  if(document.getElementById('lo-start').checked&&unit!=='w') out='Lorem ipsum dolor sit amet, '+out;
  document.getElementById('lo-out').value=out;
};
document.getElementById('lo-copy').onclick=async()=>{await navigator.clipboard.writeText(document.getElementById('lo-out').value);document.getElementById('lo-copy').textContent='copied!';setTimeout(()=>document.getElementById('lo-copy').textContent='copy',1200);};

// --- aspect ratio ---
function arCalc(){
  const w=parseFloat(document.getElementById('ar-w').value),h=parseFloat(document.getElementById('ar-h').value);
  const dw=parseFloat(document.getElementById('ar-dw').value),dh=parseFloat(document.getElementById('ar-dh').value);
  if(!(w>0&&h>0)){document.getElementById('ar-out').textContent='enter ratio';return;}
  const g=(a,b)=>b?g(b,a%b):a;
  const d=g(Math.round(w*100),Math.round(h*100));
  const sw=w*100/d,sh=h*100/d;
  let out='ratio '+sw+':'+sh+' (decimal '+(w/h).toFixed(4)+')';
  if(dw>0) out+=' · width '+dw+'px → height '+(dw*h/w).toFixed(1)+'px';
  if(dh>0) out+=' · height '+dh+'px → width '+(dh*w/h).toFixed(1)+'px';
  out+=' · css: aspect-ratio:'+sw+'/'+sh+' 或 padding-top:'+(h/w*100).toFixed(2)+'%';
  document.getElementById('ar-out').textContent=out;
}
document.getElementById('ar-go').onclick=arCalc;
document.querySelectorAll('[data-ar]').forEach(b=>b.onclick=()=>{
  const [w,h]=b.dataset.ar.split(',');
  document.getElementById('ar-w').value=w;document.getElementById('ar-h').value=h;arCalc();
});

// --- morse ---
const MORSE={'a':'.-','b':'-...','c':'-.-.','d':'-..','e':'.','f':'..-.','g':'--.','h':'....','i':'..','j':'.---','k':'-.-','l':'.-..','m':'--','n':'-.','o':'---','p':'.--.','q':'--.-','r':'.-.','s':'...','t':'-','u':'..-','v':'...-','w':'.--','x':'-..-','y':'-.--','z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.','.':'.-.-.-',',':'--..--','?':'..--..','!':'-.-.--',"'":'.----.','"':'.-..-.','(':'-.--.',')':'-.--.-','&':'.-...',':':'---...',';':'-.-.-.','=':'-...-','+':'.-.-.','-':'-....-','_':'..--.-','/':'-..-.','@':'.--.-.'};
const MORSE_R={};for(const k in MORSE)MORSE_R[MORSE[k]]=k;
document.querySelectorAll('[data-mo]').forEach(b=>b.onclick=()=>{
  const v=document.getElementById('mo-in').value;
  let out;
  if(b.dataset.mo==='enc'){
    out=v.toLowerCase().split('').map(c=>c===' '?'/':(MORSE[c]||'')).filter(x=>x!=='').join(' ');
  }else{
    out=v.trim().split(/ +/).map(w=>w==='/'?' ':(MORSE_R[w]||'?')).join('');
  }
  document.getElementById('mo-out').value=out;
});

// --- roman numerals ---
const RN=[[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
function toRoman(n){if(n<1||n>3999)return 'out of range 1-3999';let s='';for(const[v,r]of RN)while(n>=v){s+=r;n-=v;}return s;}
const RN_RX=/^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$/;
function fromRoman(s){s=s.toUpperCase();if(!RN_RX.test(s))return 'invalid roman numeral';const map={I:1,V:5,X:10,L:50,C:100,D:500,M:1000};let t=0;for(let i=0;i<s.length;i++){t+=(i+1<s.length&&map[s[i]]<map[s[i+1]])?-map[s[i]]:map[s[i]];}return t;}
document.querySelectorAll('[data-rn]').forEach(b=>b.onclick=()=>{
  const v=document.getElementById('rn-in').value.trim();
  document.getElementById('rn-out').textContent=b.dataset.rn==='enc'?toRoman(parseInt(v,10)):fromRoman(v);
});

// ---- mime types ----
const MIME=[
["aac","audio/aac"],["avif","image/avif"],["avi","video/x-msvideo"],["bin","application/octet-stream"],
["bmp","image/bmp"],["bz2","application/x-bzip2"],["css","text/css"],["csv","text/csv"],
["doc","application/msword"],["docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
["eot","application/vnd.ms-fontobject"],["epub","application/epub+zip"],["flac","audio/flac"],["gif","image/gif"],
["gz","application/gzip"],["htm","text/html"],["html","text/html"],["ico","image/vnd.microsoft.icon"],
["ics","text/calendar"],["jar","application/java-archive"],["jpeg","image/jpeg"],["jpg","image/jpeg"],
["js","text/javascript"],["json","application/json"],["jsonld","application/ld+json"],["m3u8","application/vnd.apple.mpegurl"],
["m4a","audio/mp4"],["md","text/markdown"],["mjs","text/javascript"],["mkv","video/x-matroska"],
["mov","video/quicktime"],["mp3","audio/mpeg"],["mp4","video/mp4"],["mpg","video/mpeg"],
["odp","application/vnd.oasis.opendocument.presentation"],["ods","application/vnd.oasis.opendocument.spreadsheet"],
["odt","application/vnd.oasis.opendocument.text"],["oga","audio/ogg"],["ogv","video/ogg"],["ogx","application/ogg"],
["otf","font/otf"],["pdf","application/pdf"],["png","image/png"],["pptx","application/vnd.openxmlformats-officedocument.presentationml.presentation"],
["rar","application/vnd.rar"],["rtf","application/rtf"],["sh","application/x-sh"],["sql","application/sql"],
["svg","image/svg+xml"],["tar","application/x-tar"],["tif","image/tiff"],["tiff","image/tiff"],
["ts","video/mp2t"],["ttf","font/ttf"],["txt","text/plain"],["vsd","application/vnd.visio"],
["wav","audio/wav"],["weba","audio/webm"],["webm","video/webm"],["webmanifest","application/manifest+json"],
["webp","image/webp"],["woff","font/woff"],["woff2","font/woff2"],["xhtml","application/xhtml+xml"],
["xls","application/vnd.ms-excel"],["xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
["xml","application/xml"],["yaml","application/yaml"],["yml","application/yaml"],["zip","application/zip"],["7z","application/x-7z-compressed"]];
function mmGo(){
  const q=document.getElementById("mm-in").value.trim().toLowerCase().replace(/^\./,"");
  const rows=MIME.filter(([e,t])=>!q||e.includes(q)||t.includes(q));
  document.getElementById("mm-out").innerHTML = rows.length
    ? `<table style="width:100%;font-size:12.5px;border-collapse:collapse">${rows.map(([e,t])=>`<tr><td style="padding:2px 8px 2px 0;color:var(--dim)">.${e}</td><td><code>${t}</code></td></tr>`).join("")}</table>`
    : `<span style="color:var(--dim)">no match — ${MIME.length} types indexed</span>`;
}
document.getElementById("mm-in").addEventListener("input",mmGo);
mmGo();

function svSort(){
  const lines=document.getElementById("sv-in").value.split("\n").map(l=>l.trim()).filter(Boolean);
  const out=document.getElementById("sv-out");
  if(!lines.length){out.textContent="";return}
  const lib=svLib();
  const valid=lines.filter(v=>lib&&lib.validate?lib.validate(v):svParse(v)!==null);
  const sorted=valid.sort((x,y)=>svCmp2(x,y)||0);
  const bad=lines.filter(v=>!valid.includes(v));
  out.innerHTML=sorted.join("<br>")+(bad.length?`<div class="hint" style="margin-top:6px">skipped: ${bad.join(", ")}</div>`:"");
}
function svCmp(){
  const a=document.getElementById("sv-a").value.trim(),b=document.getElementById("sv-b").value.trim();
  const out=document.getElementById("sv-out");
  if(!a||!b){out.textContent="";return}
  const r=svCmp2(a,b);
  out.innerHTML=r===null?`invalid semver`:`<code>${a}</code> ${r<0?"&lt;":r>0?"&gt;":"="} <code>${b}</code>`;
}

function rxGo(){
  const pat=document.getElementById("rx-pat").value;
  const fl=document.getElementById("rx-fl").value.trim()||"g";
  const txt=document.getElementById("rx-in").value;
  const out=document.getElementById("rx-out");
  out.innerHTML="";
  if(!pat||!txt)return;
  let re;
  try{re=new RegExp(pat,fl.includes("g")?fl:fl+"g")}
  catch(e){out.textContent="invalid pattern: "+e.message;return}
  const escx=x=>{const d=document.createElement("div");d.textContent=x;return d.innerHTML};
  let html="",last=0,groups=[],m,n=0;
  while((m=re.exec(txt))&&n<200){
    html+=escx(txt.slice(last,m.index))+"<mark>"+escx(m[0])+"</mark>";
    last=m.index+m[0].length;
    groups.push(`#${n+1}: "${m[0]}"`+(m.length>1?" groups: "+m.slice(1).map(g=>JSON.stringify(g)).join(", "):""));
    n++;
    if(m[0].length===0)re.lastIndex++;
  }
  html+=escx(txt.slice(last));
  out.innerHTML=`<div style="margin-bottom:6px">${n} match${n===1?"":"es"}</div><div style="font-family:ui-monospace,monospace;white-space:pre-wrap">${html}</div>`
    +(n?`<div class="hint" style="margin-top:6px">${groups.slice(0,12).map(escx).join("<br>")}${n>12?"<br>…":""}</div>`:"");
}
["rx-pat","rx-fl","rx-in"].forEach(id=>document.getElementById(id).addEventListener("input",rxGo));
