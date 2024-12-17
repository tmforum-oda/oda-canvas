# Open Digital Architecture Reference Implementation (RI) Security Principles

## Why does the ODA Reference Implementation need security principles?

Aside from TM Forum assets like [IG1306](https://www.tmforum.org/resources/standard/ig1306-zero-trust-architecture-and-implications-to-enterprise-security-v3-0-0/), which describes how Zero Trust Architecture and ODA relate, the ODA Accelerator Innovation Hub aims to produce a working reference implementation and therefore has some additional specific questions to answer:
- how do we ensure the reference implementation is safe to use?
- how can we demonstrate to the cybersecurity colleagues of reference implementation users that the ODA is practically deployable in the enterprise?
- how do we demonstrate and prove/disprove the security principles and standards that are proposed as part of the overall ODA standards?
- what security solutions are part of the reference implementation, and what other security provisions will need to be made by users of the reference implementation?

These principles will allow us to answer those and other questions.

## How does this relate to the actual ODA standards?

This draws from existing TM Forum work to ensure the reference implementation meets the ODA standards, but these principles relate only to the Apache2 licensed open source project. The intention is not to deviate from the ODA Standards, but to inform them and be informed. Conformance with the ODA standards is paramount, but we may discover new things or need to make practical detours before we get there.

## What are the principles?

### Automated security

Where we apply security controls, they will be automated.

For the RI itself, any security control or feature we build in will be tested automatically during every pull request. For example, if we vulnerability test containers those tests will run in every PR where the container code changes.

For developer experience security controls those will also be automated. For example, we aim to lint all code. That linting will happen during every pull request.

### A failed test is a bug

Where a test fails, by default we require it to be fixed before a pull request is merged.

If that can't be done, the ODA Accelerator team will discuss that during the daily standups and we'll agree the risk treatment for that bug. In any cases where we permit a merge with a failed test, a new `bug-fix` issue is required so that we can remove the risk.

### Run in production, but not ready for production

The RI is a test and experimentation platform designed to give a hands-on experience of an ODA Canvas, and provide just enough functionality to run component conformance tests.

It is not designed to run in production, which means it is not intended to do things like scale up/out or be resilient to failure. However, we have to assume the environment it will run on requires a certain level of production readiness.

That means things like: minimising, hardening and signing of containers; real integration with identity platforms; encryption of data in-flight by default. We will do what we can to assure users that the RI is safe to deploy. Where we miss something, we gratefully accept detailed issues and pull requests.

### Layered security; defined boundaries

The RI has pre-requisites, features and operations needs. Each of these is clearly defined.

The ODA Canvas is designed to fit into an existing enterprise, and certain assumptions are made about what that means. Features are either external prerequisites, component features, Canvas features or operational tasks specific to the RI. We document them, usually in the installation guide, so that it is clear what scope a feature falls under.

For example, the Canvas is designed in such a way that we minimised the footprint for identity management inside the Canvas and components and rely on that existing outside the Canvas before deployment. We define how the features of the Canvas integrate with that and provide open source examples of how to achieve that in the RI.

Where certain tasks are individual to different enterprises and the TM Forum is not opinionated, we've provided SRE automations that perform those tasks for us in a lightweight way. A good example of that is how machine/system user credentials are passed from identity management to the component. This will vary from organisation to organisation depending on the identity product, and the enterprise process, so the Canvas has a method for safely gathering credentials from the RI identity platform and passing them to components. It's not part of the ODA Standards and we don't expect our simple method to be used anywhere, it simply serves an operational need for us in the RI.

### Bootstrap everything

Automating everything eventually requires one identity to be configured by hand. Everything else should be bootstrapped by the installer.

Automating everything requires us to be able to enable encryption, Canvas service user accounts, operators, identity configuration and other things. The RI is a testbed for how much we can do automatically. The aim is for a single identity and its credentials to be provided to the RI installation chart after the prerequisites have been configured, which will allow the RI to bootstrap itself with no intervention.