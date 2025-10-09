#!/usr/bin/env bash
#
# Test script for template rendering error handling
# This script creates various templates with errors and validates them
# to test the improved error handling and display

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="/tmp/boilerplates-error-tests"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Template Error Handling Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clean up test directory
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

# Function to create a test template
create_test_template() {
  local name=$1
  local description=$2
  local template_content=$3
  local spec_content=$4
  
  local template_dir="$TEST_DIR/$name"
  mkdir -p "$template_dir"
  
  # Create template.yaml
  cat > "$template_dir/template.yaml" <<EOF
---
kind: compose
metadata:
  name: $name Test
  description: $description
  version: 0.1.0
  author: Test Suite
  date: '2025-01-09'
$spec_content
EOF
  
  # Create compose.yaml.j2
  echo "$template_content" > "$template_dir/compose.yaml.j2"
  
  echo "$template_dir"
}

# Function to run a test
run_test() {
  local test_name=$1
  local template_path=$2
  local expected_to_fail=$3
  
  echo -e "${YELLOW}Test: $test_name${NC}"
  echo -e "${BLUE}Template path: $template_path${NC}"
  echo ""
  
  # Run validation with debug mode
  if python3 -m cli --log-level DEBUG compose validate --path "$template_path" 2>&1; then
    if [ "$expected_to_fail" = "true" ]; then
      echo -e "${RED}✗ UNEXPECTED: Test passed but was expected to fail${NC}"
      return 1
    else
      echo -e "${GREEN}✓ Test passed as expected${NC}"
      return 0
    fi
  else
    if [ "$expected_to_fail" = "true" ]; then
      echo -e "${GREEN}✓ Test failed as expected${NC}"
      return 0
    else
      echo -e "${RED}✗ UNEXPECTED: Test failed but was expected to pass${NC}"
      return 1
    fi
  fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 1: Undefined Variable Error${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_1=$(create_test_template \
  "undefined-variable" \
  "Template with undefined variable" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:{{ nginx_version }}
    container_name: {{ undefined_variable }}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      nginx_version:
        type: str
        description: Nginx version
        default: latest
')

run_test "Undefined Variable" "$TEMPLATE_1" "true"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 2: Jinja2 Syntax Error - Missing endif${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_2=$(create_test_template \
  "syntax-error-endif" \
  "Template with missing endif" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:latest
    {% if enable_ports %}
    ports:
      - "80:80"
    # Missing {% endif %}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      enable_ports:
        type: bool
        description: Enable ports
        default: true
')

run_test "Syntax Error - Missing endif" "$TEMPLATE_2" "true"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 3: Jinja2 Syntax Error - Unclosed bracket${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_3=$(create_test_template \
  "syntax-error-bracket" \
  "Template with unclosed bracket" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:{{ version
    container_name: {{ service_name }}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      version:
        type: str
        description: Version
        default: latest
')

run_test "Syntax Error - Unclosed Bracket" "$TEMPLATE_3" "true"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 4: Filter Error - Unknown filter${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_4=$(create_test_template \
  "filter-error" \
  "Template with unknown filter" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:{{ version | unknown_filter }}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      version:
        type: str
        description: Version
        default: latest
')

run_test "Filter Error - Unknown Filter" "$TEMPLATE_4" "true"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 5: Valid Template - Should Pass${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_5=$(create_test_template \
  "valid-template" \
  "Valid template that should pass validation" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:{{ version }}
    container_name: {{ service_name }}
    {% if enable_ports %}
    ports:
      - "{{ port }}:80"
    {% endif %}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      version:
        type: str
        description: Version
        default: latest
      enable_ports:
        type: bool
        description: Enable ports
        default: true
      port:
        type: int
        description: External port
        default: 8080
')

run_test "Valid Template" "$TEMPLATE_5" "false"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 6: Nested Variable with Typo${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_6=$(create_test_template \
  "typo-variable" \
  "Template with typo in variable name" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:latest
    environment:
      - SERVICE_NAME={{ servce_name }}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
')

run_test "Typo in Variable Name" "$TEMPLATE_6" "true"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test 7: Template with Default Filter${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEMPLATE_7=$(create_test_template \
  "default-filter" \
  "Template using default filter - should pass" \
  'version: "3.8"
services:
  {{ service_name }}:
    image: nginx:{{ version | default("latest") }}
    container_name: {{ container_name | default(service_name) }}
' \
  'spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
        default: myservice
      version:
        type: str
        description: Version
        default: ""
')

run_test "Default Filter Usage" "$TEMPLATE_7" "false"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${YELLOW}Check the output above for detailed error messages.${NC}"
echo ""
echo -e "${BLUE}Test directory: $TEST_DIR${NC}"
echo -e "${YELLOW}Note: Test directory has been preserved for manual inspection${NC}"
