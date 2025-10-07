#!/usr/bin/env bash
# Test script for validating all compose templates with dry-run
# This script iterates through all templates and runs a non-interactive dry-run
# Output is GitHub Actions friendly and easy to parse

set -euo pipefail

# Colors for output (only if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Counters
TOTAL=0
PASSED=0
FAILED=0
FAILED_TEMPLATES=()

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Function to print status (GitHub Actions annotations format)
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo "[INFO] ${message}"
            ;;
        "SUCCESS")
            echo "[PASS] ${message}"
            ;;
        "ERROR")
            echo "[FAIL] ${message}"
            # GitHub Actions error annotation
            if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
                echo "::error::${message}"
            fi
            ;;
        "WARNING")
            echo "[WARN] ${message}"
            if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
                echo "::warning::${message}"
            fi
            ;;
    esac
}

# Function to test a single template
test_template() {
    local template_id=$1
    local template_name=$2
    
    TOTAL=$((TOTAL + 1))
    
    print_status "INFO" "Testing: ${template_id}"
    
    # Run the generate command with dry-run and no-interactive
    # Capture stderr for error reporting
    local temp_stderr=$(mktemp)
    if python3 -m cli compose generate "${template_id}" \
        --dry-run \
        --no-interactive \
        > /dev/null 2>"${temp_stderr}"; then
        print_status "SUCCESS" "${template_id}"
        PASSED=$((PASSED + 1))
        rm -f "${temp_stderr}"
        return 0
    else
        print_status "ERROR" "${template_id}"
        FAILED=$((FAILED + 1))
        FAILED_TEMPLATES+=("${template_id}")
        
        # Show error message from stderr
        if [[ -s "${temp_stderr}" ]]; then
            local error_msg=$(cat "${temp_stderr}" | tr '\n' ' ')
            if [[ -n "${error_msg}" ]]; then
                echo "  └─ ${error_msg}"
            fi
        fi
        rm -f "${temp_stderr}"
        return 1
    fi
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"
    
    echo "=========================================="
    echo "Compose Template Dry-Run Tests"
    echo "=========================================="
    print_status "INFO" "Working directory: ${PROJECT_ROOT}"
    echo ""
    
    # Get list of all compose templates
    local templates
    if ! templates=$(python3 -m cli compose list --raw 2>&1); then
        print_status "ERROR" "Failed to retrieve template list"
        echo "${templates}"
        exit 1
    fi
    
    # Count total templates
    local template_count
    template_count=$(echo "${templates}" | wc -l | tr -d ' ')
    
    print_status "INFO" "Found ${template_count} templates to test"
    echo ""
    
    # Iterate through each template
    while IFS=$'\t' read -r template_id template_name tags version library; do
        # Continue even if test fails (don't let set -e stop us)
        test_template "${template_id}" "${template_name}" || true
    done <<< "${templates}"
    
    # Print summary
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Total:    ${TOTAL}"
    echo "Passed:   ${PASSED}"
    echo "Failed:   ${FAILED}"
    
    # List failed templates if any
    if [ "${FAILED}" -gt 0 ]; then
        echo ""
        echo "Failed templates:"
        for template in "${FAILED_TEMPLATES[@]}"; do
            echo "  - ${template}"
        done
        echo ""
        print_status "ERROR" "${FAILED} template(s) failed validation"
        exit 1
    else
        echo ""
        print_status "SUCCESS" "All templates passed validation!"
    fi
}

# Run main function
main "$@"
