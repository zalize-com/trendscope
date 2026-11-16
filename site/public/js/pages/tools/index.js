const TOOLS = [
  {id:"json", label:"JSON formatter"},
  {id:"regex", label:"Regex tester"},
  {id:"cron", label:"Cron explainer"},
  {id:"ts", label:"Timestamp"},
  {id:"enc", label:"Base64 / URL"},
  {id:"jwt", label:"JWT decoder"},
  {id:"chmod", label:"Chmod"},
  {id:"id", label:"UUID & hash"},
];
const tabsEl = document.getElementById("tabs");
tabsEl.innerHTML = TOOLS.map((t,i) =>
  `<button class="tab${i===0?" active":""}" data-t="${t.id}">${t.label}</button>`).join("");
function activate(id) {
  tabsEl.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x.dataset.t === id));
  document.querySelectorAll(".tool").forEach(d =>
    d.classList.toggle("active", d.dataset.tool === id));
}
tabsEl.addEventListener("click", ev => {
  const b = ev.target.closest(".tab"); if (!b) return;
  activate(b.dataset.t);
  location.hash = b.dataset.t;
});
window.addEventListener("hashchange", () => {
  const h = location.hash.slice(1);
  if (TOOLS.some(t => t.id === h)) activate(h);
});
const start = location.hash.slice(1);
activate(TOOLS.some(t => t.id === start) ? start : "json");

// ---- JSON ----
function jsonDo(op) {
  const inEl = document.getElementById("json-in"), out = document.getElementById("json-out");
  try {
    const v = JSON.parse(inEl.value);
    if (op === "pretty") out.textContent = JSON.stringify(v, null, 2);
    else if (op === "minify") out.textContent = JSON.stringify(v);
    else { out.innerHTML = `<span class="ok">Valid JSON · ${Array.isArray(v)?"array":typeof v} · ${JSON.stringify(v).length} chars</span>`; }
  } catch (e) {
    out.innerHTML = `<span class="bad">${e.message}</span>`;
  }
}

// ---- Regex ----
function reGo() {
  const pat = document.getElementById("re-pat").value;
  const flags = document.getElementById("re-flags").value || "g";
  const text = document.getElementById("re-text").value;
  const out = document.getElementById("re-out");
  try {
    const re = new RegExp(pat, flags);
    const matches = [...text.matchAll(flags.includes("g") ? re : new RegExp(pat, flags+"g"))];
    let html = text.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
    let i = 0, out2 = "";
    for (const m of matches) {
      out2 += html.slice(i, m.index) + "<mark>" + html.slice(m.index, m.index + m[0].length) + "</mark>";
      i = m.index + m[0].length;
    }
    out2 += html.slice(i);
    out.innerHTML = `<div class="${matches.length?"ok":"bad"}">${matches.length} match${matches.length===1?"":"es"}</div><br>` + out2;
  } catch (e) { out.innerHTML = `<span class="bad">${e.message}</span>`; }
}
["re-pat","re-flags","re-text"].forEach(id => document.getElementById(id).addEventListener("input", reGo));

// ---- Cron ----
const CRON_NAMES = [["minute",0,59],["hour",0,23],["day of month",1,31],["month",1,12],["day of week",0,7]];
const MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DOW = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
function cronField(f, [name, lo, hi]) {
  const map = v => name==="month" ? (MON[+v-1]||v) : name==="day of week" ? (DOW[+v]||v) : v;
  if (f === "*") return `every ${name}`;
  if (f.startsWith("*/")) return `every ${f.slice(2)} ${name}${f.slice(2)>1?"s":""}`;
  if (f.includes("-")) { const [a,b]=f.split("-"); return `${name} ${map(a)}–${map(b)}`; }
  if (f.includes(",")) return `${name} ${f.split(",").map(map).join(", ")}`;
  if (f.includes("/")) { const [r,s]=f.split("/"); return `every ${s} ${name}s in ${r}`; }
  return `${name} ${map(f)}`;
}
function cronGo() {
  const v = document.getElementById("cron-in").value.trim();
  const out = document.getElementById("cron-out");
  const parts = v.split(/\s+/);
  if (parts.length !== 5) { out.innerHTML = `<span class="bad">need 5 fields, got ${parts.length}</span>`; return; }
  const nxt = nextRuns(parts, 8);
  out.innerHTML = parts.map((p,i) => `<div><b>${CRON_NAMES[i][0]}:</b> ${cronField(p, CRON_NAMES[i])}</div>`).join("")
    + `<div style="margin-top:8px" class="ok">runs at: ${describe(parts)}</div>`
    + (nxt && nxt.length
      ? `<div style="margin-top:8px"><b>next ${nxt.length}:</b><ol style="margin:6px 0 0 20px">${nxt.map(d=>`<li>${d.toString().slice(0,21)}</li>`).join("")}</ol></div>`
      : `<div style="margin-top:8px" class="bad">no upcoming runs — check field ranges</div>`);
}
function cronSet(f, lo, hi) {
  const out = new Set();
  for (const part of f.split(",")) {
    const m2 = part.match(/^(\*|\d+(?:-\d+)?)(?:\/(\d+))?$/);
    if (!m2) return null;
    let [a,b] = m2[1] === "*" ? [lo,hi] : m2[1].split("-").map(Number);
    if (m2[1] !== "*" && !m2[1].includes("-")) b = a;
    const step = +(m2[2] || 1);
    for (let i = a; i <= b; i += step) if (i >= lo && i <= hi) out.add(i);
  }
  return out;
}
function nextRuns(parts, n) {
  const mins = cronSet(parts[0],0,59), hrs = cronSet(parts[1],0,23),
        doms = cronSet(parts[2],1,31), mons = cronSet(parts[3],1,12), dows = cronSet(parts[4],0,7);
  if (!mins||!hrs||!doms||!mons||!dows) return null;
  const res = [], t = new Date(); t.setSeconds(0,0); t.setMinutes(t.getMinutes()+1);
  for (let i = 0; i < 600000 && res.length < n; i++) {
    const dow = t.getDay(), dom = t.getDate();
    const domOk = (parts[2]==="*"&&parts[4]==="*") ||
      (parts[2]!=="*"&&parts[4]!=="*" ? doms.has(dom)||dows.has(dow) : doms.has(dom)&&dows.has(dow));
    if (mins.has(t.getMinutes()) && hrs.has(t.getHours()) && mons.has(t.getMonth()+1) && domOk)
      res.push(new Date(t));
    t.setMinutes(t.getMinutes()+1);
  }
  return res;
}
function describe([m,h,dom,mon,dow]) {
  const time = (h==="*") ? `every hour at minute ${m}` :
    (m==="*") ? `every minute of hour ${h}` :
    `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}`;
  const day = (dom==="*" && dow==="*") ? "every day" :
    (dom!=="*") ? `on day ${dom} of the month` : `on ${dow==="1-5"?"weekdays":dow}`;
  return `${time}, ${day}${mon==="*"?"":`, in ${mon}`}`;
}

// ---- Timestamp ----
function tick() {
  const n = Date.now();
  document.getElementById("ts-now").textContent = Math.floor(n/1000);
  document.getElementById("ts-utc").textContent = new Date(n).toISOString().replace("T"," ").slice(0,19)+"Z";
}
setInterval(tick, 1000); tick();
function tsGo() {
  const v = document.getElementById("ts-in").value.trim();
  const out = document.getElementById("ts-out");
  let ms;
  if (/^\d{13}$/.test(v)) ms = +v;
  else if (/^\d{10}$/.test(v)) ms = +v * 1000;
  else ms = Date.parse(v);
  if (isNaN(ms)) { out.innerHTML = `<div class="cell"><span class="bad">unrecognized — try unix seconds, ms, or ISO date</span></div>`; return; }
  const d = new Date(ms);
  out.innerHTML = [
    ["unix (s)", Math.floor(ms/1000)],
    ["unix (ms)", ms],
    ["UTC", d.toISOString()],
    ["local", d.toLocaleString()],
    ["relative", relTime(ms)],
  ].map(([k,val]) => `<div class="cell"><div class="k">${k}</div><div class="v">${val}</div></div>`).join("");
}
function relTime(ms) {
  const s = Math.round((ms - Date.now())/1000), a = Math.abs(s);
  const u = a<60?`${a}s`:a<3600?`${Math.round(a/60)}m`:a<86400?`${Math.round(a/3600)}h`:`${Math.round(a/86400)}d`;
  return s>=0 ? `in ${u}` : `${u} ago`;
}

// ---- Encode ----
function encDo(op) {
  const v = document.getElementById("enc-in").value;
  const out = document.getElementById("enc-out");
  try {
    if (op==="b64e") out.textContent = btoa(unescape(encodeURIComponent(v)));
    else if (op==="b64d") out.textContent = decodeURIComponent(escape(atob(v.trim())));
    else if (op==="urle") out.textContent = encodeURIComponent(v);
    else out.textContent = decodeURIComponent(v.trim());
  } catch (e) { out.innerHTML = `<span class="bad">${e.message}</span>`; }
}

// ---- JWT ----
function b64url(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  return decodeURIComponent(escape(atob(s)));
}
function jwtGo() {
  const v = document.getElementById("jwt-in").value.trim();
  const out = document.getElementById("jwt-out");
  const parts = v.split(".");
  if (parts.length < 2) { out.innerHTML = `<span class="bad">a JWT has 3 dot-separated parts</span>`; return; }
  try {
    const h = JSON.parse(b64url(parts[0])), p = JSON.parse(b64url(parts[1]));
    const claims = [["exp","expires"],["iat","issued at"],["nbf","not before"]]
      .filter(([k]) => p[k]).map(([k,l]) => `${l}: ${new Date(p[k]*1000).toISOString()}`).join("\n");
    out.textContent =
      "── header ──\n" + JSON.stringify(h, null, 2) +
      "\n\n── payload ──\n" + JSON.stringify(p, null, 2) +
      (claims ? "\n\n── times ──\n" + claims : "") +
      "\n\n(signature: " + (parts[2] ? "present, not verified" : "missing") + ")";
  } catch (e) { out.innerHTML = `<span class="bad">${e.message}</span>`; }
}
document.getElementById("jwt-in").addEventListener("input", jwtGo);

// ---- Chmod ----
const CHMOD = ["read","write","execute"], WHO = ["owner","group","other"];
const grid = document.getElementById("chmod-grid");
grid.innerHTML = `<div class="grid" style="grid-template-columns:80px repeat(3,1fr)">` +
  `<div class="cell"></div>` + WHO.map(w => `<div class="cell"><b>${w}</b></div>`).join("") +
  CHMOD.map((p,pi) => `<div class="cell"><b>${p}</b></div>` +
    WHO.map((_,wi) => `<div class="cell"><label><input type="checkbox" data-p="${pi}" data-w="${wi}"> ${"rwx"[pi]}</label></div>`).join("")).join("") + `</div>`;
function chmodShow() {
  let oct = "", sym = "";
  for (let w = 0; w < 3; w++) {
    let n = 0;
    for (let p = 0; p < 3; p++) {
      const on = grid.querySelector(`input[data-p="${p}"][data-w="${w}"]`).checked;
      if (on) { n += 4 >> p; sym += "rwx"[p]; } else sym += "-";
    }
    oct += n;
  }
  document.getElementById("chmod-num").value = oct;
  document.getElementById("chmod-out").textContent =
    `chmod ${oct}  ·  ls -l: -${sym}\nu=+${"rwx".split("").filter((_,i)=>grid.querySelector(`input[data-p="${i}"][data-w="0"]`).checked).join("")}`;
}
grid.addEventListener("change", chmodShow);
document.getElementById("chmod-num").addEventListener("input", e => {
  const v = e.target.value.trim();
  if (!/^[0-7]{3}$/.test(v)) return;
  for (let w = 0; w < 3; w++) for (let p = 0; p < 3; p++)
    grid.querySelector(`input[data-p="${p}"][data-w="${w}"]`).checked = !!(+v[w] & (4 >> p));
  chmodShow();
});
chmodShow();

// ---- UUID & hash ----
function uuidGo(n) {
  const out = document.getElementById("id-out");
  out.textContent = Array.from({length: n}, () => crypto.randomUUID()).join("\n");
}
async function hashGo(algo) {
  const v = document.getElementById("hash-in").value;
  const out = document.getElementById("id-out");
  const buf = await crypto.subtle.digest(algo, new TextEncoder().encode(v));
  const hex = [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
  out.textContent = `${algo}\n${hex}`;
}
