# Agentic authorization design note

This document is a discussion note on how an agentic component is authorized to call a
tool, as part of the [overall ODA Canvas design](Canvas-design.md). It sits between
[Epic 1: Authentication](Authentication-design.md) and
[Epic 4: AI-Native Canvas](AI-Native-Canvas-design.md).

**Status:** discussion note, seeking maintainer direction. Documentation only; it proposes
no implementation.

**Offered as input to:**
[#533 Agentic Interaction Security Operator](https://github.com/tmforum-oda/oda-canvas/issues/533)
and [#534 Model Operator](https://github.com/tmforum-oda/oda-canvas/issues/534), which
already name the control points this note is about. Nothing here is intended as an
alternative to either.

## Purpose

The AI-Native Canvas establishes that agents can be deployed as composable ODA Components
and that Components can expose MCP interfaces as tools. This note examines how the
Canvas's existing authentication and dependency model behaves once the consumer of an API
is an agent rather than a conventional component, and sets out six points where a design
decision is still required.

The note does not argue that the AI-Native Canvas is incomplete as shipped. The deliberate
choice to enable agentic components without requiring standardised agents is, in our
reading, the right one. The consequence of that choice is that the burden of control
shifts onto the Canvas control points, and this note is about whether those control points
are at the granularity that agentic consumers need.

## Scope of this review

Reviewed on `main` at commit `284f0561`, September 2026:

* `Canvas-design.md`, `Authentication-design.md`, `AI-Native-Canvas-design.md`,
  `SecurityPrinciples.md`
* `usecase-library/UC003-Configure-Exposed-APIs.md`,
  `usecase-library/UC005-Configure-Clients-and-Roles.md`,
  `usecase-library/UC007-Configure-Dependent-APIs.md`,
  `usecase-library/UC009-Internal-Authentication.md`
* the component, ExposedAPI and DependentAPI CRDs in `charts/oda-crds/templates/`
* the API Management and Dependency Management operators in `source/operators/`
* the feature files in `feature-definition-and-test-kit/features/`
* open issues on this repository

Not reviewed, and therefore possibly covering some of what follows: the
[Architecture Decision Log](https://github.com/tmforum-oda/oda-ca-docs/tree/master/Decision-Log/README.md)
in `oda-ca-docs`, the AI-Native Blueprint workstream materials, the Catalyst outputs
referenced from the AI-Native design, and
[IG1306](https://www.tmforum.org/resources/standard/ig1306-zero-trust-architecture-and-implications-to-enterprise-security-v3-0-0/).
Maintainers should discount any finding below that is already answered in those artefacts.

## What the Canvas already provides

Setting this out first, because several of the findings below are about the granularity of
mechanisms that already exist rather than about anything missing.

### Implemented today

* **MCP as an exposed API type.** `mcp` is a value of the `apiType` enumeration on
  ExposedAPI and on the component CRD, so a Component can publish an MCP tools interface
  declaratively.
* **Gateway support for long-running connections.** The Kong and APISIX API Management
  operators recognise `mcp`, `a2a` and `sse` API types and apply extended connect, read
  and write timeouts so persistent connections survive the gateway.
* **Name-keyed dependency resolution.** A component calls the Service Inventory at
  `info.canvas.svc.cluster.local` and receives only the dependent APIs it has been
  authorized to call, matched on `componentName` and `dependencyName`
  (`UC007-Configure-Dependent-APIs.md`, and the `list_services` client in the Dependency
  Management operators).
* **Authorization of a dependency as an operations action.** UC009 assumes the Operations
  team have configured access for a declared dependency; the
  `dependency-management-using-keycloak-authorization` operator now realises this by
  watching for a Keycloak role being granted on the consumer's client.
* **Per-component identity and enforcement at the edge.** Each component gets a client and
  roles in the identity platform (UC003, UC005), and authentication between components is
  enforced by a Service Mesh or API Gateway rather than by the component (UC009).

### Designed, not yet built

* `dependentModels`, the prioritised model list, use-case metadata and declared guardrail
  thresholds are described in `AI-Native-Canvas-design.md`. They are not yet present in any
  CRD.
* The AI Gateway is described in the same document; the operator that would configure it,
  `source/operators/TMFOP009-Model-as-a-Service`, is a README marked
  *Implementation Planned*.
* A2A agent cards as part of the component specification contract are a forward-looking
  bullet in the same document.

### Already recognised as open work

Issues [#533](https://github.com/tmforum-oda/oda-canvas/issues/533) (a policy control point
for agent-to-agent, agent-to-system and agent-to-human interactions, with the suggestion on
that issue of an MCP server registry applying auditing and guardrails),
[#534](https://github.com/tmforum-oda/oda-canvas/issues/534) (a Model Operator as the
enforcement point for model access),
[#343](https://github.com/tmforum-oda/oda-canvas/issues/343) (coarse-grained authorization
at the API Gateway on the component audience in a validated JWT) and
[#339](https://github.com/tmforum-oda/oda-canvas/issues/339) (an SDK for querying the
Service Inventory).

Two concerns an outside reader might expect to raise are, in our assessment, already
answered, and are not repeated below: **agents as a component type**, which the AI-Native
Canvas establishes, and **observability of non-deterministic workloads**, for which the AI
Gateway's auditing and token accounting and the evaluation framework are the designed
answer.

## Findings

### F1 — Dependency resolution is name-keyed and fixed at deployment

**Observation.** The API dependency is an explicit part of the component definition, and
components are deliberately not given raised privileges to query the Canvas. They call the
Service Inventory at a fixed address and receive the dependent APIs they have been
authorized to call, keyed on `componentName` and `dependencyName`, each carrying a URL and
an OAS specification.

**Why an agentic consumer stresses it.** An agent selects a tool at reasoning time from
whatever tool catalogue it can see. There is no `dependencyName` to resolve against,
because the dependency did not exist when the component was authored. The mechanism is not
weak here; it is structurally unavailable to this workload class.

There is a narrower version of the same point that is visible in the schema today: `apiType`
on the DependentAPI CRD admits only `openapi`, while the ExposedAPI enumeration includes
`mcp`. The `dependency-management-using-keycloak-authorization` operator matches a
DependentAPI to an ExposedAPI by specification URL and `apiType: openapi`. A Component can
therefore publish an MCP tools interface, but no Component can currently declare, or have
resolved, a dependency on one.

**What needs deciding.** Whether dependency mediation for agentic components should resolve
a request against policy rather than against a declared name, and whether the artefact
returned should be an authorization decision — a short-lived, audience-scoped credential —
rather than a URL and a specification.

**Where it would land.** A use case in the use case library, sibling to UC007, plus BDD
scenarios. Possibly a component specification change to express "may resolve tools at
runtime within set X", which would need to go through the component standard rather than
the Canvas.

### F2 — Internal authentication has no delegation semantics

**Observation.** UC009 describes the caller bootstrapping, at deployment, the system user
it will use to call the API; the provider bootstrapping the roles for the APIs it exposes;
the caller declaring its dependency, with the Operations team configuring access for that
dependency; and enforcement performed by a Service Mesh or API Gateway.

**Why an agentic consumer stresses it.** Every tool call an agent makes carries the agent
component's own system user. The originating principal and the task context do not survive
the first hop. Three consequences follow:

1. The provider component cannot make a per-request authorization decision, because every
   request from the agent is indistinguishable from every other.
2. The audit record at the provider identifies the agent component, not the request that
   caused the call. For use cases tagged high-risk in the Canvas use case registry, this is
   the record that regulatory reporting would rest on.
3. The blast radius of a compromised or misdirected agent is the union of every permission
   any of its tasks has ever needed.

**What needs deciding.** Whether the Canvas should support an optional delegated
authorization flow — for example RFC 8693 token exchange producing an audience-restricted,
task-scoped, short-TTL token that carries the delegation chain, issued against a per-task
workload identity rather than a per-component one. The promotion of Pod Certificates and
ClusterTrustBundles to stable in Kubernetes 1.37 (KEP-4317, KEP-3257) makes per-workload
identity substantially cheaper to implement in a reference Canvas than it was when UC009
was written; note that those KEPs explicitly rule out delegation in the certificate chain,
so the chain itself would stay in the token layer. See *Standards work in flight* below —
this is not a mechanism the Canvas would have to invent.

**Where it would land.** A use case sibling to UC009; a decision record in the Architecture
Decision Log in `oda-ca-docs`, assessing token exchange against the alternatives; BDD
scenarios asserting that the delegation chain survives to the provider component. Worth
noting that UC009 currently has no feature file at all, so internal authentication has no
executable coverage to extend.

### F3 — The tool hop: what decision does the control point make?

**Observation.** For language model access the design is symmetrical: the component
declares its requirements, an operator reads them, configures the AI Gateway, grants access
with authentication details, and enforces guardrails while producing audit, observability
and cost data. For tool access, the Canvas extends the component model to declare MCP
interface types and configures API Gateways for long-running connections.

The second of those is transport handling. Issue #533 proposes the missing control point
directly, and the suggestion on that issue of an MCP server registry with auditing and
guardrails is the same shape as the AI Gateway. So the question is not whether the
asymmetry has been noticed — it has — but what the control point decides, and on what
inputs.

**Why it matters.** The agent-to-tool direction is the direction in which state changes.
The nearest existing mechanism, #343, permits or denies at the gateway on the component
audience in a validated JWT. That is the right shape, and for conventional components it is
the right granularity: a component's audience is a stable fact about it. For an agent it is
not, because the agent's authority ought to vary by task and by trust level, and the
audience claim cannot express either.

**What needs deciding.** Whether the interaction security control point evaluates per call
or per connection (see F4), whether it evaluates task context or only caller identity (F2),
and what inputs beyond identity it consumes (F5).

### F4 — Long-lived connections versus short-lived authorization

**Observation.** MCP requires special handling because it uses an event-based architecture
with long-running HTTP connections, and the API Management operators deliberately extend
gateway timeouts for `mcp`, `a2a` and `sse` API types so those connections persist.

**Why it matters.** If authorization is established when the connection is established, it
outlives any short-lived credential and is not re-evaluated per tool call. That is
structurally incompatible with the direction in F2, and it is also the property that
delayed-activation supply-chain attacks exploit: a tool server that behaves correctly for
the first several calls and changes behaviour afterwards is invisible to a decision taken
once at connection setup.

**What needs deciding.** Whether the Canvas states a requirement that policy evaluation
occurs per tool call independently of connection lifetime, and what the re-authentication
semantics are for a long-lived MCP session whose credential expires mid-connection. This is
directly expressible as a BDD scenario against whatever control point #533 produces.

### F5 — Evaluation outcomes are not an input to authorization

**Observation.** The Canvas provides pre-production and continuous post-production
evaluation, and a use case registry tagging agents, tools and high-risk use cases.

**Why it matters.** Evaluation measures quality; it does not touch privilege. There is no
edge from an evaluation outcome or a guardrail violation to a change in what an agent is
permitted to do. An agent whose evaluation scores degrade in production keeps its full
permission set until a human intervenes.

**What needs deciding.** Whether the Canvas should define graduated trust levels for
agentic components with explicit promotion *and demotion* gates, where evaluation metrics
and guardrail violations are consumed as authorization inputs by the identity and
permission operators. The Autonomous Networks L0–L5 taxonomy is a natural axis for such
levels, and binding a level to a concrete permission configuration is something the AN
framework does not currently supply. In fairness this would be introducing that axis into
the Canvas design rather than extending it: no Canvas document references AN levels today.

**Where it would land.** BDD scenarios are the cheapest way to pin the behaviour — a
demotion trigger is far easier to state as a scenario than as prose.

### F6 — Untrusted content entering the reasoning loop is not modelled

**Observation.** Guardrails in the current design are declared thresholds applied on the
model hop. No reviewed artefact addresses content retrieved through an MCP tool becoming,
in effect, an instruction that shapes subsequent tool calls.

**Why it matters.** The AI-Native Canvas positions Components as tools that agents read
from, and positions the Canvas resource inventory as an MCP server that external agents can
connect to. An agent that reads from systems of record and also holds write permissions is
the standard precondition for this class of attack, and the design encourages exactly that
topology. Identity infrastructure cannot prevent it: the call arrives from the genuine,
correctly authenticated agent, and what has been subverted is the agent's decision rather
than its identity. Containment therefore has to come from the authorization and egress
layers, which is what ties this finding to F2 and F4 rather than leaving it a
model-behaviour concern.

**What needs deciding.** Whether the Canvas carries a threat model for this, whether MCP
tool results should carry a trust classification, and whether there should be a stated rule
that an agent may not act on content retrieved within the same session above a declared
trust tier without an approval step. TMF921 Intent Management is a natural binding point
for such an approval, because it gives a canonical representation of what was approved.

**Where it would land.** Not `SecurityPrinciples.md`, which is a statement of engineering
practice for the reference implementation rather than a threat model, and which explicitly
refers Zero Trust out to IG1306. Most likely a new section in the AI-Native design or a
document of its own.

## Standards work in flight

F2 and F4 would be poorly served by a Canvas-specific mechanism, because the relevant work
is already chartered at the IETF and the Canvas's role is to consume its output rather than
to invent an equivalent. Status as at September 2026:

* **WIMSE (Workload Identity in Multi System Environments)** — a chartered working group in
  the ART area, whose programme of work is an architecture document, a JOSE-based token for
  securing service-to-service call chains with cryptographic binding and contextual claims,
  a token issuance profile, and a token exchange profile building on RFC 8693. That is the
  layer F2 needs, and it explicitly exists to reconcile OAuth, JWT and SPIFFE, which have
  been combined in practice but in isolation from each other.
* **Transaction Tokens** (`draft-ietf-oauth-transaction-tokens`, OAuth working group,
  awaiting write-up) — propagate user identity, workload identity and authorization context
  through a call chain within a trust domain, so a downstream workload can decide against
  the original request rather than against its immediate caller. That is close to a direct
  statement of what UC009 cannot currently express.
* **OAuth Identity and Authorization Chaining Across Domains**
  (`draft-ietf-oauth-identity-chaining`, with the IESG) — combines RFC 8693 token exchange
  with RFC 7523 to carry identity and authorization *across* trust domains. That is the
  shape F2 would need between two Canvases, or between a Canvas and an external agent.

Naming and discovery are a separate layer and are being worked separately. The proposed
DAWN (Discovery of Agents With Names) working group covers discovery of AI agents and
resources and explicitly places identity management and trust evaluation out of scope, and
the Agent Name Service announced by the Linux Foundation as an intent to launch in June
2026 anchors agent identity in DNS, with support for decentralised identifiers and Legal
Entity Identifiers. Both answer "which agent is this, and who operates it", which is
upstream of, and does not substitute for, a per-request decision about a particular tool
call. Neither therefore bears on the findings above, and the Canvas already has its own
discovery answer in the Service Inventory and the component registry. The place either
would become relevant to the Canvas is establishing the authenticated root of the chain in
F2 for an agent originating outside the Canvas — for example one connecting to the resource
inventory MCP server.

The practical implication is that F2 is better put as "which of these does a Canvas adopt,
and where does enforcement sit" than as a request for a new mechanism.

## Editorial observations

* `AI-Native-Canvas-design.md` linked to `Authentication-design.md`, but not the reverse.
  The change that introduces this note adds the return link, so the two epics are now
  reachable from each other.
* `UC009-Internal-Authentication.md` links to `UC005-Configure-Users-and-Roles.md`, which
  does not exist; the file is `UC005-Configure-Clients-and-Roles.md`. Left alone here to
  keep this change reviewable as one thing; happy to raise it separately.
* `usecase-library/archive/UC099-Authorization.md` is an assumptions-TBD stub. If
  authorization was parked deliberately, the reasoning would be useful context for the
  findings above.

## Suggested sequencing

1. Maintainer direction on F3 — what decision the interaction security control point makes,
   and on what inputs. That answer determines how much of the rest is real.
2. F2 and F1 as a paired use-case contribution, with a decision record in `oda-ca-docs` for
   the mechanism choice.
3. F4 and F5 as BDD scenarios against the agreed use cases.
4. F6 as a threat model, once there is agreement on where it belongs.

## Contributor context

This note comes out of an internal architecture effort on agent identity and delegation for
a TM Forum-aligned BSS platform, covering workload identity, token exchange and capability
attenuation. We can contribute the use cases, decision-record text and BDD scenarios for
F1, F2, F4 and F5 if maintainers agree on the direction.

## Related documentation

* [Canvas Design Overview](Canvas-design.md)
* [Authentication Design](Authentication-design.md)
* [AI-Native Canvas Design](AI-Native-Canvas-design.md)
* [Security Principles](SecurityPrinciples.md)
