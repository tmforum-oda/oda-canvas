"""Drill down into a single ExposedAPI showing full spec including CORS, rate limit, etc.

Usage: kubectl get exposedapi <name> -n components -o json | python parse_exposedapi_drilldown.py
"""
import json
import sys


def print_dict(d, indent=4):
    """Pretty-print a dict with indentation."""
    prefix = " " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            print(f"{prefix}{k}:")
            print_dict(v, indent + 4)
        else:
            print(f"{prefix}{k}: {v}")


def main():
    item = json.load(sys.stdin)
    m = item["metadata"]
    sp = item.get("spec", {})
    st = item.get("status", {})

    print(f"=== ExposedAPI: {m['name']} ===\n")

    # Basic info
    owner = (
        m.get("ownerReferences", [{}])[0].get("name", "N/A")
        if m.get("ownerReferences")
        else "N/A"
    )
    print(f"  Parent Component: {owner}")
    print(f"  Segment:          {sp.get('segment', 'N/A')}")
    print(f"  API Type:         {sp.get('apiType', 'N/A')}")
    print(f"  TMF ID:           {sp.get('id', 'N/A')}")
    print(f"  Implementation:   {sp.get('implementation', 'N/A')}")
    print(f"  Path:             {sp.get('path', 'N/A')}")
    print(f"  Port:             {sp.get('port', 'N/A')}")

    # Specification URLs
    specs = sp.get("specification", [])
    if specs:
        print("\n--- API Specification ---")
        for s_item in specs:
            print(f"    URL: {s_item.get('url', 'N/A')}")

    # CORS
    cors = sp.get("CORS", {})
    print(f"\n--- CORS ---")
    print(f"    Enabled:          {cors.get('enabled', 'N/A')}")
    if cors.get("enabled"):
        print(f"    Allow Origins:    {cors.get('allowOrigins', 'N/A')}")
        print(f"    Allow Credentials:{cors.get('allowCredentials', 'N/A')}")
        preflight = cors.get("handlePreflightRequests", {})
        if preflight:
            print(f"    Preflight Enabled:{preflight.get('enabled', 'N/A')}")
            print(f"    Allow Methods:    {preflight.get('allowMethods', 'N/A')}")
            print(f"    Allow Headers:    {preflight.get('allowHeaders', 'N/A')}")
            print(f"    Max Age:          {preflight.get('maxAge', 'N/A')}")

    # Rate Limiting
    rl = sp.get("rateLimit", {})
    print(f"\n--- Rate Limiting ---")
    print(f"    Enabled:    {rl.get('enabled', 'N/A')}")
    if rl.get("enabled"):
        print(f"    Limit:      {rl.get('limit', 'N/A')}")
        print(f"    Interval:   {rl.get('interval', 'N/A')}")
        print(f"    Identifier: {rl.get('identifier', 'N/A')}")

    # API Key Verification
    akv = sp.get("apiKeyVerification", {})
    print(f"\n--- API Key Verification ---")
    print(f"    Enabled:  {akv.get('enabled', 'N/A')}")
    if akv.get("enabled"):
        print(f"    Location: {akv.get('location', 'N/A')}")

    # OAS Validation
    oas = sp.get("OASValidation", {})
    print(f"\n--- OAS Validation ---")
    print(f"    Request Enabled:  {oas.get('requestEnabled', 'N/A')}")
    print(f"    Response Enabled: {oas.get('responseEnabled', 'N/A')}")

    # Quota
    quota = sp.get("quota", {})
    if quota and (quota.get("limit") or quota.get("identifier")):
        print(f"\n--- Quota ---")
        print(f"    Limit:      {quota.get('limit', 'N/A')}")
        print(f"    Identifier: {quota.get('identifier', 'N/A')}")

    # Status
    print(f"\n--- Status ---")
    impl = st.get("implementation", {})
    api_status = st.get("apiStatus", {})
    print(f"    Ready:        {impl.get('ready', 'N/A')}")
    print(f"    URL:          {api_status.get('url', 'N/A')}")
    print(f"    Developer UI: {api_status.get('developerUI', 'N/A')}")


if __name__ == "__main__":
    main()
