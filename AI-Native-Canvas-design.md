# AI-Native Canvas design

This document describes the design artefacts for the AI-Native Canvas part of the [overall ODA Canvas design](Canvas-design.md).

There is an introductory video at 

[![AI-Native-Canvas-video](images/AI-Native%20Canvas/End-to-end%20AI%20Native%20Canvas%20architecture.PNG)](https://www.youtube.com/watch?v=MICzwN8VB_o)

## Overview

The AI-Native Canvas extends the Open Digital Architecture (ODA) to support AI-native systems at enterprise scale. This work addresses three critical questions:

1. How do we expose ODA Components as tools for AI agents using MCP (Model Context Protocol)?
2. How can we deploy AI agents themselves as modular, composable components?
3. How do we operate a multi-vendor, multi-agent architecture at scale while maintaining governance, security, and responsible AI practices?

## Lessons Learned from Catalyst Programs

Three key Catalyst programs from 2025 significantly influenced the AI-Native Canvas approach:

* [Agent Fabric Catalyst](https://www.tmforum.org/catalysts/projects/C25.0.798/agent-fabric-phase-ii) 
* [Agentic ODA for Personalized Customer Experiences](https://www.tmforum.org/catalysts/projects/C25.0.793/agentic-oda-for-proactive-personalized-customer-experiences)
* [Growing B2B with Autonomous Agents](https://www.tmforum.org/catalysts/projects/M25.0.797/Growing-B2B-with-autonomous-agents)


These Catalyst proof-of-concepts revealed several critical patterns:

1. **AI agents as architectural paradigm**: Modular, task-oriented, context-aware systems operating autonomously within defined guardrails
2. **MCP as standard**: The de facto standard for how agents use APIs as tools, with TM Forum Open APIs well-suited for MCP wrappers
3. **Multi-agent architectures**: Modular agents collaborating to deliver use cases, with tightly scoped agents outperforming general-purpose ones
4. **Cross-layer applicability**: Agents relevant across every architectural layer and throughout the technology lifecycle

## MCP Support in ODA Components

### Extending the Component Model

The existing component patterns already include a declarative model for exposing API services. Components expose multiple APIs beyond TM Forum functional APIs, supporting cross-industry standards like OpenMetrics and OpenTelemetry. Extending components to expose MCP APIs was as simple as expanding the enumeration to include MCP.

![Component-exposing-MCP](images/AI-Native%20Canvas/Component%20exposing%20MCP%20tools%20interface.PNG)

### MCP Requirements

MCP requires special handling because it uses an event-based architecture with long-running HTTP connections rather than standard REST-style integration. This means API Gateways need special configuration to support these persistent connections.

The Canvas has been extended to:

* Allow declarative specification of MCP interface types in the component model
* Build MCP operators to automatically configure API Gateways for long-running connections
* Implement MCP servers for ODA Components (e.g., Product Catalog Management)

### MCP Implementation Details

![MCP-tools-example](images/AI-Native%20Canvas/Component%20MCP%20tools%20example.PNG)

MCP is fundamentally about describing APIs in natural language so agents understand how to use them. The most important part of MCP implementation is the English description of both the API function and all arguments. This contrasts sharply with Swagger descriptions, which were designed for API experts, not AI agents.

Key implementation findings:

* Arguments require detailed explanation and examples
* Language models work better with specific examples in the descriptions
* Filtering and complex parameters need explicit examples for agents to use them effectively

The API workstream has recognized that MCP wrappers could be generated automatically from Swagger files by upgrading descriptions with more detail and examples, assuming these Swaggers might be consumed by language models.

## Agents Packaged as Composable ODA Components

### Assumptions for Agentic Components

![Agentic-component-assumptions](images/AI-Native%20Canvas/Agentic%20components%20-%20assumptions.PNG)

The extension of the component model to support agents is based on several key assumptions:

1. **Foundational models as services**: GenAI models and classical machine learning models execute as services accessed through APIs on the underlying cloud platform. Agent software accesses language models through APIs, consistent with most agent frameworks today.

2. **Approved model catalogs**: CSPs will maintain approved catalogs of foundational GenAI models. This is standard practice - for example, at Vodafone, the common platform requires any language model to be on an approved list, with a rigorous process for adding new models while maintaining privacy and security standards.

3. **Non-deterministic systems**: Agentic components are non-deterministic, requiring significantly more testing. The preferred term is "evaluation" - components need comprehensive evaluation datasets and metrics to continuously evaluate agent performance against expectations.

4. **Additional canvas services**: Agent components typically require additional cloud services like vector databases, anonymization services, and chunking services, which need to be available in the Canvas.

### Extending the Component Model

![Extending-component-model](images/AI-Native%20Canvas/Extending%20component%20model%20to%20enable%20agentic%20components.PNG)

The component model extension originated from the "Agentic ODA for Proactive Customer Experiences" Catalyst. The approach allows components to declare which language models they want to access, providing a prioritized list. The Canvas platform then grants access to whichever subset are available in the approved language models.

Similar to `exposedAPIs` and `dependentAPIs`, the specification includes `dependentModels`, where components:

* Describe the models and their priority
* Provide details about the use case (required for use case inventory)
* Define guardrails to ensure responsible AI usage

The declarative requirements allow components to define their thresholds against guardrails as well.

### AIVA as Example Agentic Component

![AIVA-example](images/AI-Native%20Canvas/AIVA%20as%20example%20Agentic%20component.PNG)

The implementation was showcased at DTW using AIVA (TM Forum AI Assistant) packaged as a component and deployed on the Canvas. As an API-first component, AIVA was tested through direct API integration (not through the AIVA portal), allowing other agents to communicate directly with AIVA through APIs.

![AIVA-workflow](images/AI-Native%20Canvas/AIVA%20as%20example%20Agentic%20component%20-%20workflow.PNG)

Deploying AIVA on the Canvas provided immediate use of all existing Canvas services:

* Modular deployment
* API exposure through API Gateway
* Observability
* Identity management

These capabilities come standard when deploying agents as software components and are essential for any agent deployment.

### AI Gateway

To grant access to foundational GenAI models, the Canvas introduces an **AI Gateway**. When granting access to unknown models, access is provided through this gateway (or proxy), which enables:

* **Auditing**: All interactions are audited, essential for responsible AI practices
* **Observability**: Exact monitoring of what's being discussed between components, agents, and underlying language models
* **Cost management**: Understanding how many tokens of which model a component is consuming

The process follows four steps:

1. An operator reads the declarative requirements
2. Configures the AI Gateway
3. Grants the component access with authentication and input details for accessing language models
4. Enforces guardrails while providing data for auditing, observability, and cost management

This forms the foundation for what the Canvas must provide to support multi-vendor AI agents across every functional domain, enabling governance, control, and responsible AI adoption at scale.

## Canvas Services to Support AI Agents at Scale

![Canvas-AI-Capabilities](images/AI-Native%20Canvas/Canvas%20AI%20Capabilities.PNG)

For multi-vendor AI agents across every functional domain, the Canvas needs:

### AI Models and Services

* **Language models**: Foundation GenAI models
* **Other AI models**: Embedding models, multimodal models
* **Classical ML models**: With correspondent MLOps processes
* **Additional capabilities**: Vector databases, anonymization, chunking, and other cloud services

### Observability

Observability extends beyond technical monitoring and performance of standard software to include AI-specific observability for language models, supporting tools like:

* LangSmith
* OpenLLMetry (an OpenTelemetry extension)

### AI Gateway

A standard architectural component enabling:

* Automated guardrails
* Auditing of all AI interactions
* Cost management and token tracking

### Evaluation Framework

Support for both:

* Pre-production evaluation
* Post-production continuous evaluation of ongoing AI performance

### Use Case Registry

A Canvas registry with tagging of:

* All agents
* Tools
* High-risk use cases (requirement for EU AI Act)

## End-to-End Data and AI Architecture

![End-to-end-architecture](images/AI-Native%20Canvas/End-to-end%20AI%20Native%20Canvas%20architecture.PNG)

The AI-Native Canvas fits within the end-to-end AI and data architecture through collaboration between the Composable IT mission (where Canvas and Component work resides) and the AI and Data mission.

### Canvas Pre-AI

![Canvas-pre-AI](images/AI-Native%20Canvas/Canvas%20pre%20AI.PNG)

Historically, composable IT within ODA consisted of:

* **Modular standard components**: Extensive work building components with use cases and Catalyst programs
* **ODA Canvas**: Operators read component requirements and configure underlying cloud platform services
* **Foundational services**: API Gateways, service meshes, observability, identity and access management systems

### Canvas with AI and Data Extensions

![Canvas-with-AI-Data](images/AI-Native%20Canvas/Canvas%20with%20AI%20and%20Data.PNG)

The AI-Native Canvas extensions add:

* **Agentic components**: Alongside standard ODA Components
* **MCP interfaces**: Components can offer MCP so they're available as tools toward other agents
* **Agent-to-Agent (A2A) standards**: Support for emerging standards like Google's A2A protocol, where agent components expose "agent cards" explaining their capabilities as part of a YAML contract in the component specification
* **AI operators**: Model operators that read declarative requirements and configure the AI Gateway
* **Data products as a service**: Future extension where components declare requirements for data products, with data operators integrating and granting access through underlying data services

The patterns already established fit naturally with these AI services. The experimentation has successfully extended the ODA Component model for agentic components.

**Note on standardization**: Agentic components are shown in white (vs. colored systems of record components) to indicate that, similar to engagement management, we want to enable deployment of agents as components following the component model, without requiring standardized agents. This allows non-standard agents to seamlessly interact and interrogate all systems of record components, leveraging the foundational data within TM Forum standards.

## Canvas Resource Inventory

![Canvas-Resource-Inventory](images/AI-Native%20Canvas/Interact%20with%20a%20Canvas%20via%20Agent.PNG)

On top of the Canvas, a resource inventory has been built that serves as a registry of components, agents, tools, and use cases. The Canvas uses the TMF639 Resource Inventory API as a standard interface, making it straightforward to expose components and APIs into a TM Forum-compliant resource inventory.

As with all TM Forum APIs, the resource inventory can be exposed as an MCP server to make it available to AI agents. This means:

* External AI agents (e.g., Claude Desktop) can integrate with the Canvas using the MCP server as a tool
* Agents can query in natural language: "What resources are available in the ODA Canvas?"
* Agents can request detailed descriptions of specific components and APIs
* Agents can even create diagrams of component architectures automatically

This enables AI agents to discover and understand the Canvas architecture, making the platform self-documenting and accessible through natural language interfaces.

## Classical ML Models

In addition to GenAI models, the Canvas supports classical machine learning models through an **AI Model Manager**.

For custom machine learning models, the component needs to include that custom model as part of the component definition. Similar to how container images are specified in Kubernetes manifests, components include a URL to a machine learning model in an accessible model repository.

The Model Manager operator:

1. Downloads the model
2. Submits it into an MLOps pipeline for review, testing, and deployment
3. Once approved and deployed, provides API access to the inference engine so the component can access the custom model

This approach enables components to package and deploy their own custom ML models while maintaining proper governance and operations processes.

## Evaluation and Testing

![Evaluation-1](images/AI-Native%20Canvas/Evaluation%201.PNG)
![Evaluation-2](images/AI-Native%20Canvas/Evaluation%202.PNG)
![Evaluation-3](images/AI-Native%20Canvas/Evaluation%203.PNG)
![Evaluation-4](images/AI-Native%20Canvas/Evaluation%204.PNG)
![Evaluation-5](images/AI-Native%20Canvas/Evaluation%205.PNG)

Because AI services are non-deterministic, components should come packaged with complete evaluation datasets and tests.

### Evaluation Approach

* **Pre-deployment**: Conduct comprehensive evaluation to establish baseline performance for the agent
* **In production**: Continuously evaluate and monitor agent behavior and characteristics

### AIVA Evaluation Implementation

For the AIVA agent component:

1. **Golden dataset**: Created 87 evaluation questions representing the types of questions someone might ask the TM Forum AI Assistant
2. **Usage logging**: During real usage, log user questions and AIVA responses, gathering information about what people are actually asking
3. **Evaluation questions and responses**: Create evaluation datasets with AIVA responses for automatic and human-based manual evaluation

### Evaluation Methods

**AI-based evaluation**: At scale in production, use AI-based evaluators to evaluate AIVA's performance and responses using frameworks like the LangGraph open-source evaluation framework. The AI evaluator uses prompt templates:

* "You are an expert evaluator"
* Provides the question and answer
* Asks the AI model to evaluate for relevance, accuracy, completeness
* Provides overall assessment

**Human evaluation**: Built an interface for human evaluators to score responses for:

* Relevance
* Accuracy
* Completeness
* Commentary on scoring rationale

### Evaluation Dashboard

The evaluation framework provides:

* Metrics distinguishing golden questions vs. user questions
* Tracking of manual vs. automatic AI evaluation
* Dashboard to monitor agent performance over time
* Ensuring changes improve overall performance before deployment

This continuous evaluation is essential for maintaining quality in non-deterministic AI systems and provides the confidence needed for production enterprise deployments.

## Summary

The AI-Native Canvas demonstrates that the Open Digital Architecture isn't just ready for AI - it's architected to make AI operationally viable at telecommunications scale.

### Key Achievements

* **MCP integration**: Components can expose MCP interfaces, making them available as tools for AI agents
* **Agentic components**: Agents can be deployed as modular, composable components following the ODA Component model
* **Multi-agent architectures**: Support for multi-vendor, multi-agent systems with proper governance and control
* **AI Gateway**: Provides auditing, observability, and cost management for AI interactions
* **Evaluation framework**: Continuous evaluation for non-deterministic AI systems
* **Resource inventory**: Self-documenting Canvas accessible through natural language

### Operational Benefits

The Canvas provides the foundation for CSPs to confidently deploy and operate multi-vendor agent architectures across every functional domain with:

* **Governance and control**: Required for enterprise scale operations
* **Responsible AI practices**: Auditing, observability, cost control, continuous evaluation
* **Regulatory compliance**: Use case registry and high-risk tagging for EU AI Act
* **Production-ready**: All the operational capabilities needed for enterprise telecommunications systems

## Related Documentation

* [Canvas Design Overview](Canvas-design.md)
* [Authentication Design](Authentication-design.md)
* [Event-based Integration Design](Event-based-integration-design.md)
* [Observability Design](Observability-design.md)

## Reference Video

Full presentation: [AI Native ODA Canvas](https://www.youtube.com/watch?v=MICzwN8VB_o) (30:35)

### Video Chapters

* 0:00 - Introduction
* 1:58 - Lessons learned
* 5:30 - MCP support
* 9:17 - Agents packaged as composable ODA Components
* 15:53 - Canvas services to support AI Agents at scale
* 17:21 - End-to-end Data and AI Architecture
* 22:10 - Canvas Resource Inventory
* 24:54 - Classical ML Models
* 25:56 - Evaluation and testing
