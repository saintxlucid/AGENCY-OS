# Agency Operating Model — Dedicated Architectural Layer (FROZEN direction, STAGED build)

North star (locked): governed, AI-native enterprise operating environment modeling people, clients,
work, decisions, resources, finances, knowledge, tools and intelligence as one continuously evolving
institutional system. Loop: PEOPLE→INTENT→WORK→COLLABORATION→DECISION→EXECUTION→RESULT→LEARNING→
INSTITUTIONAL MEMORY→better people/decisions/work. Departments are views; work flowing through
people/clients/intelligence/decisions/constraints is canonical. Substrates evolve, never replaced.

## I. Operating grammar (canonical vocabulary → graph commands)
REQUEST≠BRIEF≠TASK≠JOB≠PROJECT≠CAMPAIGN≠DELIVERABLE≠ASSET≠VERSION≠REVISION≠CHANGE REQUEST≠DECISION≠
APPROVAL≠OUTPUT≠RESULT≠LEARNING. Client message → REQUEST → intent → change-to-deliverable →
scope check → impact → TASK → REVISION → REVIEW → APPROVAL. Natural phrases ("brief this", "another
route", "out of scope", "burn?", "what did we learn?") resolve to graph traversals, never chatbot-only.

## II. Work state machine (per-type templates, executable domain knowledge)
Canonical spine: NEW→INTAKE→TRIAGED→BRIEFING→BRIEFED→STRATEGY→CREATIVE→INTERNAL REVIEW→CLIENT REVIEW→
CHANGES→REVISION→QC→APPROVAL→PRODUCTION→SCHEDULED→PUBLISHED→MONITORING→ANALYSIS→LEARNING→ARCHIVED.
TVC≠social≠pitch≠always-on≠press≠asset: workflow templates per type. Maps to schema TRANSITIONS;
ERP adapters in `erp_bindings.py`.

## III. Rituals as first-class objects (all write graph objects)
Briefing (brief→clarification→interpretation→owner confirm) | Kickoff (objective/team/roles/timeline/
risks/deps/success) | WIP (moving/blocked/late/changed/needs-judgment) | Creative Review
(concept→rationale→eval→feedback→decision) | Client Presentation (narrative→work→objections→response→
decision→next) | Debrief (expected vs actual vs why vs next) | Retrospective
(worked/didn't/unexpected/root/action/owner).

## IV. Meeting→OS engine (major subsystem)
Extract PEOPLE/TOPICS/REQUESTS/DECISIONS/DISAGREEMENTS/ACTIONS/DEADLINES/RISKS/SCOPE/ APPROVALS/
SENTIMENT/OPEN QUESTIONS. Before: Meeting Brief (purpose/decision/attendees/questions/history/actions).
During: Live Copilot (topic/issues/precedent/budget/scope/missing owner). After: Decision Record
(decision/maker/change/why/evidence/version/affected). Rule: transcript = evidence; confirmed decision = truth.

## V. Why-intelligence (causal, not search)
Why exists (asset→concept→strategy→insight→objective)? Why changed (version→feedback→decision→version)?
Why approved (approval→approver→evidence→conditions)? Why late (miss→dependency→approval delay→shift)?
Why cost more (variance→revisions→out-of-scope→change request)? Lineage queries over graph+history.

## VI–IX. Decision ledger, disagreement, assumptions, experiments
Decision {id/subject/type/maker/options/selected/rationale/evidence/assumptions/risks/conditions/
expiry/affected/outcome} linked to performance ("did it work?"). Disagreement preserved
(strategist A vs CD B vs client C → final + rationale → outcome learning). Assumption registry
{audience/assumption/confidence/evidence/status untested→validated}. Experiment engine
{hypothesis/variable/test/audience/control/result/interpretation/learning} auto-available to future work.

## X–XIII. Creative/client memory, stakeholders, health
Creative Memory per brand (winning/failed/rejected concepts, preferences, patterns, sensitivities,
feedback, references, competitors, constraints, learnings) → "similar to 3 rejected directions" guard.
Client Memory (stakeholders, makers/influencers, preferences, style, approval patterns, priorities,
sensitivities, commercial history, health, wins/fails, issues). Stakeholder graph (authority/influence/
sentiment/scope/preference/history) → "commenter isn't final approver". Health composite (relationship,
satisfaction, latency, friction, scope, payment, revenue, margin, engagement, growth, escalations, churn).

## XIV–XVIII. Pulse, weather, nervous system, attention, focus
Account Pulse (initiatives/awaiting/risks/approvals/revenue/unbilled + AI diagnosis, not charts).
Agency Weather (delivery/capacity/health/margin/pipeline/load/AI cost/approvals + drill-down why).
Nervous system events (BriefCreated/Approved, TaskAssigned, AssetVersioned, FeedbackAdded, ScopeChanged,
Approval*, BudgetThreshold, RiskDetected, DeadlineThreatened, Anomaly, LearningValidated, Violation) →
Aurora listens, Sentinel observes, Scribe documents, Operator acts, Sovereign governs.
Attention routing (URGENT/IMPORTANT/WAITING/FYI/DELEGATE/AUTO/IGNORE) + per-role NOW/NEXT/WAITING/DELEGATE/FYI.
Focus Mode (current work bundle; rest queued) attacks context switching.

## XIX–XXII. Handoff, agent perf, router, COGS
Handoff protocol records human/agent/tool/model contributions + owner + approval (accuracy/bias/legal/
privacy barriers addressed structurally). Agent reviews (acceptance, first-pass, revisions, cost/latency,
compliance, hallucination, override → retire/improve/promote). Model Router (task→quality→latency→
classification→budget→capability→route; confidential→secure-only). AIOps-backed COGS per WorkObject
(human+AI+tool+vendor = delivery cost → campaign contribution). Ledger already attributes usage to
agent/user/client/project/campaign/object with cost/latency/outcome/ratings.

## XXIII–XXVIII. Forecast, promises, contracts, rights, brand, culture
Profitability Forecast pre-acceptance (effort vs capacity, AI %, external cost, margin, scope risk →
clarify-before-commit). Promise Engine (promised_by/to/deliverable/date/conditions/confidence/owner/risk;
Aurora monitors miss probability). Contract Intelligence (retainer/scope/hours/deliverables/revisions/SLA/
payment/rights/channels/geo/exclusivity/authority/termination → operational constraints; 4th revision
outside allowance detected). Rights & Usage per asset (talent/music/image/font/stock/territory/duration/
channels/exclusivity/expiry → pre-publish BLOCKED, Operator+Sovereign). Brand Constitution per brand
(identity/voice/visual/claims/forbidden/legal/cultural/audience/positioning/principles/examples/
anti-examples; generation auto-checked). Culture/Localisation first-class (MSA/Egyptian/Gulf/Levantine/
English/Arabizi + religious/seasonal/humor/norms/taboos; intent preserved, not translated).

## XXIX–XXXI. Pitch mode, capacity, chemistry
Pitch Cell (client/industry/problem/competitors/opportunity/research/hypotheses/territories/budget/timeline/
cases/capabilities/team/proposal/commercial/presentation/win-p) assembling Intel+Strategy+Creative+
Production+Commercial+Account; WON→Client/Account/Campaign, LOST→reason→learning. Capacity Market
(need → fit% + availability + familiarity + chemistry + history + timezone + burnout + conflict + margin +
growth). Team Chemistry recommendation-only (pair history), never opaque employment judgment.

## XXXII–XXXVII. Memory, mining, benchmarks, root cause, process
Org memory (known/believed/tested/worked/failed/preferred/never-repeat). Case mining (novelty/
differentiation/result/evidence → Generate). Portfolio Intelligence (semantic archive queries).
Benchmarking (response/approval/revision/acceptance/variance/leakage/utilization/margin/AI cost/velocity
× dept/client/employee/type/market/season/service/team). Root Cause (late→approval delay→unclear owner→
fragmented feedback→no deadline→no backup→systemic fix). Process Mining (expected vs actual workflow
deviation + why).

## XXXVIII–XLII. Autopilot, judgment, confidence, contradiction, decay
Autopilot for predictable flows (classify→scope→task→assign→context→AI→QC→review; humans at judgment).
Judgment points explicit (auto: research/classify/summarize/route/status/version/cost; human: strategy/
selection/commitment/brand/high-risk publish/commercial+policy exceptions). Confidence architecture
(confidence/evidence/unknowns/alternatives/risk/verification; e.g. churn 68% with evidence+unknown+action).
Contradiction detection (brand vs brief vs guideline vs concept). Knowledge decay (created/verified/used/
corroborated/expires/superseded/deprecated; stale→confidence↓). Truth states: OBSERVED→DOCUMENTED→
INTERPRETED→PROPOSED→APPROVED→EXECUTED→MEASURED→VALIDATED→DEPRECATED (hypothesis never silently truth).

## XLIII–L. Search, twins, academy, simulation, planes
Memory Search (intent queries over graph+semantics). Employee Twin (role/skills/workload/familiarity/
tools/goals/availability/patterns; employee-owned, policy views for managers). Mentor→Manager→Institution
(individual→team→agency patterns→training). Training from real work; Academy modules from own successes;
Playbooks (tasks/roles/agents/tools/models/approvals/durations/risks/gates/budgets/results) for repeatable
excellence. Simulation (request+capacity+pipeline+budget+deadlines+AI → utilization/margin/overload/risk/
revenue; delay-what-ifs = digital twin). Five intelligence classes (domain/work/institutional/personal/
governance); Aurora coordinates, ALPHAs pipeline, Pantheon judges, Sovereign permits, humans own consequence.
Agency Timeline per entity (who knew/decided/versioned/cost/evidence at any point = time machine).

## PHASE 0 classifications (research → repo)
- Operating grammar router, per-type state templates, rituals objects, meeting engine (brief/copilot/record), why/decision/disagreement/assumption/experiment stores, creative/client/stakeholder memory, health/pulse/weather, attention/focus, handoff protocol, agent perf reviews, model router, COGS views, profit forecast, promises, contract/rights/brand/culture gates, pitch cells, capacity/chemistry, case/portfolio mining, benchmarks, root cause, process mining, autopilot, judgment map, confidence, contradiction, decay, truth states, semantic search, twins, academy, playbooks, simulation, timeline: MISSING or PLANNED (intake template ready; build in §IX enterprise-value order first: Sentinel, Doctor, Context Pack).
- Spine/edges/history, proposals/evidence, approvals, receipts, ledger attribution, MCP/A2A, API Sovereign seam: EXISTS (evolve).
- Account triage, traceability, lineage, capture richness, productivity: PARTIAL.
