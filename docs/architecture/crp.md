# CRP — Creative Resource Planning

**Status:** Layers 1–4 implemented, 100 tests passing, unverified in production
**Last updated:** 2026-08-07
**Scope:** architecture + strategy for the AI-native creative ERP
**Canonical name in code:** `CRP` · aliases: `CARP`, `ARP`

---

## 0. Naming

ERP = **E**nterprise **R**esource **P**lanning. The earlier working name
"ECRP — Enterprise Creative Resource Planning" doubled the *Enterprise*
that ERP already carries. Corrected.

| Name | Expansion | Status | Notes |
|---|---|---|---|
| **CRP** | Creative Resource Planning | **canonical** | Used in class names, filenames, docs. No major collision. Reads cleanly beside ERP and CRM. |
| CARP | Creative Agency Resource Planning | alias | Most literal about who this serves. Two collisions to weigh before external use: *to carp* means to complain or nag, and CARP is the Common Address Redundancy Protocol. |
| ARP | Agency Resource Planning | alias | Phonetically closest to ERP, but engineers read ARP as Address Resolution Protocol first. |

All three resolve in code — `CRPRuntime`, `CARPRuntime`, `ARPRuntime` are the
*same class object*, not subclasses, so `isinstance()` holds across every name
and there is one implementation to maintain. `ECRPRuntime` is retained as a
deprecated alias. Locked by `TestCategoryAliases`.

**Why "Creative" and not "Agency" in the canonical name:** *agency* describes
your first market, not the category. In-house brand studios, production
companies, publishers, and media teams have the same problem and would not
buy something whose name says it is for someone else. Naming the category
after one customer segment caps the story before the second segment exists.

---

## 1. Position

AGENCY OS is not "an AI SaaS for agencies." It is an **AI-native creative ERP**:
creative production, business operations, organizational memory, autonomous
agents, and enterprise governance on one foundation.

That framing is correct. But framing is not a moat, and it is worth being
precise about which parts of this are defensible and which are not.

### What is actually defensible

| Component | Defensibility | Why |
|---|---|---|
| **Creative Object graph** | **High** | Accumulates per-tenant. Years of decisions, lineage, and outcomes. Cannot be copied, only re-earned. This is the product. |
| Governance layer | Medium | Table stakes for enterprise, but the *default policy set* encodes agency-specific domain knowledge competitors lack. |
| AI Ops ledger | Low–Medium | Easy to build, but nobody has, and it sells immediately. Land-grab, not moat. |
| Module renames (Creative Inventory, Content Factory) | **~Zero** | SAP renames a screen and ships in a quarter. |
| Vertical production workflows | Low | Configuration, not architecture. |
| Predictive layer | Deferred | Requires the graph plus labelled outcomes. Cannot lead. |

**Strategic consequence:** every roadmap decision should be judged by whether
it deepens the graph. Features that produce CRUD rows are cost; features that
produce edges and outcome labels are compounding assets.

### Category risk

"Creative ERP" as a name is claimable by any incumbent within two quarters.
Do not defend the name. Defend the data structure and the switching cost it
creates. A tenant three years into AGENCY OS has an institutional memory that
does not export.

---

## 2. Layer map

```
┌──────────────────────────────────────────────────────────────┐
│  L6  PREDICTION          (deferred — needs L1 + labels)      │
├──────────────────────────────────────────────────────────────┤
│  L5  AGENCY DIGITAL TWIN (deferred — derived from L1)        │
├──────────────────────────────────────────────────────────────┤
│  L4  CRP RUNTIME         runtime.py     ✅ implemented        │
│      the chokepoint · Intent → gate → meter → graph → audit  │
│      consumers: workflows/engine.py                          │
├──────────────────────────────────────────────────────────────┤
│  L3  GOVERNANCE          governance.py  ✅ implemented        │
│      policy engine · approval gates · hash-chained audit     │
├──────────────────────────────────────────────────────────────┤
│  L2  AI OPERATIONS       aiops.py       ✅ implemented        │
│      rate card · call ledger · budgets · agent scorecards    │
├──────────────────────────────────────────────────────────────┤
│  L1  CREATIVE OBJECTS    creative.py    ✅ implemented        │
│      typed graph · lifecycle SM · provenance · signals       │
├──────────────────────────────────────────────────────────────┤
│  L0  CLASSIC ERP         erp.py / core.py  (pre-existing)    │
│      CRM · finance · HR · procurement · projects · RBAC      │
└──────────────────────────────────────────────────────────────┘
```

L0 is not replaced. Invoices are still invoices. L1 sits *beside* it and joins
via `client_id` / `project_id` / `campaign_id`.

---

## 3. Layer 1 — Creative Object Model

`aurora/enterprise/creative.py`

### Design decisions worth defending

**Objects carry `signals`, not scores.** A `quality_score: float` is a lie with
a decimal point. Instead:

```python
obj.set_signal("brand_fit", 0.54, source="agent:qa", confidence=0.8)
# -> {"value": 0.54, "source": "agent:qa", "confidence": 0.8,
#     "at": "...", "previous": 0.71}
```

Every judgement keeps its author, its confidence, its timestamp, and the value
it displaced. When a client disputes a call, the record answers.

**The lifecycle is a real state machine.** `TRANSITIONS` declares legal moves;
everything else raises `TransitionError`. A free-text `status` column cannot
produce bottleneck analytics — a state machine can, because every hop emits a
`StageEvent` with a measured duration.

```python
graph.bottlenecks(org_id)
# {"review": {"mean_seconds": 184000, "max_seconds": 402000, "samples": 37}}
```

This is what makes "observable, measurable, improvable" true rather than a
slide.

**Agents cannot self-advance gated stages.** `APPROVAL`, `PRODUCTION`, and
`DELIVERY` reject `ActorType.AGENT` unless the caller passes `allow_gated=True`
after clearing L3. Autonomy stops where consequence starts.

**Provenance spans the whole ancestry.** `provenance()` walks the full
`DERIVED_FROM` chain, not just the current fork. A v3 approved by one director
still names everyone who shaped v1 and v2. Anything narrower is a liability in
an IP dispute.

**AI involvement is inherited on fork.** Human editing on top of generated work
remains AI-assisted for disclosure purposes. `ai_generated` never launders
itself away through a version bump.

### Object model

- **25 `ObjectKind`s** — idea → learning, plus brand DNA, design system, campaign
- **13 `EdgeType`s** — including `FULFILLS` (deliverable → brief), `RESPONDS_TO`
  (revision → review), `MEASURES` (result → deliverable), `TEACHES`
  (learning → future work)
- **16 `Stage`s** — the creative supply chain, including `KILLED` (dead ideas
  are data; most systems throw them away and lose the negative examples)
- `inferred: bool` on every edge separates asserted truth from machine guesses.
  Never let the two contaminate each other.

### Scope honesty

Reference implementation is in-memory with JSON persistence and stdlib only.
It is the **schema of record**, not the production store. Postgres + pgvector
or Neo4j swaps in behind the same method surface. `aurora/memory/graph.py`
(ChromaDB + NetworkX) is the *semantic projection* of this model, not a
competing one — they must be reconciled before either scales.

---

## 4. Layer 2 — AI Operations

`aurora/enterprise/aiops.py`

The cheapest module here and the fastest to sell. No ERP tracks this today.

### The actual insight

Agencies are eating model cost as undifferentiated overhead. It is cost of
goods sold, and it is billable. `margin()` puts it on the P&L:

```python
ledger.margin(org_id, "prj_1", revenue_usd=42000, labor_cost_usd=18500)
# {"gross_margin": 0.5595, "ai_share_of_cogs": 0.0000, ...}
```

### Design decisions worth defending

**Unknown models are never priced by guess.** `RateCard.price()` returns
`(0.0, False)` and the call records `priced=False`. Silent estimation would
poison every downstream margin number. Unpriced models surface in `spend()`.

**`attribution_gap()` is a self-audit.** It reports the share of spend that
cannot be traced to a client. A high number means the ledger is decorative —
fix instrumentation before trusting any margin figure it produces.

**Scorecards report `review_coverage` next to `acceptance_rate`.** A 100%
acceptance rate over 3 reviewed calls out of 4000 is noise. The data shape
says so rather than flattering the agent.

**Prompts are hashed, never stored.** `prompt_hash` only. PII discipline at
the schema level, not the policy level.

**Budgets can hard-stop.** `BudgetExceeded` raises *before* the call is
appended. Runaway agent loops are a cost incident, not a bug report.

### Rate card caveat

`RateCard.DEFAULTS` are **placeholders**, explicitly marked `note="placeholder"`.
Verify against current provider pricing before invoicing a client off these
numbers. Rates are versioned (`effective_from`) so historical costs stay
reproducible after a price change.

---

## 5. Layer 3 — Governance

`aurora/enterprise/governance.py`

Governance is the enterprise sale. Intelligence gets the demo; governance gets
the signature.

### Design decisions worth defending

**Adjudication is deterministic.** An LLM never decides whether an action is
permitted. It may only *propose* actions the engine then judges against pure
predicates. Non-deterministic authorization is not authorization.

**A broken rule fails closed.** If a policy's `condition` raises, `applies()`
returns `True` — the rule engages rather than silently permitting the action.

**Explicit strictness ordering.** `_STRICTNESS` ranks effects; `DENY`
short-circuits. Precedence is declared, not an artifact of iteration order.

**Every decision is explainable by construction.** `Decision.explanation`
names the blocking policy, its severity, and its rationale. Not a post-hoc
summarization step that can drift from the logic.

**Self-approval is blocked. Role is checked. Approvals expire.** All three are
enforced in `decide()`, each emitting its own audit event on refusal. Stale
approvals rot; 72h default TTL.

### Default policy set

Eight shipped policies, each encoding a real way agencies get burned:

| Policy | Effect | Priority |
|---|---|---|
| Agents may not delete | DENY | 1000 |
| PII must not leave the tenant | DENY | 1000 |
| Client IP may not train models | REQUIRE_APPROVAL | 980 |
| Client-facing AI output needs sign-off | REQUIRE_APPROVAL | 900 |
| Off-brand work cannot ship (`brand_fit < 0.6`) | REQUIRE_APPROVAL | 600 |
| Expensive runs (`> $50`) | REQUIRE_APPROVAL | 500 |
| Accessibility floor (WCAG 2.1 AA) | ALLOW_WITH_CONDITIONS | 400 |
| AI disclosure on delivery | ALLOW_WITH_CONDITIONS | 300 |

Action patterns support suffix globs (`*.delete`) because verb-scoped rules are
the highest-value class and must not be rewritten per resource type.

### Audit chain — honest limits

SHA-256 hash chain, `verify()` walks it and reports the first break.
**This is tamper-evident, not tamper-proof.** Anyone with write access can
recompute the entire chain. Real immutability needs an external anchor: WORM
storage, or periodic publication of `head()` to a third-party notary. `head()`
exists for exactly that purpose. Do not oversell this in a security review.

### Enforcement caveat

The engine is a chokepoint only if callers route through it. Nothing in
`governance.py` can enforce its own use. That wiring is Layer 4.

---

## 5a. Layer 4 — CRP Runtime (the chokepoint)

`aurora/enterprise/runtime.py`

Layers 1–3 are libraries, and a library callers may bypass is not a control.
The runtime is the single path through which consequential actions pass:

```python
result = await runtime.execute(intent, handler)
```

One call performs, in fixed order: policy evaluation → approval check →
budget preflight → handler invocation → metering → graph mutation → audit
append. Steps 1–3 and 5–7 cannot be skipped by a caller holding only
`execute()`. That is the whole design.

### Design decisions worth defending

**The handler never runs if governance blocks.** Verified by test: on `DENY`
and on `AWAITING_APPROVAL`, the handler callable is not invoked. A control
that evaluates policy *after* doing the work is an audit log, not a control.

**Budget blocks before compute is spent, not after.** Preflight checks the
projected cost against hard-stop budgets before the handler is called.

**Signals are read from the graph, never trusted from the caller.** A caller
that could assert its own `brand_fit` would bypass the brand policy by lying.
`_to_context()` reads `brand_fit` and `accessibility` off the stored object.

**`strict_mode` denies unknown actions.** An allow-by-default authorization
system is not an authorization system. Off in development, on in production.

**Intent drift is a governance event.** If a handler reports usage
contradicting what the Intent declared (`actual_ai_generated=True` against a
declared `False`), the runtime writes a `governance.misdeclaration` audit
event and flags the ledger call. Misdeclaration is detected, not trusted.

**`health()` self-audits the control plane.** `unmetered_actions` and the
attribution gap make a half-wired integration visible rather than letting it
degrade silently into the theatre this layer exists to prevent.

**Failures are values, not exceptions.** `Result.state` is authoritative;
`unwrap()` exists for callers who prefer fail-fast. An illegal stage
transition returns `FAILED` with the stage unmoved, rather than raising
through the caller's control flow.

---

## 5b. Workflow engine — repairs

`aurora/workflows/engine.py`

Auditing the execution path for phase 4 turned up four defects, all of which
made the system *look* safer than it was:

| Defect | Impact | Fix |
|---|---|---|
| **Approval gate did not halt** — set `waiting_for_approval = True` then kept executing children | Every downstream node, including `Publish`, ran before anyone approved anything. Worse than no gate: it appears in the audit log as one. | Handlers return `{"suspend": True}`; the run halts, persists its frontier, and is resumable only after `gov.is_cleared()` |
| **No cycle detection, recursive walk** | A cyclic workflow recursed until the stack died | DFS three-colour cycle detection at validate *and* execute time; iterative frontier walk with a step limit |
| **`load()` stored raw dicts** | Loaded workflows were dicts pretending to be `Workflow`; every subsequent method call failed on attribute access | `from_dict` on both `Workflow` and `WorkflowNode`, verified by round-trip test |
| **`create_campaign_workflow` was `@staticmethod`** | Built the workflow inside a throwaway engine, so `execute()` on the returned object always returned "Workflow not found" | Instance method registering into `self.workflows` |

Two further hardening changes:

- **Conditions no longer use `eval`.** Workflow definitions are user-authored
  content; `eval` on them is remote code execution with extra steps.
  `_safe_condition` implements a deliberately tiny grammar — one comparison,
  optional `and`/`or`, no attribute access, no calls. Tested against
  `__import__('os').system(...)` and class-hierarchy escapes.
- **Approvals are tracked per node, not per execution.** A regression test
  (`test_two_gates_require_two_approvals`) covers the bug found during this
  work: clearing gate 1 satisfied gate 2, because clearance was tracked on
  the execution rather than the node.

An approval node with no runtime attached now **blocks** rather than passing.
Refusing to run is the correct behaviour for an ungoverned gate.

---

## 6. Two positions I'd argue against in the original brief

### "Creative Fingerprint / Creative DNA" per employee

The highest-risk item proposed. Scoring individuals on "weaknesses" and
"productivity", stored durably and fed to staffing decisions, is:

- **GDPR Art. 22** — automated decision-making with legal or similarly
  significant effect on a person
- **EU AI Act** — employment-context scoring is a high-risk classification
- A culture problem that will leak and damage trust internally

**Recommended reframe:** team-level capability mapping, opt-in, individual
opt-out without penalty, no durable negative scores, and never an input to
compensation or termination. Same staffing benefit, survivable legal posture.

Deliberately **not implemented** in this pass.

### Predictive claims before the graph exists

"82% churn probability" without years of labelled outcomes is a confident
random number generator. The sequence must be:

1. Build the graph (L1) ✅
2. Log outcomes and human judgements (L2 `annotate()`, L1 `signals`) ✅
3. Accumulate 18–36 months of labelled data ⏳
4. *Then* predict

Shipping step 4 first produces plausible nonsense, and enterprise buyers
eventually check. `AIERPLayer` in `ai_erp.py` currently contains heuristic
stubs — they should be labelled as heuristics in the UI, not as predictions.

---

## 7. Sequencing

| Phase | Work | Status |
|---|---|---|
| **1** | Creative Object graph + lifecycle | ✅ done |
| **2** | AI Ops metering | ✅ done |
| **3** | Governance subsystem | ✅ done |
| **4** | Runtime chokepoint + workflow wiring | ✅ done |
| **5** | **Wire runtime into `api/server.py` and the agent executor** | ⏳ next, blocking |
| **6** | Reconcile `creative.py` graph with `memory/graph.py` semantic layer | ⏳ |
| **7** | Persistence: JSON → Postgres + pgvector | ⏳ |
| **8** | Agency Digital Twin (derived, read-only over L1) | later |
| **9** | Prediction, once labels exist | later |

Phase 5 is now the blocking item. `runtime.py` is wired into the workflow
engine but **not yet into `aurora/api/server.py` or the agent invocation path
in `aurora/core.py`**. Until every entry point routes through `execute()`, the
control plane has holes, and `health()["unmetered_actions"]` is the instrument
that will show them.

---

## 8. Verification

**100 tests, stdlib `unittest`, no third-party dependencies:**

```bash
python -m unittest tests.test_crp -v
```

Note: the pre-existing `tests/test_agency_os.py` requires `pytest`, which is
not installed in `venv/`. The CRP suite deliberately uses `unittest` so it
runs without adding a dependency.

Coverage by area:

| Area | Approach | Notable cases |
|---|---|---|
| Lifecycle state machine | Table-driven over the full `Stage × Stage` matrix | Every declared transition permitted; **every undeclared one rejected**; no non-terminal dead ends; agents blocked from all gated stages |
| Signals | Example | Provenance and prior-value retention |
| Graph | Example | Full-ancestry provenance, AI-flag inheritance on fork, org isolation, enum + history rehydration |
| Rate card | Example | Token/per-call/GPU arithmetic; unknown models never guessed |
| Ledger | Example | Hard-stop blocks *before* append; scoped budgets; coverage reported beside acceptance |
| Policy matching | Table-driven over glob semantics | `*`, `asset.*`, `*.delete`, exact; `asset.publishing` must not match `asset.publish` |
| Policy engine | Example | DENY beats approval; strictest-wins regardless of priority order; **broken condition fails closed**; tenant isolation |
| Approvals | Example | Self-approval, wrong role, double decision, expiry — all blocked |
| Audit chain | Example | Content tamper, deletion, and reordering all detected |
| Runtime | Example | Handler not invoked on deny or gate; budget blocks before compute; signals read from graph not caller; misdeclaration flagged |
| Condition grammar | Table-driven | Comparison ops, `and`/`or`, missing fields; **injection attempts return False rather than executing** |
| Workflow | Example | Gate suspends; resume refused without clearance; two gates need two approvals; cycle refused; persistence rehydrates real objects |
| Category aliases | Example | `CARP`/`ARP`/`ECRP` are the same class as `CRP`; `isinstance` holds; an aliased instance enforces governance identically |

### Known gaps

- No concurrency tests. The runtime is not thread-safe; the ledger and graph
  use plain dicts and lists. Single-process assumption must be documented or
  removed before horizontal scaling.
- No property-based / fuzz testing of `_safe_condition`. The grammar is small
  enough to audit by eye, but hostile input deserves a fuzzer.
- Rate-card figures are placeholders; no test asserts their correctness
  because correctness is a provider-pricing question, not a code question.
