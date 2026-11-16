const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
function mdInline(s) {
  s = s.replace(/`([^`]+)`/g, (m, c) => `<code>${c}</code>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/__([^_]+)__/g, "<b>$1</b>");
  s = s.replace(/\*([^*\n]+)\*/g, "<i>$1</i>").replace(/\b_([^_\n]+)_/g, "<i>$1</i>");
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|[^)\s]+)\)/g, '<a href="$2">$1</a>');
  return s;
}
function mdRender(src) {
  const lines = src.split("\n");
  let html = "", inCode = false, list = null, para = [], tbl = null;
  const flushPara = () => { if (para.length) { html += `<p>${mdInline(para.join(" "))}</p>`; para = []; } };
  const flushList = () => { if (list) { html += `</${list}>`; list = null; } };
  const flushTbl = () => { if (tbl) { html += "</table>"; tbl = null; } };
  for (const raw of lines) {
    if (/^```/.test(raw)) {
      flushPara(); flushList(); flushTbl();
      html += inCode ? "</code></pre>" : "<pre><code>";
      inCode = !inCode; continue;
    }
    if (inCode) { html += esc(raw) + "\n"; continue; }
    const t = raw.trimEnd();
    if (!t.trim()) { flushPara(); flushList(); flushTbl(); continue; }
    if (/^\|.+\|$/.test(t)) {
      flushPara(); flushList();
      const cells = t.split("|").slice(1, -1).map(c => c.trim());
      if (cells.every(c => /^:?-+:?$/.test(c))) continue;
      if (!tbl) { tbl = true; html += "<table>"; }
      html += "<tr>" + cells.map(c => `<td>${mdInline(esc(c))}</td>`).join("") + "</tr>";
      continue;
    }
    flushTbl();
    let m;
    if (m = t.match(/^(#{1,6})\s+(.*)/)) {
      flushPara(); flushList();
      const lv = Math.min(m[1].length, 3);
      html += `<h${lv}>${mdInline(esc(m[2]))}</h${lv}>`;
    } else if (/^(-{3,}|\*{3,})$/.test(t)) {
      flushPara(); flushList(); html += "<hr>";
    } else if (m = t.match(/^>|^&gt;/)) {
      flushPara(); flushList();
      html += `<blockquote>${mdInline(esc(t.replace(/^&gt;|^>\s?/, "")))}</blockquote>`;
    } else if (m = t.match(/^[-*+]\s+(.*)/)) {
      flushPara();
      if (list !== "ul") { flushList(); html += "<ul>"; list = "ul"; }
      html += `<li>${mdInline(esc(m[1]))}</li>`;
    } else if (m = t.match(/^\d+[.)]\s+(.*)/)) {
      flushPara();
      if (list !== "ol") { flushList(); html += "<ol>"; list = "ol"; }
      html += `<li>${mdInline(esc(m[1]))}</li>`;
    } else {
      para.push(t);
    }
  }
  flushPara(); flushList(); flushTbl();
  return html;
}
const md = await fetch("docs/api.md", {cache:"no-cache"}).then(r => r.text()).catch(() => null);
document.getElementById("doc").innerHTML = md ? mdRender(md) : '<p id="err">docs/api.md unavailable</p>';
