
import os, sys, json, re, time, traceback
from pathlib import Path
from openai import OpenAI

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"input"
OUT=ROOT/"results"
OUT.mkdir(exist_ok=True)

KEY=os.getenv("OPENROUTER_API_KEY")
MODEL=os.getenv("OPENROUTER_MODEL","openai/gpt-oss-20b:free")
if not KEY:
    print("ERROR: OPENROUTER_API_KEY is not configured.")
    sys.exit(2)

# Load the original JSON containing the actual LLM-generated B/closed-loop code.
candidates=list(INPUT.glob("representative_experiment*.json"))
orig=None
for p in candidates:
    try:
        d=json.loads(p.read_text(encoding="utf-8"))
        if "results" in d and "B" in d["results"]:
            orig=d
            break
    except Exception:
        pass
if orig is None:
    print("ERROR: Original representative_experiment.json not found in input.")
    sys.exit(2)

text=orig["results"]["B"]["closed_loop"]["attempts"][0]["llm"]["text"]
m=re.search(r"===\s*FILE:\s*app\.py\s*===",text,re.I)
if not m:
    print("ERROR: Could not locate app.py block.")
    sys.exit(2)
tail=text[m.end():]
f=re.search(r"```(?:python|py)?\s*\n(.*?)```",tail,re.I|re.S)
current=(f.group(1) if f else tail).strip()+"\n"

# The verified V3.1 failure: syntax error at line 30.
failure={
    "failure_type":"execution_error",
    "error":"SyntaxError: unterminated string literal at line 30",
    "context":"The generated B/closed-loop application failed to import before behavioral tests could execute.",
    "required_behavior":"Preserve the same 8 behavioral checks used in V3.1."
}

system="""You are performing a controlled repair experiment for legacy Web migration.
Repair ONLY the verified syntax/execution defect in the supplied Flask application.
Do not redesign the application. Preserve all externally observable behavior:
routes, HTTP methods, status codes, JSON fields/values, CRUD semantics, and the
existing /health and /items behavior.
Return ONLY:
=== FILE: app.py ===
```python
<complete corrected app.py>
```
The output must be complete and syntactically valid Python. Do not add commentary."""

user=f"""VERIFIED FAILURE:
{json.dumps(failure,indent=2)}

CURRENT GENERATED APPLICATION:
{current}
"""

print("Starting V3.2: exactly ONE repair request...")
client=OpenAI(base_url="https://openrouter.ai/api/v1",api_key=KEY,timeout=90)
start=time.time()
try:
    r=client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0,
        max_tokens=5000
    )
except Exception as e:
    print("API ERROR:",repr(e))
    print("STOP. No retry was performed.")
    sys.exit(1)

elapsed=time.time()-start
usage=getattr(r,"usage",None)
usage_obj=None if usage is None else {
    "prompt_tokens":getattr(usage,"prompt_tokens",None),
    "completion_tokens":getattr(usage,"completion_tokens",None),
    "total_tokens":getattr(usage,"total_tokens",None)
}
reply=r.choices[0].message.content or ""

m=re.search(r"===\s*FILE:\s*app\.py\s*===",reply,re.I)
if not m:
    print("ERROR: Repair response did not contain app.py block.")
    sys.exit(1)
tail=reply[m.end():]
f=re.search(r"```(?:python|py)?\s*\n(.*?)```",tail,re.I|re.S)
code=(f.group(1) if f else tail).strip()+"\n"

artifact=ROOT/"results"/"B_closed_loop_repaired_attempt_2.py"
artifact.write_text(code,encoding="utf-8")

# Same 8 V3.1 behavioral tests, unchanged.
def evaluate(path):
    import importlib.util
    spec=importlib.util.spec_from_file_location("v32_repaired",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    app=getattr(mod,"app",None)
    if app is None: raise AssertionError("No module-level app")
    app.config["TESTING"]=True
    def c(): return app.test_client()
    checks=[]
    x=c()
    r=x.get("/health"); checks.append(("health",r.status_code==200 and r.get_json()=={"status":"ok"}))
    r=x.get("/items"); checks.append(("initial_items",r.status_code==200 and r.get_json()=={"items":[{"id":1,"name":"Alpha","qty":2},{"id":2,"name":"Beta","qty":5}]}))
    r=x.get("/items/1"); checks.append(("get_item",r.status_code==200 and r.get_json()["name"]=="Alpha"))
    r=x.get("/items/99"); checks.append(("missing_item",r.status_code==404 and r.get_json()=={"error":"not_found"}))
    r=x.post("/items",json={"name":"Gamma","qty":3}); checks.append(("create_item",r.status_code==201 and r.get_json()["name"]=="Gamma"))
    nid=(r.get_json() or {}).get("id")
    r=x.put(f"/items/{nid}",json={"name":"Gamma2","qty":4}); checks.append(("update_item",r.status_code==200 and r.get_json()["name"]=="Gamma2" and r.get_json()["qty"]==4))
    checks.append(("delete_item",x.delete(f"/items/{nid}").status_code==204))
    checks.append(("deleted_item",x.get(f"/items/{nid}").status_code==404))
    passed=sum(v for _,v in checks)
    return {"pass":passed==8,"passed":passed,"total":8,
            "checks":[{"name":n,"passed":bool(v)} for n,v in checks]}

try:
    evaluation=evaluate(artifact)
except Exception as e:
    evaluation={"pass":False,"passed":0,"total":8,
                "failure_type":"execution_error",
                "error":repr(e),
                "traceback":traceback.format_exc()}

result={
    "experiment":"v3.2_closed_loop_repair",
    "model":MODEL,
    "llm_requests":1,
    "repair_elapsed_seconds":elapsed,
    "usage":usage_obj,
    "verified_failure_before_repair":failure,
    "repair_evaluation":evaluation,
    "artifact":artifact.name
}
out=OUT/"v32_closed_loop_repair_result.json"
out.write_text(json.dumps(result,indent=2),encoding="utf-8")
print()
print("==============================================")
print("V3.2 CLOSED-LOOP REPAIR COMPLETE")
print("==============================================")
print("LLM requests made: 1")
print("Repair evaluation:", evaluation["passed"], "/", evaluation["total"])
print("Result:", out)
print("Upload this JSON here.")
