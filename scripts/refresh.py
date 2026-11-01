#!/usr/bin/env python3
"""Weekly source checker. Standard library only.
Checks each URL in sources.json politely (robots.txt, 2s delay), hashes the visible text,
and reports changes, hiring keywords, closure phrases and failures.
It NEVER marks a vacancy verified or closed by itself: fetch failures become "needs_recheck",
closure phrases become "closed_signal" for a human to confirm."""
import json, hashlib, re, sys, time, datetime, os, urllib.request, urllib.robotparser, urllib.parse, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "EnergyJobBoardBot/1.0 (personal job-search monitor; weekly, low volume)"
KW = ["graduate", "trainee", "early career", "early careers", "2027", "petroleum", "reservoir", "production engineer", "field engineer", "nigeria", "applications open", "apply now"]
CLOSED = ["no longer accepting", "closed for applications", "applications are closed", "this job is no longer", "position has been filled", "applications have closed"]

def text_of(raw):
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))).strip()

def robots_ok(url):
    p = urllib.parse.urlparse(url)
    if p.scheme == "file":
        return True, ""
    rp = urllib.robotparser.RobotFileParser(f"{p.scheme}://{p.netloc}/robots.txt")
    try:
        rp.read()
    except Exception as e:
        return False, f"robots.txt unreachable ({type(e).__name__}); skipped to stay polite"
    return (rp.can_fetch(UA, url), "" if rp.can_fetch(UA, url) else "disallowed by robots.txt")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        code = getattr(r, "status", 200)
        return code, r.read(2_000_000).decode("utf-8", "replace"), r.geturl()

def check(s, prev):
    out = {"id": s["id"], "employer": s["employer"], "url": s["url"], "provenance": s.get("provenance", ""), "checked_utc": now()}
    ok, why = robots_ok(s["url"])
    if not ok:
        out.update(result="needs_recheck", reason=why); return out
    try:
        code, raw, final = fetch(s["url"])
    except Exception as e:
        out.update(result="needs_recheck", reason=f"fetch failed: {type(e).__name__}: {e}"); return out
    t = text_of(raw); low = t.lower()
    h = hashlib.sha256(t.encode()).hexdigest()
    kws = [k for k in KW if k in low]
    out.update(http=code, final_url=final, text_len=len(t), hash=h, keywords=kws,
               closed_signal=[c for c in CLOSED if c in low])
    if final.split("/")[2:3] != s["url"].split("/")[2:3]:
        out["redirected_to_other_host"] = True   # possible impersonation or site move: human must look
    if len(t) < 500:
        out["js_rendered_suspected"] = True       # content probably loads by script; cannot be read automatically
    if not prev:
        out["result"] = "baseline"
    elif prev.get("hash") != h:
        out["result"] = "changed"; out["new_keywords"] = [k for k in kws if k not in prev.get("keywords", [])]
    else:
        out["result"] = "unchanged"
    return out

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    sp = os.environ.get("SOURCES", os.path.join(ROOT, "sources.json"))
    dd = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))
    rd = os.environ.get("REPORT_DIR", os.path.join(ROOT, "reports"))
    sources = json.load(open(sp))
    state = json.load(open(f"{dd}/state.json")); log = json.load(open(f"{dd}/log.json"))
    res = []
    for s in sources:
        r = check(s, state.get(s["id"])); res.append(r)
        if r["result"] in ("baseline", "changed", "unchanged"):
            state[s["id"]] = {"hash": r["hash"], "keywords": r["keywords"], "last_ok": r["checked_utc"]}
        if not s["url"].startswith("file:"):
            time.sleep(2)
    n_ok = sum(r["result"] in ("baseline", "changed", "unchanged") for r in res)
    status = {"last_run_utc": now(), "checked": len(res), "ok": n_ok, "failed": len(res) - n_ok,
              "changed": sum(r["result"] == "changed" for r in res), "sources": {r["id"]: r for r in res}}
    json.dump(status, open(f"{dd}/status.json", "w"), indent=1); json.dump(state, open(f"{dd}/state.json", "w"), indent=1)
    log = (log + [{"run": status["last_run_utc"], "ok": n_ok, "failed": status["failed"], "changed": status["changed"]}])[-200:]
    json.dump(log, open(f"{dd}/log.json", "w"), indent=1)
    L = [f"# Weekly digest {status['last_run_utc'][:10]}", "", f"Sources checked: {status['checked']} · read OK: {n_ok} · failed/skipped: {status['failed']} · changed: {status['changed']}", ""]
    def sect(title, rows):
        L.append(f"## {title}")
        L.extend(rows or ["- none"]); L.append("")
    sect("Changed pages (open and read them; a change is not proof of a new vacancy)", [f"- {r['employer']}: {r['url']} (new keywords: {', '.join(r.get('new_keywords', [])) or 'none'})" for r in res if r["result"] == "changed"])
    sect("Closure phrases seen (human must confirm; never auto-closed)", [f"- {r['employer']}: {', '.join(r['closed_signal'])}" for r in res if r.get("closed_signal")])
    sect("Needs recheck (failures are NOT evidence of closure)", [f"- {r['employer']}: {r['reason']}" for r in res if r["result"] == "needs_recheck"])
    sect("Cannot be read automatically (script-rendered page): check by hand", [f"- {r['employer']}: {r['url']}" for r in res if r.get("js_rendered_suspected")])
    sect("Redirected to a different host: inspect before trusting", [f"- {r['employer']}: {r['url']} → {r['final_url']}" for r in res if r.get("redirected_to_other_host")])
    L.append("## Actions\n- Open each changed page, confirm any vacancy on the employer’s own site, then update the board.\n- Never apply through a link received by message or email.")
    open(f"{rd}/digest-{status['last_run_utc'][:10]}.md", "w").write("\n".join(L))
    print(f"checked {len(res)}, ok {n_ok}, failed {status['failed']}, changed {status['changed']}")
    if n_ok == 0:
        sys.exit(1)   # total failure turns the Action red so you are told

if __name__ == "__main__":
    main()
