"""Check BDD test dependencies — verify node_modules exist in all required directories.

Usage: python check_bdd_deps.py [base-dir]
  base-dir defaults to current directory (should be feature-definition-and-test-kit)
"""
import os
import sys


UTILITY_DIRS = [
    "utilities/identity-manager-utils-keycloak",
    "utilities/package-manager-utils-helm",
    "utilities/resource-inventory-utils-kubernetes",
    "utilities/observability-utils-kubernetes",
    "utilities/component-utils",
]


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    missing = []
    ok = []

    # Check utility sub-packages
    for d in UTILITY_DIRS:
        full = os.path.join(base, d, "node_modules")
        if os.path.isdir(full):
            ok.append(d)
        else:
            missing.append(d)

    # Check main package
    main_nm = os.path.join(base, "node_modules")
    if os.path.isdir(main_nm):
        ok.append("(main)")
    else:
        missing.append("(main)")

    if ok:
        print(f"OK ({len(ok)}):")
        for d in ok:
            print(f"  ✓ {d}")

    if missing:
        print(f"\nMISSING ({len(missing)}):")
        for d in missing:
            print(f"  ✗ {d}")
        print("\nTo install missing dependencies, run:")
        for d in missing:
            if d == "(main)":
                print(f"  cd {base} && npm install")
            else:
                print(f"  cd {os.path.join(base, d)} && npm install")
    else:
        print("\nAll dependencies installed.")


if __name__ == "__main__":
    main()
