/* OPML doctor — feed health checker. Fetches via the opml-doctor CF Worker
 * (server-side proxy, avoids CORS). Classifies each feed:
 * alive | dormant | moved | dead | unreachable | not-a-feed | empty. */
(function () {
  const WORKER = "https://opml-doctor.zalize.workers.dev/?u=";
  const DORMANT_DAYS = 180;
  const CONCURRENCY = 6;
  const MAX_FEEDS = 500;
  const $ = (id) => document.getElementById(id);
  const inp = $("d-in"), stat = $("d-stat"), sum = $("d-sum"), tbl = $("d-tbl"),
        ops = $("d-ops"), goBtn = $("d-go"), stopBtn = $("d-stop");
  let results = [], aborted = false, running = false;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function entriesFromOpml(text) {
    const doc = new DOMParser().parseFromString(text, "text/xml");
    if (doc.querySelector("parsererror")) return null;
    const out = [];
    doc.querySelectorAll("outline").forEach((o) => {
      const feed = o.getAttribute("xmlUrl") || o.getAttribute("xmlurl");
      if (!feed) return;
      out.push({
        title: o.getAttribute("title") || o.getAttribute("text") || feed,
        feed, site: o.getAttribute("htmlUrl") || o.getAttribute("htmlurl") || "",
      });
    });
    return out;
  }

  async function workerFetch(url) {
    const r = await fetch(WORKER + encodeURIComponent(url));
    const status = parseInt(r.headers.get("X-Remote-Status") || "0", 10);
    const finalUrl = r.headers.get("X-Final-Url") || url;
    const err = r.headers.get("X-Error") || "";
    const text = await r.text();
    return { status, finalUrl, err, text };
  }

  const DATE_TAGS = ["pubDate", "published", "updated", "date", "lastBuildDate", "dc:date"];
  function analyzeFeed(text) {
    const doc = new DOMParser().parseFromString(text, "text/xml");
    if (doc.querySelector("parsererror")) return { kind: "notxml" };
    const items = [...doc.querySelectorAll("item, entry")];
    if (!items.length) {
      // channel without items but with feed-ish root = empty feed
      if (doc.querySelector("rss, feed, rdf\\:RDF, RDF")) return { kind: "empty", items: 0 };
      return { kind: "notxml" };
    }
    let newest = 0;
    for (const it of items.slice(0, 30)) {
      for (const tag of DATE_TAGS) {
        const el = it.getElementsByTagName(tag)[0] ||
          it.getElementsByTagNameNS("*", tag.replace(/^dc:/, ""))[0];
        const t = el && Date.parse(el.textContent);
        if (t && t > newest) newest = t;
      }
    }
    return { kind: "feed", items: items.length, newest };
  }

  function classify(entry, res) {
    if (res.err || res.status === 0) return { status: "unreachable", detail: res.err || "network" };
    if (res.status === 404 || res.status === 410) return { status: "dead", detail: "HTTP " + res.status };
    if (res.status >= 400) return { status: "dead", detail: "HTTP " + res.status };
    const a = analyzeFeed(res.text);
    const moved = res.finalUrl && res.finalUrl.replace(/\/$/, "") !== entry.feed.replace(/\/$/, "");
    if (a.kind === "notxml") {
      return moved ? { status: "moved", detail: "→ " + res.finalUrl, newUrl: res.finalUrl }
                   : { status: "not-a-feed", detail: "HTML or non-feed response" };
    }
    if (a.kind === "empty") {
      return moved ? { status: "moved", detail: "→ " + res.finalUrl, newUrl: res.finalUrl }
                   : { status: "empty", detail: "0 items" };
    }
    const days = a.newest ? Math.round((Date.now() - a.newest) / 86400000) : null;
    if (moved) return { status: "moved", detail: "→ " + res.finalUrl, newUrl: res.finalUrl };
    if (days != null && days > DORMANT_DAYS) return { status: "dormant", detail: days + "d since last item", items: a.items };
    return { status: "alive", detail: a.items + " items" + (days != null ? ", latest " + days + "d" : ""), items: a.items };
  }

  const ORDER = ["alive", "moved", "dormant", "empty", "not-a-feed", "dead", "unreachable"];
  const COLOR = { alive: "#2ea043", moved: "#58a6ff", dormant: "#d29922",
                  empty: "#8b949e", "not-a-feed": "#8b949e", dead: "#f85149", unreachable: "#f85149" };

  function render() {
    const counts = {};
    results.forEach((r) => { counts[r.status] = (counts[r.status] || 0) + 1; });
    sum.innerHTML = "<p class='cards' style='margin:10px 0'>" + ORDER.filter((s) => counts[s])
      .map((s) => `<span class="chip" style="border-color:${COLOR[s]};color:${COLOR[s]}">${s}: ${counts[s]}</span>`).join(" ") + "</p>";
    const sorted = [...results].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status));
    tbl.innerHTML = "<table style='width:100%;font-size:13px'><thead><tr><th></th><th>feed</th><th>status</th><th>detail</th></tr></thead><tbody>" +
      sorted.map((r, i) => `<tr><td>${i + 1}</td><td><div style="max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(r.feed)}">${esc(r.title)}</div></td>` +
        `<td><span class="chip" style="color:${COLOR[r.status]};border-color:${COLOR[r.status]}">${r.status}</span></td>` +
        `<td class="muted" style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(r.detail)}">${esc(r.detail)}</td></tr>`).join("") +
      "</tbody></table>";
    ops.style.display = results.length ? "flex" : "none";
  }

  async function run(entries) {
    running = true; aborted = false; results = [];
    goBtn.disabled = true; stopBtn.disabled = false;
    let done = 0;
    const queue = [...entries];
    async function worker() {
      while (queue.length && !aborted) {
        const e = queue.shift();
        const t0 = performance.now();
        try {
          const res = await workerFetch(e.feed);
          results.push({ ...e, ...classify(e, res), ms: Math.round(performance.now() - t0) });
        } catch (err) {
          results.push({ ...e, status: "unreachable", detail: String(err && err.message || err).slice(0, 80) });
        }
        done++;
        stat.textContent = `checked ${done}/${entries.length}…`;
        if (done % 8 === 0) render();
      }
    }
    await Promise.all(Array.from({ length: CONCURRENCY }, worker));
    render();
    stat.textContent = aborted ? `stopped at ${done}/${entries.length}` : `done — ${entries.length} feeds checked`;
    goBtn.disabled = false; stopBtn.disabled = true; running = false;
  }

  function buildFixedOpml(entries) {
    const dropDead = $("d-drop-dead").checked, fixMoved = $("d-fix-moved").checked, dropDorm = $("d-drop-dorm").checked;
    const xesc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
    const lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="1.0">',
      '  <head><title>repaired subscriptions</title></head>', "  <body>"];
    for (const r of results) {
      if (dropDead && (r.status === "dead" || r.status === "unreachable" || r.status === "not-a-feed" || r.status === "empty")) continue;
      if (dropDorm && r.status === "dormant") continue;
      const url = fixMoved && r.newUrl ? r.newUrl : r.feed;
      lines.push(`    <outline type="rss" text="${xesc(r.title)}" title="${xesc(r.title)}" xmlUrl="${xesc(url)}"${r.site ? ` htmlUrl="${xesc(r.site)}"` : ""}/>`);
    }
    lines.push("  </body>", "</opml>");
    return lines.join("\n");
  }

  goBtn.addEventListener("click", async () => {
    if (running) return;
    let text = inp.value.trim();
    if (!text) { stat.textContent = "paste OPML or feed URLs first"; return; }
    // single URL → fetch it as the input document
    if (/^https?:\/\/\S+$/.test(text) && !text.includes("<")) {
      stat.textContent = "fetching input document…";
      try { text = (await workerFetch(text)).text; }
      catch (e) { stat.textContent = "fetch failed: " + e.message; return; }
    }
    let entries = entriesFromOpml(text);
    if (!entries) {
      // fall back to one-feed-URL-per-line
      entries = text.split("\n").map((l) => l.trim()).filter((l) => /^https?:\/\//.test(l))
        .map((feed) => ({ title: feed, feed, site: "" }));
      if (!entries.length) { stat.textContent = "couldn't parse — need OPML or feed URLs"; return; }
    }
    const seen = new Set(); entries = entries.filter((e) => !seen.has(e.feed) && seen.add(e.feed));
    if (entries.length > MAX_FEEDS) { stat.textContent = `${entries.length} feeds — capped at ${MAX_FEEDS}`; entries = entries.slice(0, MAX_FEEDS); }
    run(entries);
  });

  stopBtn.addEventListener("click", () => { aborted = true; });

  $("d-load-trendscope").addEventListener("click", async () => {
    stat.textContent = "loading trendscope security lane OPML…";
    try {
      const r = await fetch("../data/opml/sec.opml");
      inp.value = await r.text();
      stat.textContent = "loaded — hit Run health check";
    } catch (e) { stat.textContent = "failed: " + e.message; }
  });

  $("d-dl").addEventListener("click", () => {
    const blob = new Blob([buildFixedOpml()], { type: "text/x-opml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "subscriptions-fixed.opml"; a.click();
    URL.revokeObjectURL(a.href);
  });
  $("d-copy").addEventListener("click", async () => {
    await navigator.clipboard.writeText(buildFixedOpml());
    stat.textContent = "OPML copied";
  });
})();
