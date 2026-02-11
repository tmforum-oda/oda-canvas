"""Parse a single IdentityConfig JSON from kubectl into a detailed view."""
import json
import sys


def main():
    data = json.load(sys.stdin)
    spec = data.get("spec", {})
    status = data.get("status", {}).get("identityConfig", {})
    meta = data.get("metadata", {})

    print("=" * 60)
    print(f"  IdentityConfig: {meta.get('name', '?')}")
    print("=" * 60)

    # Owner
    owners = meta.get("ownerReferences", [])
    if owners:
        print(f"\n  Parent Component: {owners[0].get('name', '?')}")

    # Canvas system role
    canvas_role = spec.get("canvasSystemRole")
    if canvas_role:
        print(f"  Canvas System Role: {canvas_role}")

    # Identity provider
    provider = status.get("identityProvider", "—")
    listener = status.get("listenerRegistered", "—")
    print(f"\n  Identity Provider: {provider}")
    print(f"  Listener Registered: {listener}")

    # Static component roles
    roles = spec.get("componentRole", [])
    if roles:
        print(f"\n  Static Component Roles ({len(roles)}):")
        for r in roles:
            desc = f" — {r['description']}" if r.get("description") else ""
            print(f"    - {r['name']}{desc}")

    # Permission Specification Set API (dynamic roles)
    pss = spec.get("permissionSpecificationSetAPI")
    if pss:
        print("\n  Permission Specification Set API (dynamic roles):")
        print(f"    Implementation: {pss.get('implementation', '?')}")
        print(f"    Path:           {pss.get('path', '?')}")
        print(f"    Port:           {pss.get('port', '?')}")

    # Party Role API (legacy, dynamic roles)
    pr = spec.get("partyRoleAPI")
    if pr:
        print("\n  Party Role API (legacy dynamic roles):")
        print(f"    Implementation: {pr.get('implementation', '?')}")
        print(f"    Path:           {pr.get('path', '?')}")
        print(f"    Port:           {pr.get('port', '?')}")

    if not pss and not pr and not roles:
        print("\n  No role configuration found.")

    print()


if __name__ == "__main__":
    main()
