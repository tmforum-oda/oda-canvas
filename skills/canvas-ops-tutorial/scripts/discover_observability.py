"""Discover observability services from kubectl get svc -A output (JSON).

Usage: kubectl get svc -A -o json | python discover_observability.py
"""
import json
import sys


OBSERVABILITY_KEYWORDS = ["prometheus", "grafana", "jaeger", "opentelemetry"]

PORT_FORWARD_MAP = {
    "prometheus": {"local_port": 9090, "description": "Prometheus UI"},
    "grafana": {"local_port": 3000, "description": "Grafana UI"},
    "jaeger-query": {"local_port": 16686, "description": "Jaeger UI"},
}


def main():
    data = json.load(sys.stdin)
    items = data.get("items", [])

    found = []
    for item in items:
        name = item["metadata"]["name"]
        ns = item["metadata"]["namespace"]
        svc_type = item["spec"]["type"]
        ports = item["spec"].get("ports", [])
        port_strs = [f"{p.get('port', '?')}/{p.get('protocol', 'TCP')}" for p in ports]

        if any(kw in name.lower() for kw in OBSERVABILITY_KEYWORDS):
            found.append({
                "name": name,
                "namespace": ns,
                "type": svc_type,
                "ports": ", ".join(port_strs),
            })

    if not found:
        print("No observability services found (Prometheus, Grafana, Jaeger, OpenTelemetry).")
        print()
        print("The observability stack is optional. To install:")
        print("  See: https://github.com/tmforum-oda/oda-canvas/tree/main/charts/observability-stack")
        print()
        print("Quick install:")
        print("  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts")
        print("  helm repo add opentelemetry https://open-telemetry.github.io/opentelemetry-helm-charts")
        print("  helm repo add jaegertracing https://jaegertracing.github.io/helm-charts")
        print("  helm repo update")
        print("  cd charts && helm dependency build observability-stack")
        print("  helm install observability ./observability-stack --create-namespace --namespace monitoring")
        return

    print(f"=== Observability Services Found ({len(found)}) ===\n")
    for svc in found:
        print(f"  {svc['name']}")
        print(f"    Namespace: {svc['namespace']}")
        print(f"    Type:      {svc['type']}")
        print(f"    Ports:     {svc['ports']}")
        print()

    # Suggest port-forward commands
    print("--- Suggested port-forward commands ---")
    ns = found[0]["namespace"]  # use namespace of first found service
    for svc in found:
        for key, pf in PORT_FORWARD_MAP.items():
            if key in svc["name"].lower():
                target_port = None
                for p in svc["ports"].split(", "):
                    port_num = p.split("/")[0]
                    if port_num.isdigit():
                        target_port = port_num
                        break
                if target_port:
                    print(f"  kubectl port-forward svc/{svc['name']} {pf['local_port']}:{target_port} -n {svc['namespace']}  # {pf['description']}")
                break


if __name__ == "__main__":
    main()
