# ActionBoundary Product Direction

## Register

ActionBoundary is a focused, founder-led authorization evidence review for B2B AI agents that can take high-impact business actions. Public language is direct, technically precise, and restrained.

## Users

The primary user is a founder, CTO, product-security owner, or engineering lead building an accounts-payable or finance agent that can move money, change vendor records, issue refunds, or write to an ERP. They need to answer a buyer's concrete security question without turning the engagement into a broad penetration test or a platform rewrite.

Secondary users operate other tool-using agents with comparable authorization risk, including access grants, exports, record changes, support operations, scheduling, and healthcare workflows.

## Product Purpose

Turn one high-impact staging workflow into reviewable authorization evidence. Start from existing redacted logs where possible, identify missing evidence when a verdict is not supportable, and bind the trace, scenario pack, scored verdict, report, execution profile, and customer execution attestation into a reproducible evidence package.

For multi-agent or externally orchestrated systems, accept optional harness
context for workflow state, delegation, tool grants, deterministic gates, and
fork/join outcomes. ActionBoundary verifies how those controls affected one
selected business action; it does not replace the customer's harness, IAM,
policy engine, observability stack, or agent runtime.

## Brand Personality

Forensic, restrained, accountable, and independent. The product should feel like a careful evidence desk: calm enough for a security reviewer, concrete enough for an engineering team, and candid about what the evidence does not prove.

## Anti-references

- Generic AI safety platform or all-purpose governance suite.
- Benchmark leaderboard or vendor-ranking theater.
- Compliance certification, security seal, or "certified secure" claim.
- Anonymous scanner that produces findings without customer execution evidence.
- Generic AI SaaS landing-page clichés, purple-blue gradients, robot imagery, floating orbs, decorative dashboards, or glassmorphism.
- Absolute claims such as "buyer-ready" or "verifiable" when the public artifact is synthetic, illustrative, incomplete, or not bound to customer execution.

## Design Principles

- Lead with AP and finance authorization; keep broader workflows secondary.
- Show bound artifacts and explicit limitations before promotional claims.
- Preserve a narrow review boundary: one workflow, staging or sandbox, no production credentials, and no real customer data by default.
- Make PASS, BLOCKED, and INCONCLUSIVE evidence readable to both engineers and security reviewers.
- Keep human responsibility visible: the review is performed and signed by a named reviewer.
- Keep public proof distinct from private customer evidence.

## Product Freeze

After contract set 1.2, do not add a new core capability without evidence from
a real customer trace, a documented lost-deal reason, or a paid-pilot delivery
blocker. Allowed maintenance is limited to defects, contract or artifact
inconsistency, evidence-integrity gaps, critical dependency or regulatory
changes, and narrowly scoped customer field mappings. Research ideas stay in
the backlog until market evidence selects them.

## Accessibility and Inclusion

Target WCAG 2.2 AA contrast and keyboard access. Never encode verdict state by color alone. Preserve visible focus states, semantic headings, useful alt text, and reduced-motion behavior. Copy must remain understandable without security or machine-learning jargon.
