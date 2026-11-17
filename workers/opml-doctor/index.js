// opml-doctor — server-side feed fetch proxy for the OPML health-check tool.
// GET /?u=<feed-url> → streams back the feed with CORS + diagnostic headers.
// Free tier: 100k req/day. Deploy: npx wrangler deploy (needs CLOUDFLARE_ACCOUNT_ID + CF_API_KEY + CF_EMAIL).

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "*",
  "Access-Control-Expose-Headers": "X-Remote-Status, X-Final-Url, X-Error",
};

function j(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const u = new URL(request.url);
    const target = u.searchParams.get("u");
    if (!target || !/^https?:\/\/[^\s]+$/i.test(target)) {
      return j({ error: "pass ?u=<http(s) url>" }, 400);
    }
    let host;
    try { host = new URL(target).hostname; } catch { return j({ error: "bad url" }, 400); }
    // block obvious internal targets
    if (/^(localhost|127\.|10\.|192\.168\.|169\.254\.|0\.0\.0\.0|\[?::1)/.test(host)) {
      return j({ error: "not allowed" }, 403);
    }
    const RETRYABLE = new Set([429, 502, 503, 520, 522, 525, 526, 527]);
    const UAS = [
      "opml-doctor/1.0 (+https://trendscope.zalize.com/tools/doctor)",
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36 opml-doctor/1.0",
      "FeedFetcher-Google; (+http://www.google.com/feedfetcher.html)",
    ];
    let resp;
    try {
      for (let attempt = 0; ; attempt++) {
        resp = await fetch(target, {
          redirect: "follow",
          headers: {
            "User-Agent": UAS[Math.min(attempt, UAS.length - 1)],
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
          },
          cf: { timeout: 10000, cacheTtl: attempt === 0 ? 300 : 0 },
        });
        if (!RETRYABLE.has(resp.status) || attempt >= 2) break;
        // burst-limited upstream (e.g. substack 429 wave): back off and retry
        // with a different UA + fresh edge colo chance
        await new Promise(r => setTimeout(r, 1200 + Math.random() * 1500));
      }
    } catch (e) {
      return new Response("", {
        status: 200,
        headers: { ...CORS, "X-Remote-Status": "0", "X-Final-Url": target, "X-Error": String(e && e.message || e).slice(0, 200) },
      });
    }
    const buf = await resp.arrayBuffer();
    const body = buf.byteLength > 2_000_000 ? buf.slice(0, 2_000_000) : buf;
    return new Response(body, {
      status: 200,
      headers: {
        ...CORS,
        "Content-Type": resp.headers.get("content-type") || "text/plain; charset=utf-8",
        "X-Remote-Status": String(resp.status),
        "X-Final-Url": resp.url,
      },
    });
  },
};
