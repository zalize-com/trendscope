// <trend-scope> — embeddable web component for trendscope.
// Usage: <script src="https://zalize-com.github.io/trendscope/docs/api/widget.js" defer></script>
//        <trend-scope mode="top" n="5" source="hackernews"></trend-scope>
// modes: top (today's board) | new (fresh today) | risers (today's spikes)
// attrs: n=max items (default 5), source=filter, theme=light|dark|auto (default auto),
//        api=base url override for self-hosting (default the github.io site)
(() => {
  const API_DEFAULT = "https://zalize-com.github.io/trendscope";
  const css = `
    :host{display:block;font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
    .ts{border:1px solid var(--tsbd,#d8dee4);border-radius:8px;padding:10px 12px;background:var(--tsbg,#fff);color:var(--tsfg,#1f2328)}
    @media (prefers-color-scheme:dark){.ts{--tsbg:#0d1117;--tsfg:#e6edf3;--tsbd:#30363d}}
    :host([theme=dark]) .ts{--tsbg:#0d1117;--tsfg:#e6edf3;--tsbd:#30363d}
    :host([theme=light]) .ts{--tsbg:#fff;--tsfg:#1f2328;--tsbd:#d8dee4}
    .ts h4{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;opacity:.7}
    .ts a{color:inherit;text-decoration:none}
    .ts a:hover{text-decoration:underline}
    .ts li{margin:3px 0;list-style:none;display:flex;gap:8px;align-items:baseline}
    .ts .sc{opacity:.55;font-size:11px;min-width:34px;text-align:right}
    .ts ul{margin:0;padding:0}
    .ts .ft{margin-top:8px;font-size:11px;opacity:.55}`;
  class TrendScope extends HTMLElement {
    async connectedCallback() {
      const mode = this.getAttribute("mode") || "top";
      const n = +(this.getAttribute("n") || 5);
      const src = this.getAttribute("source");
      const API = this.getAttribute("api") || API_DEFAULT;
      const root = this.attachShadow({ mode: "open" });
      root.innerHTML = `<style>${css}</style><div class="ts"><h4>trendscope</h4><ul>loading…</ul></div>`;
      try {
        let items;
        if (mode === "new") {
          const d = await (await fetch(`${API}/docs/api/new.json`)).json();
          items = d.items || [];
        } else if (mode === "risers") {
          const d = await (await fetch(`${API}/docs/api/risers.json`)).json();
          items = (d.single_day_spikes || []).map(s => s.item || s);
        } else {
          const d = await (await fetch(`${API}/data/latest.json`)).json();
          items = Array.isArray(d.items) ? d.items : Object.values(d.items || {}).flat();
          items = items.filter(i => !["npm", "pypi", "crates"].includes(i.source));
        }
        if (src) items = items.filter(i => i.source === src);
        items.sort((a, b) => (b.score || 0) - (a.score || 0));
        items = items.slice(0, n);
        root.querySelector("ul").innerHTML = items.map(it =>
          `<li><span class="sc">${it.score ?? ""}</span><a href="${it.url}" target="_blank" rel="noopener">${(it.title || "").replace(/</g, "&lt;")}</a></li>`
        ).join("") + `<li class="ft"><a href="${API}/">trendscope →</a> ${mode} · ${items.length}</li>`;
      } catch (e) {
        root.querySelector("ul").innerHTML = `<li class="ft"><a href="${API}/">trendscope →</a></li>`;
      }
    }
  }
  customElements.define("trend-scope", TrendScope);
})();
