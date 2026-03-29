# PDB Management Operator - Grafana Dashboard Import Guide

## 📊 **Fixed Dashboard Files**

The following corrected dashboard files are ready for import:

- `pdb-operator-overview-fixed.json` - Main operational overview
- `pdb-operator-policy-analysis-fixed.json` - Policy enforcement analysis
- `pdb-operator-troubleshooting-fixed.json` - Error diagnosis and debugging
- `pdb-operator-traces-fixed.json` - Distributed tracing visualization

## 🔧 **What Was Fixed**

All dashboard queries have been updated to use the correct metric labels:

**Before (broken):**

```promql
controller_runtime_reconcile_total{app_kubernetes_io_name="pdb-management"}
```

**After (working):**

```promql
controller_runtime_reconcile_total{job="pdb-management-operator"}
```

## 📥 **Import Instructions**

### Method 1: Manual Import via Grafana UI

1. **Access Grafana**: http://localhost:3000 (admin/admin123)
2. **Navigate**: + → Import
3. **Upload JSON**: Select each `*-fixed.json` file
4. **Configure**:
   - Select **Prometheus** data source: `prometheus-stack-kube-prom-prometheus`
   - Select **Loki** data source: `loki`
   - Select **Tempo** data source: `tempo`
5. **Import**: Click "Import"

### Method 2: Automated Import via API

```bash
# Set Grafana credentials
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"

# Import all fixed dashboards
for dashboard in config/grafana/*-fixed.json; do
  echo "Importing $dashboard..."
  curl -X POST \
    -H "Content-Type: application/json" \
    -d "{\"dashboard\":$(cat "$dashboard"),\"overwrite\":true}" \
    "$GRAFANA_URL/api/dashboards/db" \
    -u "$GRAFANA_USER:$GRAFANA_PASS"
done
```

## 📈 **Expected Data**

With the corrected dashboards, you should immediately see:

### Overview Dashboard:

- **~338 Total Reconciliations**
- **Reconciliation rates** (deployments and policies)
- **P95 Latency metrics**
- **Active worker counts**

### Policy Analysis Dashboard:

- **6 Active Policies** (from your test)
- **Enforcement decisions**
- **Compliance rates**

### Troubleshooting Dashboard:

- **Error counts** (~4 AvailabilityPolicy errors)
- **Performance metrics**
- **Resource usage**

### Traces Dashboard:

- **Trace volume and latency**
- **Correlated logs and traces**

## 🔍 **Verification**

After import, verify the data is showing by checking:

1. **Prometheus Targets**: http://localhost:9090/targets

   - Look for `pdb-management-operator` targets (should be "UP")

2. **Sample Query**: In Grafana Explore, try:

   ```promql
   sum(controller_runtime_reconcile_total{job="pdb-management-operator"})
   ```

   Should return: **~338**

3. **Dashboard Panels**: All panels should show data instead of "No data"

## 🚨 **Troubleshooting**

### If dashboards still show no data:

1. **Check data sources**: Ensure Prometheus/Loki/Tempo are properly configured
2. **Check time range**: Set to "Last 1 hour" or "Last 30 minutes"
3. **Check targets**: Verify operator metrics are being scraped
4. **Check query**: Use Grafana Explore to test individual queries

### If import fails:

1. **Check JSON syntax**: Ensure files are valid JSON
2. **Check permissions**: Ensure admin access to Grafana
3. **Check data sources**: Create Prometheus/Loki/Tempo data sources first

## 📋 **Sample Working Queries**

These queries should return data in your Grafana:

```promql
# Total reconciliations
sum(controller_runtime_reconcile_total{job="pdb-management-operator"})

# Reconciliation rate
rate(controller_runtime_reconcile_total{job="pdb-management-operator"}[5m]) * 60

# P95 latency
histogram_quantile(0.95, sum(rate(controller_runtime_reconcile_time_seconds_bucket{job="pdb-management-operator"}[5m])) by (le)) * 1000

# Error rate
rate(controller_runtime_reconcile_errors_total{job="pdb-management-operator"}[5m]) * 60
```

## 🎯 **Success Indicators**

✅ All dashboard panels show data  
✅ Reconciliation metrics show ~338 total  
✅ Latency charts show realistic values (1-10ms)  
✅ Error rates show minimal errors  
✅ Time series charts show activity patterns
