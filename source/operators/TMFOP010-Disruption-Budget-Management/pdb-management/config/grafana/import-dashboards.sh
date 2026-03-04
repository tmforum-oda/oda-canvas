#!/bin/bash

# PDB Management Operator - Dashboard Import Script
# This script imports all Grafana dashboards for the PDB Management Operator

set -euo pipefail

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
DASHBOARD_DIR="$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

log_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "║        PDB Management Operator - Dashboard Import Tool           ║"
    echo "═══════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Test Grafana connectivity
test_grafana_connection() {
    log_info "Testing connection to Grafana at ${GRAFANA_URL}..."
    
    local response
    response=$(curl -s -w "%{http_code}" -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_URL}/api/health" -o /dev/null || echo "000")
    
    if [ "$response" != "200" ]; then
        log_error "Failed to connect to Grafana (HTTP $response)"
        log_error "Please check:"
        log_error "  - GRAFANA_URL is correct: ${GRAFANA_URL}"
        log_error "  - GRAFANA_USER is correct: ${GRAFANA_USER}"
        log_error "  - GRAFANA_PASSWORD is correct"
        log_error "  - Grafana is running and accessible"
        exit 1
    fi
    
    log_success "Connected to Grafana successfully"
}

# Get or create folder
setup_dashboard_folder() {
    log_info "Setting up dashboard folder..."
    
    local folder_title="PDB Management Operator"
    local folder_uid="pdb-operator"
    
    # Check if folder exists
    local folder_response
    folder_response=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_URL}/api/folders/${folder_uid}" || echo '{"message":"not found"}')
    
    if echo "$folder_response" | jq -e '.message' | grep -q "not found"; then
        log_info "Creating dashboard folder: ${folder_title}"
        
        local create_response
        create_response=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
            -H "Content-Type: application/json" \
            -X POST "${GRAFANA_URL}/api/folders" \
            -d "{\"uid\":\"${folder_uid}\",\"title\":\"${folder_title}\"}")
        
        if echo "$create_response" | jq -e '.id' > /dev/null; then
            log_success "Created folder: ${folder_title}"
        else
            log_warning "Failed to create folder, continuing with default"
        fi
    else
        log_success "Using existing folder: ${folder_title}"
    fi
    
    echo "$folder_uid"
}

# Import a single dashboard
import_dashboard() {
    local dashboard_file="$1"
    local folder_uid="$2"
    local dashboard_name
    dashboard_name=$(basename "$dashboard_file" .json)
    
    log_info "Importing dashboard: ${dashboard_name}"
    
    # Read and modify dashboard JSON
    local dashboard_json
    dashboard_json=$(cat "$dashboard_file")
    
    # Wrap in import format and set folder
    local import_json
    import_json=$(echo "$dashboard_json" | jq --arg folder "$folder_uid" '{
        dashboard: (. + {id: null, folderId: null}),
        folderId: null,
        folderUid: $folder,
        message: "Imported via script",
        overwrite: true
    }')
    
    # Import dashboard
    local response
    response=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -H "Content-Type: application/json" \
        -X POST "${GRAFANA_URL}/api/dashboards/db" \
        -d "$import_json")
    
    if echo "$response" | jq -e '.status' | grep -q "success"; then
        local dashboard_uid
        dashboard_uid=$(echo "$response" | jq -r '.uid')
        local dashboard_url="${GRAFANA_URL}/d/${dashboard_uid}"
        log_success "Imported: ${dashboard_name} (${dashboard_url})"
        return 0
    else
        local error_message
        error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
        log_error "Failed to import ${dashboard_name}: ${error_message}"
        return 1
    fi
}

# Import all dashboards
import_all_dashboards() {
    local folder_uid="$1"
    local success_count=0
    local total_count=0
    
    log_info "Importing dashboards from: ${DASHBOARD_DIR}"
    
    # Find all dashboard JSON files
    local dashboard_files=()
    while IFS= read -r -d '' file; do
        dashboard_files+=("$file")
    done < <(find "$DASHBOARD_DIR" -name "*.json" -not -name "import-*" -print0)
    
    if [ ${#dashboard_files[@]} -eq 0 ]; then
        log_warning "No dashboard files found in ${DASHBOARD_DIR}"
        return 0
    fi
    
    # Import each dashboard
    for dashboard_file in "${dashboard_files[@]}"; do
        ((total_count++))
        if import_dashboard "$dashboard_file" "$folder_uid"; then
            ((success_count++))
        fi
    done
    
    # Summary
    echo ""
    log_info "Import Summary:"
    log_info "  Total dashboards: ${total_count}"
    log_success "  Successfully imported: ${success_count}"
    
    if [ $success_count -lt $total_count ]; then
        log_warning "  Failed imports: $((total_count - success_count))"
        return 1
    fi
    
    return 0
}

# Verify dashboard data sources
verify_data_sources() {
    log_info "Checking data source availability..."
    
    # Get all data sources
    local datasources_response
    datasources_response=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        "${GRAFANA_URL}/api/datasources")
    
    # Check for required data source types
    local required_types=("prometheus" "loki" "tempo")
    local missing_types=()
    
    for type in "${required_types[@]}"; do
        if ! echo "$datasources_response" | jq -e ".[] | select(.type == \"$type\")" > /dev/null; then
            missing_types+=("$type")
        fi
    done
    
    if [ ${#missing_types[@]} -eq 0 ]; then
        log_success "All required data sources are configured"
    else
        log_warning "Missing data source types: ${missing_types[*]}"
        log_warning "Some dashboard panels may not work correctly"
        log_info "Configure these data sources in Grafana:"
        for type in "${missing_types[@]}"; do
            log_info "  - ${type}"
        done
    fi
}

# Print usage instructions
print_usage() {
    log_info "Dashboard URLs (after import):"
    log_info "  Overview: ${GRAFANA_URL}/d/pdb-operator-overview"
    log_info "  Policy Analysis: ${GRAFANA_URL}/d/pdb-operator-policies"
    log_info "  Troubleshooting: ${GRAFANA_URL}/d/pdb-operator-troubleshooting"
    log_info "  Distributed Tracing: ${GRAFANA_URL}/d/pdb-operator-traces"
    echo ""
    log_info "Next steps:"
    log_info "  1. Configure your data sources if not already done"
    log_info "  2. Verify metrics are being collected: ${GRAFANA_URL}/explore"
    log_info "  3. Set up alerting rules based on dashboard metrics"
    log_info "  4. Customize thresholds and time ranges as needed"
}

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Import PDB Management Operator dashboards into Grafana"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --url URL           Grafana URL (default: http://localhost:3000)"
    echo "  --user USER             Grafana username (default: admin)"
    echo "  --password PASSWORD     Grafana password (default: admin)"
    echo "  --dry-run               Show what would be imported without doing it"
    echo ""
    echo "Environment Variables:"
    echo "  GRAFANA_URL             Grafana URL"
    echo "  GRAFANA_USER            Grafana username"
    echo "  GRAFANA_PASSWORD        Grafana password"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --url http://grafana:3000 --user myuser --password mypass"
    echo "  GRAFANA_URL=https://grafana.example.com $0"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--url)
                GRAFANA_URL="$2"
                shift 2
                ;;
            --user)
                GRAFANA_USER="$2"
                shift 2
                ;;
            --password)
                GRAFANA_PASSWORD="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    parse_args "$@"
    
    print_banner
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "DRY RUN MODE - No changes will be made"
        log_info "Would import dashboards from: ${DASHBOARD_DIR}"
        find "$DASHBOARD_DIR" -name "*.json" -not -name "import-*" -exec basename {} .json \; | while read -r name; do
            log_info "  - $name"
        done
        exit 0
    fi
    
    check_prerequisites
    test_grafana_connection
    verify_data_sources
    
    local folder_uid
    folder_uid=$(setup_dashboard_folder)
    
    if import_all_dashboards "$folder_uid"; then
        echo ""
        log_success "All dashboards imported successfully!"
        print_usage
        exit 0
    else
        echo ""
        log_error "Some dashboards failed to import"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 