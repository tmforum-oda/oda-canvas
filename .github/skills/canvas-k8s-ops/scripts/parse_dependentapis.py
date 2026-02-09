"""Parse DependentAPI list JSON and display resolution status.

Usage: kubectl get dependentapis -n components -o json | python parse_dependentapis.py
"""
import json
import sys


def main():
    data = json.load(sys.stdin)
    items = data.get("items", [])

    if not items:
        print("No DependentAPIs found in this namespace.")
        print()
        print("DependentAPIs only exist when a component declares them.")
        print("To enable, deploy a component with: --set component.dependentAPIs.enabled=true")
        return

    resolved = []
    unresolved = []

    for item in items:
        m = item["metadata"]
        sp = item.get("spec", {})
        st = item.get("status", {})
        owner = (
            m.get("ownerReferences", [{}])[0].get("name", "N/A")
            if m.get("ownerReferences")
            else "N/A"
        )

        impl = st.get("implementation", {})
        depapi_status = st.get("depapiStatus", {})

        entry = {
            "name": m["name"],
            "parent": owner,
            "api_name": sp.get("name", "N/A"),
            "api_type": sp.get("apiType", sp.get("apitype", "N/A")),
            "tmf_id": sp.get("id", "N/A"),
            "version": sp.get("version", "N/A"),
            "ready": impl.get("ready", False),
            "url": depapi_status.get("url", "N/A"),
        }

        if entry["ready"]:
            resolved.append(entry)
        else:
            unresolved.append(entry)

    if unresolved:
        print(f"=== UNRESOLVED ({len(unresolved)}) ===")
        for e in unresolved:
            print(f"  {e['name']}")
            print(f"    Parent:   {e['parent']}")
            print(f"    API:      {e['api_name']} ({e['api_type']})")
            print(f"    TMF ID:   {e['tmf_id']}")
            print(f"    Ready:    False")
            print(f"    URL:      {e['url']}")
            print()

    if resolved:
        print(f"=== RESOLVED ({len(resolved)}) ===")
        for e in resolved:
            print(f"  {e['name']}")
            print(f"    Parent:   {e['parent']}")
            print(f"    API:      {e['api_name']} ({e['api_type']})")
            print(f"    TMF ID:   {e['tmf_id']}")
            print(f"    Ready:    True")
            print(f"    URL:      {e['url']}")
            print()

    print(f"Total: {len(items)} DependentAPI(s) — {len(resolved)} resolved, {len(unresolved)} unresolved")


if __name__ == "__main__":
    main()
