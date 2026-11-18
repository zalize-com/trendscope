import asyncio
import json

# Demand-mining swarm, round 4.
# Orchestrator (this script) fans out 6 corpus miners in parallel, then a
# synthesizer clusters every hit into demand themes (>=10 mentions = buildable).

FRICTION = (
    'title or comment expressing an unmet need: "wish there was", "is there a tool", '
    '"looking for", "how do you deal with", "annoyed/frustrated by", "I built this because", '
    '"why isn\'t there", "am I the only one", requests for software/tool/app recommendations'
)

MINER_PROMPT = """You are a demand-mining agent. Mine ONE corpus for real, unmet software/tool needs stated by actual users.

Corpus: {corpus}

Method (be resourceful; if a source blocks you, try alternate endpoints/mirrors rather than giving up):
{method}

Extract only items where a person clearly states an unmet need matching these friction patterns:
{f}

Rules:
- Real user needs only, not product announcements or general complaints about a company.
- Return at most 30 hits. Fewer is fine; zero is a valid honest result.
- For each hit: url, title (or thread title), a short verbatim quote proving the need, and a one-line pain summary.
- In `notes`, report what you actually tried and coverage (e.g. how many threads scanned, what got blocked).

Structured output required."""

CORPORA = [
    {
        "name": "hackernews_titles",
        "corpus": "Hacker News Ask HN threads from the last ~30 days that ask for tools.",
        "method": (
            "Use the free Algolia API, e.g.\n"
            "  curl -s 'https://hn.algolia.com/api/v1/search?tags=ask_hn&hitsPerPage=100'\n"
            "and add query params like query=tool%20OR%20looking%20for%20OR%20wish.\n"
            "Then fetch promising threads via\n"
            "  curl -s 'https://hn.algolia.com/api/v1/items/<objectID>'\n"
            "and scan top comments for stated needs (not just the title)."
        ),
    },
    {
        "name": "devto_discussion",
        "corpus": "dev.to discussion/watercooler posts and their comment sections.",
        "method": (
            "Free API: curl -s 'https://dev.to/api/articles?top=30&per_page=50' plus\n"
            "'https://dev.to/api/articles?tag=discuss&per_page=50' and tag=watercooler,productivity,webdev.\n"
            "For promising articles fetch comments: 'https://dev.to/api/comments?a_id=<id>'.\n"
            "Look for threads where someone asks what tool solves X."
        ),
    },
    {
        "name": "reddit_indie",
        "corpus": "r/SaaS, r/webdev, r/indiehackers, r/sideproject hot/top threads asking for tools.",
        "method": (
            "Try in order until one works: old.reddit.com/r/<sub>/top.json?t=month with a browser-ish\n"
            "User-Agent; www.reddit.com .json; if all 403/429 use search engines\n"
            "(web_search tool) for 'site:reddit.com r/<sub> looking for tool' and open threads that surface.\n"
            "Report which path worked in notes."
        ),
    },
    {
        "name": "v2ex",
        "corpus": "V2EX Chinese forum — 酷工作区 / 分享发现 / 问与答 nodes.",
        "method": (
            "Try curl https://www.v2ex.com/api/topics/hot.json and node pages like\n"
            "https://www.v2ex.com/go/creative and /go/qna (HTML scrape is fine).\n"
            "Look for Chinese posts like 有没有一个工具/求推荐/大家都用什么做X. Translate pains to English summaries."
        ),
    },
    {
        "name": "lobsters",
        "corpus": "Lobste.rs ask stories and comments.",
        "method": (
            "JSON: curl https://lobste.rs/t/ask.json and /newest.json.\n"
            "Fetch comments via https://lobste.rs/s/<short_id>.json for promising threads.\n"
            "Dev community — needs tend to be technical (devtools, ops, infra)."
        ),
    },
    {
        "name": "producthunt_indie",
        "corpus": "ProductHunt discussions + IndieHackers-like public threads.",
        "method": (
            "producthunt.com frontpage/discussions may need a browser; try web_search tool for\n"
            "'site:producthunt.com looking for' and recent discussion URLs, then open pages.\n"
            "If PH is hard-blocked, fall back to indiehackers.com forum pages via search.\n"
            "Report honestly what was reachable in notes."
        ),
    },
]

MINER_SCHEMA = {
    "type": "object",
    "properties": {
        "hits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "quote": {"type": "string"},
                    "pain": {"type": "string"},
                },
                "required": ["url", "title", "quote", "pain"],
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["hits", "notes"],
}

SYNTH_SCHEMA = {
    "type": "object",
    "properties": {
        "clusters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "count": {"type": "integer"},
                    "buyer": {"type": "string"},
                    "verdict": {"type": "string"},
                    "examples": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["theme", "count", "buyer", "verdict", "examples"],
            },
        },
        "report_md": {"type": "string"},
        "recommendation": {"type": "string"},
    },
    "required": ["clusters", "report_md", "recommendation"],
}


async def mine(c):
    try:
        return await agent(
            MINER_PROMPT.format(corpus=c["corpus"], method=c["method"], f=FRICTION),
            phase="mine",
            schema=MINER_SCHEMA,
            label=c["name"],
        )
    except WorkflowAgentError as e:
        log(f"miner {c['name']} failed: {e}")
        return {"hits": [], "notes": f"agent failed: {e}"}


async def main():
    await register_workflow({
        "name": "demand-mining-swarm-r4",
        "description": "Round-4 demand mining: 6 parallel corpus miners -> cluster synthesizer",
        "product": "trendscope / product pipeline",
        "soft_time_limit_minutes": 25,
        "phases": [
            {"title": "mine", "detail": "one miner per corpus, parallel",
             "labels": [c["name"] for c in CORPORA]},
            {"title": "synthesize", "detail": "cluster all hits into demand themes", "count": 1},
        ],
    })
    log(f"fan-out: {len(CORPORA)} corpus miners")
    results = await parallel([lambda c=c: mine(c) for c in CORPORA])
    total = sum(len(r["hits"]) for r in results)
    log(f"fan-in: {total} raw hits")
    for c, r in zip(CORPORA, results):
        log(f"  {c['name']}: {len(r['hits'])} hits | {r['notes'][:160]}")

    payload = [
        {"corpus": c["name"], "hits": r["hits"], "notes": r["notes"]}
        for c, r in zip(CORPORA, results)
    ]
    synth = await agent(
        "You are the synthesis stage of a demand-mining swarm. Below are raw mining hits "
        "from 6 corpora, each a stated unmet software need by a real user.\n\n"
        "Tasks:\n"
        "1. Cluster hits into demand themes. Report every theme with >=2 independent hits; "
        "mark which reach the >=10 independent-mentions buildable threshold.\n"
        "2. For each cluster: theme name, hit count, who the buyer is, a verdict "
        "(build / watch / pass with one-line reason, considering that pain-killer-idea "
        "SaaS is a saturated market), and up to 3 example urls.\n"
        "3. Write report_md: a Markdown report 'Demand mining round 4 (swarm)' with a "
        "method paragraph, a per-corpus coverage table, the cluster table, and a bottom-line "
        "recommendation. Tone: honest, terse, data-first.\n"
        "4. recommendation: one paragraph on whether any cluster justifies building product #3.\n\n"
        f"RAW HITS JSON:\n{json.dumps(payload, sort_keys=True)}",
        phase="synthesize",
        schema=SYNTH_SCHEMA,
        label="synthesize",
    )
    log("=== CLUSTERS ===")
    for cl in synth["clusters"]:
        log(f"  [{cl['count']}] {cl['theme']} -> {cl['verdict']}")
    log("=== REPORT_MD ===")
    log(synth["report_md"])
    log("=== RECOMMENDATION ===")
    log(synth["recommendation"])


asyncio.run(main())
