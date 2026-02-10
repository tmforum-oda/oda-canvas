"""Exercise the TMF620 Product Catalog API to generate metrics and notification events.

Creates and deletes resources across multiple TMF620 resource types (category,
catalog, productSpecification, productOffering) to produce a variety of
notification events visible in the component's Prometheus metrics.

Usage:
  python exercise_catalog_api.py <base-url> [--cleanup] [--rounds N]

Arguments:
  base-url    The TMF620 API base URL, e.g.:
              https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4
  --cleanup   Delete all resources created by this script (tagged with managed-by marker)
  --rounds N  Number of create/delete rounds to run (default: 1)

Examples:
  # Run one round of creates + deletes
  python exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4

  # Run 3 rounds for more metrics data
  python exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4 --rounds 3

  # Clean up all resources created by this script
  python exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4 --cleanup
"""
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

# Disable SSL verification for self-signed certs
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Marker to identify resources created by this script
MARKER = "exercise-catalog-api"

# Sample data for each resource type
SAMPLE_DATA = {
    "category": [
        {"name": "IoT line of product", "description": f"IoT devices and solutions [{MARKER}]"},
        {"name": "Mobile line of product", "description": f"Mobile phones and packages [{MARKER}]"},
        {"name": "Internet line of product", "description": f"Fiber and ADSL broadband [{MARKER}]"},
        {"name": "TV and Media", "description": f"Television and streaming services [{MARKER}]"},
        {"name": "Enterprise Solutions", "description": f"B2B enterprise connectivity [{MARKER}]"},
    ],
    "catalog": [
        {"name": "Main Product Catalog", "description": f"Primary catalog for all products [{MARKER}]"},
        {"name": "Partner Catalog", "description": f"Catalog for partner offerings [{MARKER}]"},
    ],
    "productSpecification": [
        {"name": "5G Home Router", "description": f"High-speed 5G wireless home router [{MARKER}]", "brand": "ODA Telecom", "productNumber": "SPEC-001"},
        {"name": "Fiber ONT", "description": f"Optical network terminal for FTTH [{MARKER}]", "brand": "ODA Telecom", "productNumber": "SPEC-002"},
        {"name": "IoT Gateway", "description": f"Multi-protocol IoT gateway device [{MARKER}]", "brand": "ODA Telecom", "productNumber": "SPEC-003"},
        {"name": "Enterprise SIP Trunk", "description": f"SIP trunking service specification [{MARKER}]", "brand": "ODA Telecom", "productNumber": "SPEC-004"},
    ],
    "productOffering": [
        {"name": "5G Home Unlimited", "description": f"Unlimited 5G home broadband plan [{MARKER}]"},
        {"name": "Fiber 1Gbps", "description": f"1 Gbps fiber broadband offering [{MARKER}]"},
        {"name": "IoT Starter Pack", "description": f"IoT connectivity starter package [{MARKER}]"},
    ],
}


def api_request(url, method="GET", data=None):
    """Make an HTTP request to the TMF620 API."""
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=SSL_CTX) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 204:
            return None
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"  ERROR {e.code}: {body_text[:200]}")
        return None


def list_resources(base_url, resource_type):
    """List all resources of a given type."""
    return api_request(f"{base_url}/{resource_type}") or []


def create_resource(base_url, resource_type, data):
    """Create a resource and return its ID."""
    result = api_request(f"{base_url}/{resource_type}", method="POST", data=data)
    if result and "id" in result:
        return result["id"]
    return None


def delete_resource(base_url, resource_type, resource_id):
    """Delete a resource by ID."""
    api_request(f"{base_url}/{resource_type}/{resource_id}", method="DELETE")


def is_managed(resource):
    """Check if a resource was created by this script."""
    desc = resource.get("description", "")
    return MARKER in desc


def cleanup(base_url):
    """Delete all resources created by this script."""
    print("\n=== CLEANUP: Removing resources created by this script ===\n")
    total_deleted = 0
    for resource_type in SAMPLE_DATA:
        resources = list_resources(base_url, resource_type)
        managed = [r for r in resources if is_managed(r)]
        if not managed:
            print(f"  {resource_type}: no managed resources found")
            continue
        for r in managed:
            print(f"  DELETE {resource_type}/{r['id']} ({r.get('name', '?')})")
            delete_resource(base_url, resource_type, r["id"])
            total_deleted += 1
        time.sleep(0.2)
    print(f"\nDeleted {total_deleted} resource(s)")


def run_round(base_url, round_num, total_rounds):
    """Run one create/delete round."""
    print(f"\n{'='*60}")
    print(f"  ROUND {round_num}/{total_rounds}")
    print(f"{'='*60}")

    created = {}  # resource_type -> [ids]
    total_creates = 0
    total_deletes = 0

    # Phase 1: Create resources
    print("\n--- Phase 1: Creating resources ---\n")
    for resource_type, samples in SAMPLE_DATA.items():
        created[resource_type] = []
        for sample in samples:
            rid = create_resource(base_url, resource_type, sample)
            if rid:
                created[resource_type].append(rid)
                total_creates += 1
                event_type = resource_type[0].upper() + resource_type[1:]
                print(f"  POST {resource_type} -> {rid[:12]}... ({sample['name']})  [{event_type}CreationNotification]")
            time.sleep(0.1)  # small delay to avoid overwhelming the API

    print(f"\n  Created: {total_creates} resources")

    # Phase 2: Delete some resources (half of each type) to generate Remove events
    print("\n--- Phase 2: Deleting resources (generating RemoveNotifications) ---\n")
    for resource_type, ids in created.items():
        # Delete roughly half
        to_delete = ids[: len(ids) // 2]
        for rid in to_delete:
            print(f"  DELETE {resource_type}/{rid[:12]}...")
            delete_resource(base_url, resource_type, rid)
            total_deletes += 1
            time.sleep(0.1)

    print(f"\n  Deleted: {total_deletes} resources")
    print(f"  Remaining: {total_creates - total_deletes} resources")
    return total_creates, total_deletes


def main():
    if len(sys.argv) < 2:
        print("Usage: python exercise_catalog_api.py <base-url> [--cleanup] [--rounds N]")
        print()
        print("Example:")
        print("  python exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    do_cleanup = "--cleanup" in sys.argv
    rounds = 1
    if "--rounds" in sys.argv:
        idx = sys.argv.index("--rounds")
        if idx + 1 < len(sys.argv):
            rounds = int(sys.argv[idx + 1])

    print(f"TMF620 Product Catalog API Exerciser")
    print(f"Base URL: {base_url}")
    print(f"Resource types: {', '.join(SAMPLE_DATA.keys())}")

    if do_cleanup:
        cleanup(base_url)
        return

    print(f"Rounds: {rounds}")

    grand_creates = 0
    grand_deletes = 0
    for i in range(1, rounds + 1):
        c, d = run_round(base_url, i, rounds)
        grand_creates += c
        grand_deletes += d

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total notification events generated:")
    print(f"    Creation events: {grand_creates}")
    print(f"    Remove events:   {grand_deletes}")
    print(f"    Total events:    {grand_creates + grand_deletes}")
    print()
    print(f"  Resources remaining in API: {grand_creates - grand_deletes}")
    print(f"  Use --cleanup to remove all managed resources")
    print()
    print(f"  Check metrics:")
    print(f"    Prometheus: product_catalog_api_counter")
    print(f"    Direct:     kubectl exec -n components deploy/<release>-metricsapi -- wget -qO- http://localhost:4000/<component>/metrics")


if __name__ == "__main__":
    main()
