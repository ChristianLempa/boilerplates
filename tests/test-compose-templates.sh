#!/usr/bin/env bash
# Test script for validating all compose templates
# This script iterates through all templates and runs validation
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

# Function to validate and test a single template
validate_template() {
    local template_id=$1
    local template_name=$2
    
    TOTAL=$((TOTAL + 1))
    
    echo -e "${BLUE}────────────────────────────────────────${NC}"
    print_status "INFO" "Testing: ${template_id} (${template_name})"
    
    # Step 1: Run validation
    echo -e "  ${YELLOW}→${NC} Running validation..."
    local temp_output=$(mktemp)
    if ! python3 -m cli compose validate "${template_id}" \
        > "${temp_output}" 2>&1; then
        echo -e "  ${RED}✗${NC} Validation failed"
        print_status "ERROR" "${template_id} - Validation failed"
        FAILED=$((FAILED + 1))
        FAILED_TEMPLATES+=("${template_id}")
        
        # Show error message (first few lines)
        if [[ -s "${temp_output}" ]]; then
            echo "  └─ Validation error:"
            head -n 5 "${temp_output}" | sed 's/^/     /'
        fi
        rm -f "${temp_output}"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} Validation passed"
    rm -f "${temp_output}"
    
    # Step 2: Run dry-run generation with quiet mode
    echo -e "  ${YELLOW}→${NC} Running dry-run generation..."
    local temp_gen=$(mktemp)
    if ! python3 -m cli compose generate "${template_id}" \
        --dry-run \
        --no-interactive \
        --quiet \
        > "${temp_gen}" 2>&1; then
        echo -e "  ${RED}✗${NC} Generation failed"
        print_status "ERROR" "${template_id} - Generation failed"
        FAILED=$((FAILED + 1))
        FAILED_TEMPLATES+=("${template_id}")
        
        # Show error message (first few lines)
        if [[ -s "${temp_gen}" ]]; then
            echo "  └─ Generation error:"
            head -n 5 "${temp_gen}" | sed 's/^/     /'
        fi
        rm -f "${temp_gen}"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} Generation passed"
    rm -f "${temp_gen}"
    
    # Both validation and generation passed
    print_status "SUCCESS" "${template_id}"
    PASSED=$((PASSED + 1))
    echo ""
    return 0
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"
    
    echo "=========================================="
    echo "Compose Template Validation Tests"
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
        # Continue even if validation fails (don't let set -e stop us)
        validate_template "${template_id}" "${template_name}" || true
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
