"""Poll ODA Component deployment status until Complete or timeout.

Usage: kubectl get components -n components -o json | python poll_component_status.py [component-name]

If component-name is provided, only that component is shown.
Otherwise all components are shown.
"""
import json
import sys


STATUS_MESSAGES = {
    "In-Progress-CompCon": "Configuring APIs...",
    "In-Progress-IDConfOp": "Configuring identity...",
    "In-Progress-SecretMan": "Configuring secrets...",
    "In-Progress-DepApi": "Resolving dependent APIs...",
    "Complete": "Component deployed successfully!",
}


def main():
    filter_name = sys.argv[1] if len(sys.argv) > 1 else None

    data = json.load(sys.stdin)
    items = data.get("items", [])

    if not items:
        print("No components found.")
        return

    for item in items:
        name = item["metadata"]["name"]
        if filter_name and filter_name != name:
            continue

        status = item.get("status", {})
        summary = status.get("summary/status", {})
        dep_status = summary.get("deployment_status", "Unknown")
        message = STATUS_MESSAGES.get(dep_status, f"Status: {dep_status}")

        print(f"{name}: {dep_status} — {message}")


if __name__ == "__main__":
    main()
