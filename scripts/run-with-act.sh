#!/bin/bash
set -e

# Script to run GitHub Actions workflows locally using act
# https://github.com/nektos/act

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if act is installed
install_act() {
    if ! command -v act &> /dev/null; then
        log_info "act not found. Installing..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install act
            else
                log_error "Homebrew not found. Please install act manually:"
                echo "  curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
        else
            log_error "Unsupported OS. Please install act manually from: https://github.com/nektos/act"
            exit 1
        fi
    fi
    
    log_success "act is installed: $(act --version)"
}

# Create act configuration
create_act_config() {
    log_info "Creating act configuration..."
    
    # Create .actrc file for default settings
    cat > "$PROJECT_ROOT/.actrc" <<EOF
# Act configuration for Canvas ODA testing
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04
--container-architecture linux/amd64
--container-daemon-socket -
EOF
    
    # Create secrets file if needed
    if [ ! -f "$PROJECT_ROOT/.secrets" ]; then
        cat > "$PROJECT_ROOT/.secrets" <<EOF
# GitHub secrets for local testing
# Add any required secrets here in KEY=VALUE format
# GITHUB_TOKEN=your_token_here
EOF
    fi
    
    log_success "Act configuration created"
}

# Run specific workflow
run_workflow() {
    local workflow=$1
    local job=$2
    local event=$3
    
    cd "$PROJECT_ROOT"
    
    log_info "Running workflow: $workflow"
    
    local act_args=(
        "--verbose"
        "--rm"
        "--pull=false"
    )
    
    # Add workflow file if specified
    if [ -n "$workflow" ]; then
        act_args+=("-W" ".github/workflows/$workflow")
    fi
    
    # Add job if specified
    if [ -n "$job" ]; then
        act_args+=("-j" "$job")
    fi
    
    # Add event type
    if [ -n "$event" ]; then
        act_args+=("$event")
    else
        act_args+=("push")
    fi
    
    # Run act
    act "${act_args[@]}"
}

# Quick test function
quick_test() {
    log_info "Running quick PDB operator test..."
    
    cd "$PROJECT_ROOT"
    
    # Run the local test workflow
    act push \
        -W .github/workflows/local-test.yml \
        -j test-canvas-installation \
        --container-architecture linux/amd64 \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest
}

# Full test function (original workflow)
full_test() {
    log_info "Running full Canvas test workflow..."
    
    cd "$PROJECT_ROOT"
    
    # Run the full trigger_test workflow
    act pull_request \
        -W .github/workflows/trigger_test.yml \
        -j run_tests_job \
        --container-architecture linux/amd64 \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest
}

# List available workflows
list_workflows() {
    log_info "Available workflows:"
    
    for workflow in "$PROJECT_ROOT"/.github/workflows/*.yml; do
        if [ -f "$workflow" ]; then
            local name=$(basename "$workflow")
            echo "  - $name"
            
            # Extract jobs from workflow
            local jobs=$(grep -E '^\s{2}[a-zA-Z_-]+:$' "$workflow" | sed 's/://g' | sed 's/^  //')
            if [ -n "$jobs" ]; then
                echo "    Jobs:"
                while IFS= read -r job; do
                    echo "      * $job"
                done <<< "$jobs"
            fi
        fi
    done
}

# Show help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  quick        Run quick PDB operator test"
    echo "  full         Run full Canvas test suite"
    echo "  list         List available workflows"
    echo "  run <workflow> [job] [event]  Run specific workflow"
    echo "  install      Install act if not present"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 quick                    # Run quick test"
    echo "  $0 full                     # Run full test suite"
    echo "  $0 run trigger_test.yml     # Run specific workflow"
    echo "  $0 run local-test.yml test-canvas-installation push"
    echo ""
    echo "Note: This script uses 'act' to run GitHub Actions locally."
    echo "      Learn more: https://github.com/nektos/act"
}

# Main execution
main() {
    echo -e "${GREEN}Canvas ODA GitHub Actions Local Runner${NC}"
    echo "======================================="
    
    case "${1:-help}" in
        quick)
            install_act
            create_act_config
            quick_test
            ;;
        full)
            install_act
            create_act_config
            full_test
            ;;
        list)
            list_workflows
            ;;
        run)
            install_act
            create_act_config
            run_workflow "$2" "$3" "$4"
            ;;
        install)
            install_act
            create_act_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"