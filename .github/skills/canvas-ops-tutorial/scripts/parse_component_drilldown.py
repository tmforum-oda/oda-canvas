"""Drill down into a single ODA Component showing API details, identity, and secrets.

Usage: kubectl get component <name> -n components -o json | python parse_component_drilldown.py
"""
import json
import sys


def main():
    d = json.load(sys.stdin)
    name = d["metadata"]["name"]
    s = d.get("status", {})

    print(f"=== Component: {name} ===\n")

    # API details
    print("--- API Details ---")
    for section in ["coreAPIs", "managementAPIs", "securityAPIs"]:
        apis = s.get(section, [])
        if apis:
            print(f"\n{section}:")
            for a in apis:
                print(f"  {a.get('name', '?')}")
                print(f"    Ready:        {a.get('ready', '?')}")
                print(f"    URL:          {a.get('url', 'N/A')}")
                print(f"    Developer UI: {a.get('developerUI', 'N/A')}")
                print(f"    Service:      {a.get('implementation', 'N/A')}")
                print(f"    Port:         {a.get('port', 'N/A')}")

    # Summary URLs
    summary = s.get("summary/status", {})
    print("\n--- Summary URLs ---")
    for key, label in [
        ("coreAPIsummary", "Core API URLs"),
        ("managementAPIsummary", "Management API URLs"),
        ("securityAPIsummary", "Security API URLs"),
        ("developerUIsummary", "Developer UIs"),
    ]:
        val = summary.get(key, "").strip()
        print(f"  {label}: {val or 'None'}")

    # Identity config — may be under different keys
    ic = s.get("identityConfig", {})
    if not ic:
        for k, v in s.items():
            if ("identity" in k.lower() or "security_client" in k.lower()) and isinstance(v, dict):
                ic = v
                break
    print("\n--- Identity Config ---")
    print(f"  Provider:            {ic.get('identityProvider', 'N/A')}")
    print(f"  Listener Registered: {ic.get('listenerRegistered', 'N/A')}")

    # Secrets management
    sm = s.get("securitySecretsManagement", {})
    sm_summary = summary.get("securitySecretsManagementSummary", "")
    print("\n--- Secrets Management ---")
    print(f"  Ready:   {sm.get('ready', 'N/A')}")
    print(f"  Summary: {sm_summary or 'Not configured'}")


if __name__ == "__main__":
    main()
