const esc = s => { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; };
const $ = id => document.getElementById(id);

function snippet(el) {
  const s = el.outerHTML || "";
  return s.length > 110 ? s.slice(0, 107) + "…" : s;
}
function accessibleName(el) {
  return (el.getAttribute("aria-label") ||
          el.getAttribute("aria-labelledby") ||
          el.getAttribute("alt") ||
          el.getAttribute("title") ||
          (el.textContent || "")).trim();
}

function audit(html) {
  const issues = [];
  const doc = new DOMParser().parseFromString(html, "text/html");
  const add = (sev, what, el) => issues.push({ sev, what, code: el ? snippet(el) : "" });

  if (!/<html[^>]*\slang=/i.test(html))
    add("warn", "missing lang attribute on <html>");
  if (!/<title[^>]*>[^<]/i.test(html) && /<html/i.test(html))
    add("warn", "missing <title>");

  doc.querySelectorAll("img").forEach(el => {
    if (el.getAttribute("role") === "presentation" || el.getAttribute("aria-hidden") === "true") return;
    if (!el.hasAttribute("alt")) add("err", "<img> missing alt text", el);
  });
  doc.querySelectorAll("button").forEach(el => {
    if (!accessibleName(el)) add("err", "<button> has no accessible name", el);
  });
  doc.querySelectorAll("a[href]").forEach(el => {
    if (!accessibleName(el)) add("err", "<a> has no link text", el);
    if (/^#|javascript:/i.test(el.getAttribute("href") || "") && !accessibleName(el))
      add("warn", "placeholder link with no text", el);
  });
  doc.querySelectorAll("input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea").forEach(el => {
    const id = el.id;
    const labelled = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") ||
      (id && doc.querySelector(`label[for="${id}"]`)) || el.closest("label");
    if (!labelled) add("err", `<${el.tagName.toLowerCase()}> has no label`, el);
  });
  const heads = [...doc.querySelectorAll("h1,h2,h3,h4,h5,h6")];
  let prev = 0;
  heads.forEach(h => {
    const lvl = +h.tagName[1];
    if (prev && lvl > prev + 1) add("warn", `heading skips <h${prev}> → <h${lvl}>`, h);
    prev = lvl;
  });
  if (!heads.some(h => h.tagName === "H1") && heads.length)
    add("warn", "headings present but no <h1>");
  const ids = {};
  doc.querySelectorAll("[id]").forEach(el => {
    const id = el.id;
    if (ids[id]) add("err", `duplicate id "${id}"`, el);
    ids[id] = 1;
  });
  doc.querySelectorAll("[aria-hidden='true']").forEach(el => {
    if (el.querySelector("a[href],button,input,select,textarea,[tabindex]:not([tabindex='-1'])"))
      add("err", "aria-hidden element contains focusable content", el);
  });
  const VAGUE = /^(click here|here|read more|more|learn more|link|this|go|继续|更多|点击这里|阅读更多|了解详情)\.?$/i;
  doc.querySelectorAll("a[href]").forEach(el => {
    const t = (el.textContent || "").trim();
    if (t && VAGUE.test(t)) add("warn", `vague link text "${t}" — say what it leads to`, el);
  });
  doc.querySelectorAll("area[href]").forEach(el => {
    if (!el.getAttribute("alt")) add("err", "<area> in image map missing alt", el);
  });
  doc.querySelectorAll('input[type="image"]').forEach(el => {
    if (!el.getAttribute("alt") && !el.getAttribute("aria-label")) add("err", "input[type=image] missing alt", el);
  });
  doc.querySelectorAll("[autofocus]").forEach(el => {
    add("warn", "autofocus moves focus without warning", el);
  });
  doc.querySelectorAll("[role='button'],[role='link']").forEach(el => {
    const t = el.getAttribute("tabindex");
    if (t === null || +t < 0) add("warn", `${el.getAttribute("role")} role element not keyboard-focusable`, el);
  });
  doc.querySelectorAll("a[target='_blank']").forEach(el => {
    const t = (el.textContent || "") + " " + (el.getAttribute("aria-label") || "");
    if (!/new (tab|window)|新窗口|新标签/i.test(t))
      add("warn", "target=_blank link doesn't warn it opens a new tab", el);
  });
  doc.querySelectorAll("table").forEach(el => {
    if (!el.querySelector("th")) add("warn", "<table> has no <th> headers", el);
  });
  doc.querySelectorAll("[tabindex]").forEach(el => {
    const v = +el.getAttribute("tabindex");
    if (v > 0) add("warn", `tabindex="${v}" disrupts natural tab order`, el);
  });
  doc.querySelectorAll("iframe").forEach(el => {
    if (!el.getAttribute("title")) add("warn", "<iframe> missing title", el);
  });
  if (!doc.querySelector("main, [role=main]") && doc.querySelectorAll("*").length > 8)
    add("warn", "no <main> landmark");
  if (heads.filter(h => h.tagName === "H1").length > 1)
    add("warn", `multiple <h1> (${heads.filter(h => h.tagName === "H1").length})`, heads.find(h => h.tagName === "H1"));
  return { issues, doc };
}

function renderOutline(doc) {
  const heads = [...doc.querySelectorAll("h1,h2,h3,h4,h5,h6")], box = $("outline");
  if (!heads.length) { box.innerHTML = '<div class="stat">no headings</div>'; return; }
  box.innerHTML = heads.map(h => {
    const lvl = +h.tagName[1];
    return `<div class="foc" style="padding-left:${(lvl - 1) * 18 + 10}px">` +
      `<span class="num">h${lvl}</span><span>${esc((h.textContent || "").trim().slice(0, 80)) || "<i class='nm'>(empty)</i>"}</span></div>`;
  }).join("");
}

const FOCUSABLE = "a[href],area[href],button,input:not([type=hidden]),select,textarea," +
  "iframe,audio[controls],video[controls],summary,[contenteditable=true],[tabindex]";
function inHidden(el) {
  for (let p = el; p; p = p.parentElement)
    if (p.hasAttribute && (p.hasAttribute("hidden") || p.getAttribute("aria-hidden") === "true")) return true;
  return false;
}
function focusOrder(doc) {
  const els = [...doc.querySelectorAll(FOCUSABLE)].filter(el =>
    !el.disabled && !inHidden(el) && el.getAttribute("tabindex") !== "-1");
  const pos = els.filter(el => +el.getAttribute("tabindex") > 0)
    .sort((a, b) => +a.getAttribute("tabindex") - +b.getAttribute("tabindex"));
  const nat = els.filter(el => !(+el.getAttribute("tabindex") > 0));
  return pos.concat(nat);
}
function renderFocus(doc) {
  const list = focusOrder(doc), box = $("focus");
  if (!list.length) { box.innerHTML = '<div class="stat">no focusable elements</div>'; return; }
  box.innerHTML = list.map((el, i) => {
    const name = accessibleName(el);
    const tv = +el.getAttribute("tabindex");
    const label = `<${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}${tv ? ' tabindex="' + tv + '"' : ""}>`;
    return `<div class="foc${tv ? " bad" : ""}"><span class="num">${i + 1}</span>` +
      `<span><code>${esc(label)}</code> <span class="nm">${name ? "— " + esc(name.slice(0, 60)) : ""}${tv ? " ⚠ tabindex>0" : ""}</span></span></div>`;
  }).join("");
}

function go() {
  const html = $("in").value;
  const out = $("out"), stat = $("stat");
  if (!html.trim()) { out.innerHTML = ""; stat.textContent = ""; return; }
  const { issues, doc } = audit(html);
  const errs = issues.filter(i => i.sev === "err").length;
  const warns = issues.filter(i => i.sev === "warn").length;
  const n = doc.querySelectorAll("*").length;
  stat.innerHTML = `${n} elements · ` + (issues.length
    ? `<span style="color:var(--red)">${errs} errors</span> · <span style="color:var(--orange)">${warns} warnings</span>`
    : `<span class="ok">no issues found</span>`);
  out.innerHTML = issues.map(i =>
    `<div class="issue"><span class="sev ${i.sev}">${i.sev}</span>
      <span class="what">${esc(i.what)}${i.code ? ` — <code>${esc(i.code)}</code>` : ""}</span></div>`).join("");
  renderFocus(doc);
  renderOutline(doc);
}
$("in").addEventListener("input", go);
