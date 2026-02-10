"""Parse ODA Component list JSON and display structured summary.

Usage: kubectl get components -n components -o json | python parse_components.py
"""
import json
import sys


def main():
    data = json.load(sys.stdin)
    items = data.get("items", [])

    if not items:
        print("No ODA Components found.")
        return

    for item in items:
        name = item["metadata"]["name"]
        ns = item["metadata"]["namespace"]
        status = item.get("status", {})
        summary = status.get("summary/status", {})
        dep_status = summary.get("deployment_status", "Unknown")

        core_apis = status.get("coreAPIs", [])
        mgmt_apis = status.get("managementAPIs", [])
        sec_apis = status.get("securityAPIs", [])
        core_dep = status.get("coreDependentAPIs", [])
        mgmt_dep = status.get("managementDependentAPIs", [])
        sec_dep = status.get("securityDependentAPIs", [])
        pub_events = status.get("publishedEvents", [])
        sub_events = status.get("subscribedEvents", [])

        core_ready = sum(1 for a in core_apis if a.get("ready"))
        mgmt_ready = sum(1 for a in mgmt_apis if a.get("ready"))
        sec_ready = sum(1 for a in sec_apis if a.get("ready"))
        cdep_ready = sum(1 for a in core_dep if a.get("ready"))
        mdep_ready = sum(1 for a in mgmt_dep if a.get("ready"))
        sdep_ready = sum(1 for a in sec_dep if a.get("ready"))

        print(f"Component: {name}")
        print(f"  Namespace:            {ns}")
        print(f"  Deployment Status:    {dep_status}")
        print(f"  Core APIs:            {core_ready}/{len(core_apis)} ready")
        print(f"  Management APIs:      {mgmt_ready}/{len(mgmt_apis)} ready")
        print(f"  Security APIs:        {sec_ready}/{len(sec_apis)} ready")
        print(f"  Core Dependent APIs:  {cdep_ready}/{len(core_dep)} ready")
        print(f"  Mgmt Dependent APIs:  {mdep_ready}/{len(mgmt_dep)} ready")
        print(f"  Sec Dependent APIs:   {sdep_ready}/{len(sec_dep)} ready")
        print(f"  Published Events:     {len(pub_events)}")
        print(f"  Subscribed Events:    {len(sub_events)}")
        print()

    print(f"Total: {len(items)} component(s)")


if __name__ == "__main__":
    main()
