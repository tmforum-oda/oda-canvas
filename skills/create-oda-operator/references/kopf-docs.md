# Kopf Documentation Reference

Full documentation index: https://docs.kopf.dev/en/stable/

The ODA Canvas uses **kopf==1.37.2**, but all patterns described here apply. Links point to the
stable doc channel which reflects the current maintained release.

---

## Handler Types

| Topic | URL | When to consult |
|---|---|---|
| Handlers overview | https://docs.kopf.dev/en/stable/handlers/ | All handler types: create, update, resume, delete, field, event, sub-handlers — start here |
| Timers | https://docs.kopf.dev/en/stable/timers/ | `@kopf.timer()` — periodic execution with `interval`, `idle`, `initial_delay`, `sharp` |
| Daemons | https://docs.kopf.dev/en/stable/daemons/ | Long-running `async` tasks per resource (alternative to timers for continuous work) |
| Admission control | https://docs.kopf.dev/en/stable/admission/ | `@kopf.on.mutate()` / `@kopf.on.validate()` webhooks, webhook servers/tunnels, managed configs |
| Arguments reference | https://docs.kopf.dev/en/stable/kwargs/ | Complete list of handler kwargs: `body`, `spec`, `status`, `meta`, `patch`, `logger`, `retry`, `diff`, `old`, `new` |
| Filtering | https://docs.kopf.dev/en/stable/filters/ | `labels=`, `annotations=`, `field=`, `when=` callback filters on any handler |
| Results delivery | https://docs.kopf.dev/en/stable/results/ | How handler return values are written to `status` sub-resource |
| Error handling | https://docs.kopf.dev/en/stable/errors/ | `TemporaryError`, `PermanentError`, `errors=ErrorsMode`, `retries=`, `backoff=`, `timeout=` |
| Async/Await | https://docs.kopf.dev/en/stable/async/ | When to use `async def` vs sync, configuring the sync thread pool |
| Sub-handlers | https://docs.kopf.dev/en/stable/handlers/#sub-handlers | `kopf.subhandler()` / `kopf.execute()` for per-item lifecycle within a list |
| Scopes | https://docs.kopf.dev/en/stable/scopes/ | Namespace-scoped (`-n`) vs cluster-wide (`-A`) operator modes |
| Resource specification | https://docs.kopf.dev/en/stable/resources/ | Selector syntax (group/version/plural), by-category, catch-all |

---

## Operator Configuration

| Topic | URL | When to consult |
|---|---|---|
| Startup | https://docs.kopf.dev/en/stable/startup/ | `@kopf.on.startup()` hook and `kopf.OperatorSettings` object |
| Configuration | https://docs.kopf.dev/en/stable/configuration/ | All settings: `watching.*`, `posting.*`, `execution.*`, `networking.*`, `persistence.*`, `scanning.*` |
| Peering | https://docs.kopf.dev/en/stable/peering/ | Multi-operator coordination, `priority`, `ClusterKopfPeering`, standalone mode |
| Health checks | https://docs.kopf.dev/en/stable/probing/ | `@kopf.on.probe()`, liveness HTTP endpoint, Kubernetes probe integration |
| Authentication | https://docs.kopf.dev/en/stable/authentication/ | Custom Kubernetes client auth, `login_via_client()` |
| Command-line options | https://docs.kopf.dev/en/stable/cli/ | All `kopf run` flags: `--namespace` / `-n`, `--all-namespaces` / `-A`, `--standalone`, `--priority`, `--dev`, `--verbose`, `--log-format` |

---

## Toolkits & Patterns

| Topic | URL | When to consult |
|---|---|---|
| Hierarchies | https://docs.kopf.dev/en/stable/hierarchies/ | `kopf.adopt()`, `kopf.label()`, `kopf.harmonize_naming()`, `kopf.adjust_namespace()`, `kopf.append_owner_reference()` |
| Events | https://docs.kopf.dev/en/stable/events/ | `kopf.info()`, `kopf.warn()`, `kopf.exception()` — posting Kubernetes events from handlers |
| In-memory containers | https://docs.kopf.dev/en/stable/memos/ | `memo` kwarg — sharing state between handlers for the same resource without K8s API calls |
| In-memory indexing | https://docs.kopf.dev/en/stable/indexing/ | `@kopf.index()` — build in-memory lookup tables of resources for fast cross-resource queries |
| Patching | https://docs.kopf.dev/en/stable/patches/ | Modifying the `patch` object in mutation webhooks; dictionary merge behaviour |
| Loading and importing | https://docs.kopf.dev/en/stable/loading/ | Splitting operators across multiple Python files/modules |

---

## Deployment & Operations

| Topic | URL | When to consult |
|---|---|---|
| Docker image | https://docs.kopf.dev/en/stable/docker/ | Dockerfile patterns, image variants (`slim`, `alpine`), passing CLI options via `CMD` |
| Deployment | https://docs.kopf.dev/en/stable/deployment/ | RBAC setup (ServiceAccount + ClusterRole + ClusterRoleBinding), service account template |
| Continuity | https://docs.kopf.dev/en/stable/continuity/ | How kopf persists state across restarts; finalizers; progress storage |
| Idempotence | https://docs.kopf.dev/en/stable/idempotence/ | Making handlers safe to re-run; get-or-create patterns; 409 Conflict handling |
| Reconciliation | https://docs.kopf.dev/en/stable/reconciliation/ | Edge-based vs level-based triggering; when to use timers/daemons for reconciliation |
| Tips & Tricks | https://docs.kopf.dev/en/stable/tips-and-tricks/ | Excluding handlers forever (`errors=IGNORED`), other advanced techniques |
| Troubleshooting | https://docs.kopf.dev/en/stable/troubleshooting/ | `kubectl delete` freezes (finalizer issues), stale watch streams |

---

## Testing

| Topic | URL | When to consult |
|---|---|---|
| Operator testing | https://docs.kopf.dev/en/stable/testing/ | `kopf.testing.KopfRunner` for integration tests; KMock for unit tests without a real cluster |
