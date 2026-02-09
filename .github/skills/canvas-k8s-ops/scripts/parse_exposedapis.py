"""Parse ExposedAPI list JSON and display structured summary.

Usage: kubectl get exposedapis -n components -o json | python parse_exposedapis.py
"""
import json
import sys


def main():
    data = json.load(sys.stdin)
    items = data.get("items", [])

    if not items:
        print("No ExposedAPIs found.")
        return

    for item in items:
        m = item["metadata"]
        sp = item.get("spec", {})
        st = item.get("status", {})
        owner = (
            m.get("ownerReferences", [{}])[0].get("name", "N/A")
            if m.get("ownerReferences")
            else "N/A"
        )

        print(f"{m['name']}")
        print(f"  Parent:       {owner}")
        print(f"  Segment:      {sp.get('segment', 'N/A')}")
        print(f"  API Type:     {sp.get('apiType', 'N/A')}")
        print(f"  TMF ID:       {sp.get('id', 'N/A')}")
        print(f"  Service:      {sp.get('implementation', 'N/A')}:{sp.get('port', 'N/A')}")
        print(f"  Path:         {sp.get('path', 'N/A')}")
        print(f"  Ready:        {st.get('implementation', {}).get('ready', 'N/A')}")
        print(f"  URL:          {st.get('apiStatus', {}).get('url', 'N/A')}")
        print(f"  Developer UI: {st.get('apiStatus', {}).get('developerUI', 'N/A')}")
        print()

    print(f"Total: {len(items)} ExposedAPI(s)")


if __name__ == "__main__":
    main()
