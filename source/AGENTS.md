# AGENTS.md — source/

This directory contains the core Canvas implementation: Kubernetes operators, admission webhooks, TMF service implementations, and development utilities.

## Directory Structure

- `operators/`: Kubernetes operators (Python/KOPF and Go/kubebuilder) — see `operators/AGENTS.md` for details
- `webhooks/`: CRD version conversion webhook (Node.js/Express)
- `tmf-services/`: TMF API implementations (Node.js and Python)
- `utilities/`: Development and troubleshooting tools

## Technology Mix

| Area | Language | Framework |
|------|----------|-----------|
| Most operators | Python 3.12 | KOPF (Kubernetes Operator Pythonic Framework) |
| PDB management operator | Go | kubebuilder |
| Webhooks | Node.js | Express.js |
| TMF639 Resource Inventory | Node.js | Express.js |
| MCP Resource Inventory | Python | FastMCP / UV package manager |

## Webhooks

The webhook server (`webhooks/implementation/app.js`) handles CRD version conversion between all supported ODA Component API versions (v1beta2, v1beta3, v1beta4, v1).

### Do

- Ensure version conversions are **bidirectional** — every upgrade path needs a corresponding downgrade path
- Test with the Postman collections in `webhooks/unit-tests/` and `webhooks/system-tests/`
- Use the CLI tool (`webhooks/command-line/convert.js`) for local conversion testing
- Return `ConversionReview` responses in the exact format Kubernetes expects

### Don't

- Do not add a new API version without updating `supportedAPIVersions` array AND adding both upgrade/downgrade conversion blocks
- Do not change the webhook without testing against all supported versions — a bug here breaks the entire Canvas

### Commands

```bash
# Run webhook in test mode (HTTP on port 8002)
cd source/webhooks/implementation
node app.js test

# Run local conversion
cd source/webhooks/command-line
node convert.js
```

## TMF Services

### TMF639 Resource Inventory (Node.js)
```bash
cd source/tmf-services/TMF639_Resource_Inventory
npm install
npm start
```

### MCP Resource Inventory (Python)
```bash
cd source/tmf-services/MCP_Resource_Inventory
uv install
uv run pytest          # Run tests
uv run python resource_inventory_mcp_server.py
```
