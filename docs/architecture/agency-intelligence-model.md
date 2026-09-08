# Agency Intelligence Model — Full-Service Canonical (v1 FINDINGS)

Canonical lifecycle (locked): **Lead → Pitch → Scope → Client → Brief → Strategy → Creative → Production → Approval → Launch → Media/Distribution → Performance → Learning → Retainer/Growth.** Specialist modes are overlays, never forks. Seams between disciplines are where agencies fail — every handoff below names its payload, acceptance check, and failure mode.

Source discipline: IPA role guidance (account management as cross-discipline owner; planning connects research→brief→measurement; creative owns delivery/quality/budget). Each finding names mapping targets: `graph object | workflow | screen | agent behavior | automation | governance rule | metric`.

## 1. People & titles
| Title | Department | Tier | Responsibilities | Mapping target |
|---|---|---|---|---|
| New Business Director | Growth | T2 | owns lead qualification, pitch go/no-go, pipeline value | `NewBusinessWorker.pipeline` + graph `lead/pitch` |
| Account Manager | Client Service | T1 | brief intake, status comms, approvals routing, change requests | `AccountWorker.triage` + Client OS screens |
| Senior Account Manager / AD | Client Service | T2 | supervises T1, department review, escalation owner | access `operator_t2` + Approval L2 |
| Strategist / Planner | Strategy | T2 | research → insight → brief criteria → territory eval → measurement plan | `IntelWorker` + `strategy` node |
| Creative Director | Creative | T2 | concept approval for production, brand gate, craft bar | Approval L2/L3 + `asset.publish` gate |
| Designer / Copywriter / Art Director | Creative | T1 | produce wip → in_qc assets against brief | task `doing` + Asset versions |
| Producer | Production | T2 | schedule, crew, shoot days, launch readiness, receipts | `DeliveryWorker.health` + launch preflight |
| Media Buyer / Planner | Media | T1/T2 | distribution plan, pacing, buy execution | `distribution` node + Performance ingest |
| Performance Analyst | Intelligence | T2 | attribution, reporting, learning proposals | `PerformanceWorker.report` |
| Finance Manager | Finance | T2 | estimates, SOW, change orders, invoices, retainers, margin | ERP commercial + `preflight_scope_change` |
| HR Manager | People | T2 | capacity data, hiring triggers (never salaries to non-HR) | access `hr` profile + row policy |

## 2. Responsibilities (RACI per lifecycle stage)
| Stage | Responsible | Accountable | Consulted | Informed | Mapping target |
|---|---|---|---|---|---|
| Lead | New Business | Growth Lead | Strategy | — | `lead` node owner New Business |
| Pitch | New Business | Growth Lead | Creative, Strategy | Finance | `pitch` + Approval (go/no-go) |
| Scope | Account + Finance | AD | Production | Client | `scope` + SOW doc; change → ChangeOrder |
| Brief | Account | Strategist (approved_by human) | Creative | Client | `brief` approved unlocks Strategy |
| Strategy | Strategist | Strategy Owner | Account | Client (selected only) | 3 territories, evidence each |
| Creative | CD | CD | Strategist | Account | 2 variants, eval vs brief+brand |
| Production | Producer | Producer | Craft | Account | tasks + shoot days + receipts |
| Approval | Owner role | Human L3 | Sovereign | Requestor | Approval node immutable |
| Launch | Producer | Producer | Account | Client | `launch` + version pin + receipt |
| Distribution | Media | Media Lead | Performance | Client | `distribution` live/paused/ended |
| Performance | Analyst | Performance Owner | Media | Client, Account | 7-day ingest, window stated |
| Learning | Analyst | Human validator | Strategy | All (embedded) | LearningProposal + INFORMS brief |
| Retainer | AD + Finance | Owner | Account | Client | `retainer` + churn rationale |

## 3. Task ontology
| Task verb | Object | Preconditions | Done = receipt | Mapping target |
|---|---|---|---|---|
| qualify | lead | source + contact captured | score + next step set | NewBusiness pipeline |
| draft/submit | pitch | qualified lead + conflict check | submitted + go/no-go requested | pitch transitions |
| propose/approve | scope | won pitch or active client | SOW signed (doc + edge) | scope + AUTHORIZES |
| intake/clarify | brief | active client + scope ref | approved Brief node | brief transitions |
| analyze/propose | strategy/media | approved brief + evidence | Proposal with evidence_ids | IntelWorker.propose |
| create/edit/submit | asset | concept approved_for_production | versioned node + SUPERSEDES | Asset versions |
| review/approve | asset/concept | QC passed + version match | Approval immutable | Sovereign + Operator |
| release | launch | QC-passed + exact-version approval | external receipt | preflight_launch |
| pace/pause | distribution | live + budget | ingest rows | distribution transitions |
| report/distill | performance/learning | publication_id + window | validated Learning | PerformanceWorker |
| renew/churn | retainer | active + rationale | renewed | retainer transitions |

## 4. Agency vocabulary (canonical terms)
| Term | Definition | Not-to-be-confused-with | Mapping target |
|---|---|---|---|
| Lead | unqualified commercial interest | Opportunity (qualified, valued) | graph `lead` / ERP Lead |
| Pitch | competitive proposal for a lead | Scope (post-win commercial terms) | graph `pitch` / ERP Pitch |
| Scope/SOW | agreed work, price, timeline | Estimate (pre-agreement numbers) | graph `scope` / ERP Scope |
| Change Order | approved delta to a signed scope | Scope creep (unapproved drift) | ERP ChangeOrder + `scope: changed` |
| Brief | approved creative instruction | Strategy (response to the brief) | graph `brief` |
| Territory | one strategic direction (of 3) | Concept (creative answer) | `strategy` selected |
| Concept | creative answer, 2 variants | Asset (produced artifact) | `concept` approved_for_production |
| Asset version | immutable produced node | File (mutable bytes) | new node + SUPERSEDES |
| Launch | versioned release event | Publish (the governed action) | graph `launch` + receipt |
| Distribution | paid/owned flight of an asset | Performance (measured outcome) | graph `distribution` |
| Learning | validated finding + evidence | Opinion (no evidence) | LearningProposal + EMBEDS_IN |
| Retainer | recurring commercial frame | Project (bounded scope) | graph `retainer` / ERP Retainer |

## 5. Rituals / meetings
| Ritual | Cadence | Inputs | Outputs | Mapping target |
|---|---|---|---|---|
| Pipeline review | Weekly | leads/pitches/scopes + values | go/no-go, owners, next steps | Meeting → Task/Revision; NewBusiness metric |
| Brief intake | Per brief | scope ref, client goals | clarified Brief | brief transitions + Scribe draft |
| Creative review | Per concept | 2 variants + eval | approved_for_production / killed + rationale | Approval node |
| Pre-flight / launch readiness | Per launch | QC report + approval + version | released / blocked + Blocker | preflight_launch |
| Post-campaign retro | Per campaign | performance + receipts | LearningProposal + action items | Learning + Meeting notes |
| QBR (retainer) | Quarterly | performance, spend, learnings | renew / churn + rationale | retainer transitions |

## 6. Artifacts
| Artifact | Producer | Consumer | Versioning | Mapping target |
|---|---|---|---|---|
| Pitch deck | New Business | Prospect | submitted immutable | `pitch` + DocDraft |
| SOW / estimate | Finance+Account | Client | signed version | `scope` + AUTHORIZES |
| Change order | Account | Client, Finance | numbered delta | ChangeOrder + `changed` |
| Brief | Account/Scribe | Strategy, Creative | approved/superseded | `brief` |
| Strategy territories | Strategist | CD, Client | proposed/selected | `strategy` |
| Concepts | Creative | CD | in_critique/revised | `concept` + eval |
| Assets | Craft | QC, Client | new node per version | Asset + SUPERSEDES |
| QC report + AI provenance | Operator | Approver | attached to version | receipt detail |
| Launch receipt | Channel/tool | Producer | required | `launch` released |
| Performance report | Analyst | Client, Account | collecting/reported | `performance` |
| Invoice / retainer statement | Finance | Client | draft→paid | ERP + money chain |

## 7. Tools (current reality → seams)
| Tool | Used by | For | Integration seam |
|---|---|---|---|
| Figma/Adobe | Creative | design/production | connectors (read-only first) |
| Premiere/DaVinci | Production | edit/grade | file watch → Sentinel |
| GitHub | Engineering | code/config | connector |
| Slack | All | comms/approvals surface | connector (drafts, never auto-send) |
| MCP servers | Operator | tool exec | `MCPLayer.call_tool` sole exec surface |
| LLM providers | Pantheon | analyze/propose/draft | `aurora/llm` adapters, never direct publish |

## 8. Handoffs (seams)
| From → To | Payload | Acceptance | Failure if dropped | Mapping target |
|---|---|---|---|---|
| Lead → Pitch | qualified lead + value + conflicts | score + owner set | ghost pipeline | CONVERTS_TO + NewBusiness metric |
| Pitch → Scope | won pitch + terms | SOW signed | free work | SCOPES + AUTHORIZES |
| Scope → Brief | scope ref + goals | brief cites scope | orphan brief | brief GROUNDS scope |
| Brief → Strategy | approved brief | 3 evidenced territories | opinion strategy | evidence_ids enforced |
| Strategy → Creative | selected territory | 2 evaluated variants | off-brief craft | eval vs brief+brand |
| Creative → Production | approved concept | versioned assets | unproducible ideas | task parent+owner+due |
| Production → Approval | QC-passed version | exact-version approval | version drift publish | version pin |
| Approval → Launch | approval + channel | external receipt | scheduled≠published | receipt required |
| Launch → Distribution | live asset + plan | pacing rows | spend without trace | attribution window |
| Distribution → Performance | publication_id + window | reported | orphan metrics | MEASURES |
| Performance → Learning | report + approval evidence | validated | opinion embedded | DISTILLS + validator |
| Learning → Retainer/Brief | embedded learning | cited by next brief | amnesia loop | INFORMS |
| Any → Change | delta + reason | change order signed | margin bleed | preflight_scope_change |

## 9. Decision points
| Decision | Owner | Inputs | Options | Mapping target |
|---|---|---|---|---|
| Pitch go/no-go | Growth Lead | value, fit, conflicts, capacity | bid / no-bid | pitch submitted→won/lost |
| SOW sign | AD + Client | scope, price, timeline | sign / renegotiate | scope approved |
| Territory select | Strategy Owner + CD | 3 evidenced territories | select 1 / reject all | strategy selected |
| Concept to production | CD | eval vs brief+brand | approve_for_production / kill | concept transition |
| Asset publish | Human L3 | QC + exact version | approved / changes_requested | Approval immutable |
| Launch release | Producer | QC + approval + receipt path | released / rolled_back | preflight_launch |
| Budget/scope change | L4 dual | change order + margin | approve / reject | scope changed + audit |
| Retainer renew/churn | Owner | performance + rationale | renewed / churned | retainer + learning capture |

## 10. Approval patterns
| Subject | Approver | Threshold | Expiry | Mapping target |
|---|---|---|---|---|
| Pitch submit | Growth Lead | always | — | pitch submitted |
| Scope sign / change | AD (sign), L4 dual (>$5k delta) | amount | 72h | preflight_scope_change |
| Concept → production | CD | brand fit ≥0.6 else escalate | — | concept transition |
| Asset publish | Human L3 | exact version + QC | 72h | preflight_publish |
| Launch release | Producer (exec) + L3 approval | receipt path present | — | preflight_launch |
| External send | Human L3 | AI output reviewed | 72h | message.send_external |
| Retainer churn | L4 + rationale + learning | always | — | retainer churned |

## 11. Failure modes
| Failure | Stage | Cause | Detection | Recovery | Mapping target |
|---|---|---|---|---|---|
| Ghost pipeline | Lead | no owner/next step | stale >14d | reassign or lost with reason | NewBusiness stale metric |
| Free work | Scope | production before SOW | task without scope ref | freeze + backfill scope | scope gate |
| Opinion strategy | Strategy | no evidence | empty evidence_ids | refuse proposal | Scribe.propose |
| Off-brief craft | Creative | skipped eval | brand_fit <0.6 | changes_requested | eval gate |
| Version drift publish | Approval→Launch | wrong version executed | pin mismatch | deny + Blocker | version pin |
| Receiptless launch | Launch | tool silent fail | no result_ref | stays scheduled + Blocker | receipt required |
| Unattributed spend | Distribution | no publication link | orphan rows | quarantine report | MEASURES invariant |
| Opinion learning | Learning | missing perf/approval evidence | gate check | refuse embed | propose_learning |
| Margin bleed | Scope | unsigned deltas | cost without change order | change order + re-approval | preflight_scope_change |
| Client churn surprise | Retainer | no health signal | overdue + silence | L4 + learning capture | churn prediction |

## 12. Mental models
| Model | Example quote | UX/AI implication |
|---|---|---|
| "The brief is the contract" | "If it's not in the brief, it's a change request" | brief diff view; scope-change detector on new asks |
| "Version is truth" | "Which v7? The approved one" | version pins everywhere; never overwrite |
| "No receipt, didn't happen" | "Show me the post ID" | launch/distribution UIs lead with receipts |
| "Approve the exact thing" | "I approved v4, you shipped v5" | approval binds version hash, not title |
| "Margin is made in scoping" | "We lost it in the SOW" | estimate-vs-actual visible at scope change |

## 13. KPIs
| KPI | Stage | Formula/source | Target | Mapping target |
|---|---|---|---|---|
| Lead→win rate | Lead/Pitch | won / (won+lost) | ≥25% | NewBusiness metric |
| Pitch cycle time | Pitch | submitted−created median | ≤14d | pipeline report |
| Scope change rate | Scope | changed scopes / approved | ≤20% | scope health |
| Estimate accuracy | Scope/Production | actual / estimated cost | 0.9–1.1 | margin() |
| First-pass approval | Creative | approved without revision | ≥60% | concept metric |
| QC pass rate | Production | qc_passed / submitted | ≥85% | asset metric |
| Launch receipt rate | Launch | receipts / releases | 100% | Operator metric |
| ROAS / CTR lift | Performance | channel-reported | per-client | performance rows |
| Learning embed rate | Learning | embedded / validated | ≥80% | Scribe metric |
| Retainer NRR | Retainer | renewed+expansion / base | ≥100% | retainer report |
| Utilization | Operations | allocated / capacity | 70–90% | AI-ERP capacity |
| AI cost share of COGS | Operations | ai_cost / cogs | tracked | AIOps margin() |

## 14. Commercial mechanics
| Mechanism | Trigger | Amount basis | Docs | Mapping target |
|---|---|---|---|---|
| Estimate | pitch won / brief intake | rate card × hours + pass-through | quote → scope | ERP Scope.estimate |
| SOW sign | scope approved | fixed / T&M terms | signed scope | scope AUTHORIZES |
| Change order | approved→changed | delta hours/cost | numbered CO | ChangeOrder + re-approval |
| Milestone invoice | stage gate hit | % of SOW | invoice ↔ scope | money chain, no orphans |
| Retainer fee | period start | monthly × scope | retainer statement | Retainer + invoice |
| Overrun absorption | actual > estimate w/o CO | margin hit | variance note | profitability + insight |
| Kill fee | campaign killed | % per SOW terms | cancellation invoice | killed + terms ref |

## 15. UX patterns (screens — contracts, UI builds later)
| Screen | User | Shows (graph query) | Actions (gated) | Mapping target |
|---|---|---|---|---|
| Pipeline room | Growth | leads/pitches/scopes + values/ages | qualify, submit, go/no-go (L2) | NewBusiness |
| Client room | Account | briefs, concepts, approvals pending, status | submit, request changes (L1) | Account |
| Creative room | CD/Craft | variants, evals, QC queue | approve_for_production (L2/L3) | Intel + Scribe |
| Launch console | Producer | QC + approvals + versions + receipts | release / roll back (L3 approval) | Operator + CRP |
| Performance room | Analyst/Client | attributed metrics + window | report, propose learning | Performance |
| Finance room | Finance | estimates/actuals, COs, invoices, retainers | sign, invoice (L3/L4) | ERP commercial |
| Command center | Producer/AD | blockers, pending approvals, loop health, access | escalate, reassign (L2) | Delivery + monitor |

## 16. AI behaviors
| Surface | May do | Must never do | Verification | Mapping target |
|---|---|---|---|---|
| New business | score leads, draft pitches, flag stale | submit pitch, set price | evidence + L2 review | NewBusinessWorker |
| Strategy | analyze, propose territories w/ evidence | declare truth, skip evidence | citation_check | IntelWorker |
| Creative | generate variants, self-critique vs brief | approve own work, publish | brand_fit + human gate | worker contract |
| Production | render, QC-check, collect receipts | mark QC passed without checks | QC report attached | Operator receipt |
| Launch | stage release, verify version | release without approval/receipt | preflight_launch | CRP + Sovereign |
| Finance | draft estimates/invoices, variance notes | send invoice, change terms | L3/L4 approval | commercial gates |
| Learning | propose with performance+approval evidence | embed without validator | propose_learning | Scribe gate |
| Client-facing | draft responses/status | send externally | human L3 + approval | send_external gate |

## 17. Agent capabilities (derived — gaps only)
| Gap | Owner worker | Inputs/outputs | Authority | Escalation | Metric |
|---|---|---|---|---|---|
| Pre-client pipeline untriaged | NewBusinessWorker | ERP leads/opps → triage WorkerResult | L1 propose | stale/conf<0.65 → Growth Lead | win rate, stale count |
| Launch release unverified | Operator.preflight_launch (+Delivery health) | QC+approval+version → allow/deny | L1 execute gate | deny → Producer + Blocker | receipt rate 100% |
| Scope economics drifting | Finance via preflight_scope_change | delta + CO → allow/deny | L3/L4 gate | deny → AD | change rate, margin |

No other new agents: Intel/Account/Delivery/Performance cover their domains.

## Mapping index
| Finding | Graph object | Workflow | Screen | Agent behavior | Automation | Governance rule | Metric | Status |
|---|---|---|---|---|---|---|---|---|
| F-01 lifecycle spine | lead/pitch/scope/launch/distribution/retainer | lifecycle template | pipeline/finance rooms | NewBusiness triage | stale nudge | preflight_scope_change/launch | win/change/receipt rates | code: schema+tests; doc: this file |
| F-02 version truth | Asset versions + SUPERSEDES | campaign + lifecycle gates | creative room | craft submit | drift detector | version pin (publish/launch) | first-pass, QC rate | exists; launch pin new |
| F-03 money chain | Scope/ChangeOrder/Invoice/Retainer | finance gates | finance room | finance draft-only | variance notes | L3/L4 spend + CO gate | estimate accuracy, NRR | ERP commercial new |
| F-04 approval lattice | Approval immutable +meeting decisions | approval nodes in templates | command center | request, never grant | expiry nudge 48h | L0–L4 + thresholds | approval SLA | exists; scope/launch additions new |
| F-05 learning loop | Learning + INFORMS | retro step | performance room | propose_learning | embed on validate | validator-required | embed rate | exists; enforced |
| F-06 seam failures | Blocker + observation | all handoffs | command center | raise/resolve-proposal | 24h escalation | fail-closed preflights | blocker age | exists |
