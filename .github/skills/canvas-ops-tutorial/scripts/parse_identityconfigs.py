"""Parse IdentityConfig list JSON from kubectl into a summary table."""
import json
import sys


def main():
    data = json.load(sys.stdin)
    items = data.get("items", [])
    if not items:
        print("No IdentityConfig resources found.")
        return

    # Header
    fmt = "{:<40} {:<20} {:<18} {:<6}"
    print(fmt.format("NAME", "IDENTITY PROVIDER", "LISTENER REG.", "ROLES"))
    print(fmt.format("-" * 40, "-" * 20, "-" * 18, "-" * 6))

    for item in items:
        name = item["metadata"]["name"]
        status = item.get("status", {}).get("identityConfig", {})
        provider = status.get("identityProvider", "—")
        listener = str(status.get("listenerRegistered", "—"))
        roles = item.get("spec", {}).get("componentRole", [])
        role_count = str(len(roles)) if roles else "dynamic"
        print(fmt.format(name, provider, listener, role_count))


if __name__ == "__main__":
    main()
