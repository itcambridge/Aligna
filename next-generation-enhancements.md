Aligna — Codebase Improvements Plan



Last updated: 11 Aug 2025Scope: From MVP (grounded CV generator) → production-hardening with evaluation, UI guardrails, and deployability.



🎯 Objectives (in priority order)



Zero‑hallucination UX: Only generate claims backed by retrieved evidence; visibly mark gaps.



ATS‑safe output: Deterministic structure, citation footnotes, and multi‑template export (DOCX/PDF/JSON).



Measurable quality: Golden‑set evaluation, retrieval metrics, and CI quality gates.



Operational readiness: Observability, cost/latency controls, and safe multi‑tenant data boundaries.



Sensible integrations: Clean LinkedIn MCP ingestion, complete Supabase storage, frictionless deploy.



🧭 Guiding Principles



Evidence first: A claim must have ≥1 cited snippet. If not, either omit or label “Not evidenced in CV.”



Determinism where possible: Small model for JD structuring/rerank; large model only for final prose.



User agency: Allow edits, but flag when edits sever evidence links.



Privacy by default: Clear user scoping on every query; one‑click purge of vectors + artifacts.



🗺️ Roadmap Overview (logical order)



Phase 0 — Hotfixes (Day 0–1)







Phase 1 — Retrieval Guardrails \& Coverage (Day 1–5) ✅







Definition of Done



Evidence table appears per JD; bullets never render without ≥1 citation. ✅



Unit tests cover: empty evidence, partial coverage, normalization map. ✅



Phase 2 — Generation Contracts \& Templates (Day 4–8) ✅







Requirement Scoring Record (JSON)



{

&nbsp; "req\_id": "uuid",

&nbsp; "text": "Deploy ML models to prod",

&nbsp; "signals": {

&nbsp;   "semantic\_top1": 0.83,

&nbsp;   "avg\_top3": 0.77,

&nbsp;   "keyword\_overlap": 0.6,

&nbsp;   "years\_evidence": 2.0,

&nbsp;   "recency\_years": 1

&nbsp; },

&nbsp; "decision": {

&nbsp;   "covered": true,

&nbsp;   "confidence": 0.78,

&nbsp;   "gaps": \["No explicit on-call ownership"]

&nbsp; },

&nbsp; "evidence": \[

&nbsp;   {"cv\_id":"…","chunk\_index":12,"section":"Experience","snippet":"…deployed models with CI/CD…","start":345,"end":512}

&nbsp; ]

}



Bullet Generator Contract (JSON)



{

&nbsp; "input": {

&nbsp;   "requirement": "Operate Kubernetes in production",

&nbsp;   "evidence\_snippets": \["…", "…"],

&nbsp;   "allowed\_claims\_only": true

&nbsp; },

&nbsp; "output": {

&nbsp;   "bullet": "Operated Kubernetes clusters for 30+ microservices with IaC; reduced deployment MTTR by 40%.",

&nbsp;   "citations": \[{"cv\_id":"…","chunk\_index":7}],

&nbsp;   "risk\_flags": \["metric\_inferred"]

&nbsp; }

}







DoD: Given a JD with partial matches, writer returns (a) bullets only for covered items; (b) labeled gaps list; (c) footnotes compiled. ✅



Phase 3 — UI/UX Evidence Experience (Day 6–10) ✅







DoD: Any bullet click shows the exact snippet; exporting preserves footnotes; lighthouse‑style UX checks. ✅



Phase 4 — Evaluation \& Quality Gates (Day 8–12)







Phase 5 — Observability, Cost \& Latency (Day 10–14)







DoD: Grafana‑ready metrics or logs; cost per generation visible in admin pane; A/B toggles runtime‑switchable.



Phase 6 — Integrations (Day 12–16)







DoD: JD paste‑in and MCP paths both produce identical internal JobRequirements objects; Supabase holds minimal PII, everything user‑scoped.



Phase 7 — Deployment \& CI/CD (Day 14–18)







DoD: One‑click deploy pipeline green; rollback procedure documented and tested.



Phase 8 — Future Enhancements (post‑launch)







📦 Task Breakdown by Component



Retrieval \& Matching







Generation







UI/UX







Evaluation







Observability \& Ops







Data \& Privacy







Integrations







Deployment







✅ Acceptance Criteria (condensed)



No uncited bullets ever render.



Gaps show as badges with “closest related evidence” when available.



ATS‑safe exports validated by common parsers.



CI blocks deploy above hallucination threshold and below recall target.



Logs \& metrics expose cost/latency per generation.



User privacy: purge works; queries are user‑scoped; minimal PII at rest.



📚 Artifacts to Produce



contracts/requirement\_scoring.schema.json



contracts/bullet\_generator.schema.json



export/templates/{classic,concise,impact}.docx



eval/golden\_set/\*.yaml + eval/report.md



ops/run\_log.schema.json + dashboards



docs/runbooks/deploy.md, rollback.md, privacy.md



🧩 Effort \& Ownership (T‑shirt sizes)



Retrieval guardrails: M



Generation contracts \& templates: M



UI evidence experience: M–L



Evaluation harness + CI gates: M



Observability \& cost: S–M



Integrations (MCP + Supabase): M–L



Deployment \& pipeline: M



🔗 References (internal)



Existing enhanced Qdrant client \& schema (15+ indexed fields).



Current Streamlit Apple‑style UI; results section hooks.



Prior assistant notes on coverage matrix and safe phrasing.
