#!/bin/bash

  # verify-go-files.sh - Comprehensive Go files verification script

  DIR1="/Users/nonicked/Documents/Personal/pdb-management"
  DIR2="/Users/nonicked/Documents/Personal/oda-canvas/source/operators/pdb-management"

  # Colors for output
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  NC='\033[0m' # No Color

  echo "=== Comprehensive Go Files Security Check for PDB Management Operators ==="
  echo "Directory 1: $DIR1"
  echo "Directory 2: $DIR2"
  echo "=========================================================================="
  echo

  # Function to check directory
  check_directory() {
      local dir=$1
      local dir_name=$2

      echo -e "${YELLOW}=== Checking $dir_name: $dir ===${NC}"
      echo

      # 1. Count Go files
      echo "1. Go Files Analysis:"
      go_files=$(find "$dir" -name "*.go" -type f 2>/dev/null | wc -l)
      echo "   Total Go files: $go_files"

      # List all Go files
      echo "   Go files structure:"
      find "$dir" -name "*.go" -type f 2>/dev/null | sed 's|'"$dir"'/||' | sort | head -20
      echo

      # 2. Check for suspicious imports
      echo "2. Checking suspicious imports in Go files:"
      suspicious_imports=$(grep -h "^import\|^\s*\"" "$dir"/**/*.go 2>/dev/null | \
          grep -v "k8s.io\|sigs.k8s.io\|github.com/go-logr\|github.com/prometheus\|github.com/onsi\|golang.org/x" | \
          grep -E "net/http|os/exec|syscall|unsafe" | sort -u)

      if [ -z "$suspicious_imports" ]; then
          echo -e "   ${GREEN}✓ No suspicious imports found${NC}"
      else
          echo -e "   ${RED}⚠ Found potentially suspicious imports:${NC}"
          echo "$suspicious_imports" | head -10
      fi
      echo

      # 3. Check for hardcoded credentials
      echo "3. Checking for hardcoded credentials:"
      creds=$(grep -rn --include="*.go" -E "(password|passwd|secret|token|apikey|api_key|access_key|private_key)\s*[:=]\s*\"[^\"]+\"" "$dir" 2>/dev/null | \
          grep -v "SecretKeyRef\|secretRef\|PasswordSecret\|TokenSecret\|//" | head -5)

      if [ -z "$creds" ]; then
          echo -e "   ${GREEN}✓ No hardcoded credentials found${NC}"
      else
          echo -e "   ${RED}⚠ Potential hardcoded credentials:${NC}"
          echo "$creds"
      fi
      echo

      # 4. Check for network operations
      echo "4. Checking network operations:"
      echo "   External URLs found:"
      grep -rh --include="*.go" "https://\|http://" "$dir" 2>/dev/null | \
          grep -v "//\|kubernetes.io\|k8s.io\|sigs.k8s.io\|github.com/operator-framework" | \
          sort -u | head -10
      echo

      # 5. Check for file system operations
      echo "5. Checking dangerous file operations:"
      dangerous_ops=$(grep -rn --include="*.go" -E "os\.Remove|os\.RemoveAll|os\.Chmod|ioutil\.WriteFile|os\.WriteFile" "$dir" 2>/dev/null | wc -l)
      echo "   File deletion operations found: $dangerous_ops"

      if [ "$dangerous_ops" -gt 0 ]; then
          echo -e "   ${YELLOW}Sample dangerous operations:${NC}"
          grep -rn --include="*.go" -E "os\.Remove|os\.RemoveAll" "$dir" 2>/dev/null | head -3
      fi
      echo

      # 6. Check for command execution
      echo "6. Checking command execution:"
      exec_cmds=$(grep -rn --include="*.go" -E "exec\.Command|exec\.Run|syscall\.Exec" "$dir" 2>/dev/null | wc -l)
      echo "   Command execution calls found: $exec_cmds"

      if [ "$exec_cmds" -gt 0 ]; then
          echo -e "   ${YELLOW}Command execution instances:${NC}"
          grep -rn --include="*.go" "exec\.Command" "$dir" 2>/dev/null | head -3
      fi
      echo

      # 7. Check for environment variable usage
      echo "7. Checking environment variables:"
      env_vars=$(grep -rh --include="*.go" "os\.Getenv\|os\.LookupEnv" "$dir" 2>/dev/null | \
          sed 's/.*Getenv("\([^"]*\)").*/\1/' | \
          sed 's/.*LookupEnv("\([^"]*\)").*/\1/' | \
          sort -u)
      echo "   Environment variables accessed:"
      echo "$env_vars" | head -10
      echo

      # 8. Check for unsafe operations
      echo "8. Checking unsafe operations:"
      unsafe_ops=$(grep -rn --include="*.go" "unsafe\." "$dir" 2>/dev/null | wc -l)
      echo "   Unsafe operations found: $unsafe_ops"

      if [ "$unsafe_ops" -gt 0 ]; then
          echo -e "   ${RED}⚠ Unsafe package usage detected${NC}"
          grep -rn --include="*.go" "unsafe\." "$dir" 2>/dev/null | head -3
      fi
      echo

      # 9. Check main.go specifically
      echo "9. Checking main.go file:"
      if [ -f "$dir/cmd/main.go" ]; then
          echo "   Lines of code: $(wc -l < "$dir/cmd/main.go")"
          echo "   Main function check:"
          grep -n "func main()" "$dir/cmd/main.go"
      else
          echo -e "   ${RED}⚠ main.go not found${NC}"
      fi
      echo

      # 10. Generate Go files checksum
      echo "10. Generating checksums for all Go files:"
      find "$dir" -name "*.go" -type f -exec shasum -a 256 {} \; 2>/dev/null | \
          sed 's|'"$dir"'/||' | sort > "/tmp/${dir_name}_go_checksums.txt"
      echo "   Checksums saved to /tmp/${dir_name}_go_checksums.txt"
      echo "   Total Go files checksummed: $(wc -l < "/tmp/${dir_name}_go_checksums.txt")"
      echo
  }

  # Check both directories
  check_directory "$DIR1" "DIR1"
  echo -e "${YELLOW}=========================================================================${NC}"
  echo
  check_directory "$DIR2" "DIR2"

  # Compare the directories
  echo -e "${YELLOW}=== COMPARISON RESULTS ===${NC}"
  echo

  # Compare Go file counts
  count1=$(find "$DIR1" -name "*.go" -type f 2>/dev/null | wc -l)
  count2=$(find "$DIR2" -name "*.go" -type f 2>/dev/null | wc -l)

  if [ "$count1" -eq "$count2" ]; then
      echo -e "${GREEN}✓ Same number of Go files in both directories: $count1${NC}"
  else
      echo -e "${RED}✗ Different number of Go files: DIR1=$count1, DIR2=$count2${NC}"
  fi
  echo

  # Compare checksums
  echo "Comparing Go file checksums..."
  if [ -f "/tmp/DIR1_go_checksums.txt" ] && [ -f "/tmp/DIR2_go_checksums.txt" ]; then
      diff_output=$(diff "/tmp/DIR1_go_checksums.txt" "/tmp/DIR2_go_checksums.txt")
      if [ -z "$diff_output" ]; then
          echo -e "${GREEN}✓ All Go files are identical${NC}"
      else
          echo -e "${RED}✗ Differences found in Go files:${NC}"
          echo "$diff_output" | head -20
          echo
          echo "Files only in DIR1:"
          diff "/tmp/DIR1_go_checksums.txt" "/tmp/DIR2_go_checksums.txt" | grep "^<" | head -10
          echo
          echo "Files only in DIR2:"
          diff "/tmp/DIR1_go_checksums.txt" "/tmp/DIR2_go_checksums.txt" | grep "^>" | head -10
      fi
  fi
  echo

  # List specific differences in key files
  echo "Checking key Go files for differences:"
  for file in "cmd/main.go" "internal/controller/deployment_controller.go" "internal/controller/availabilitypolicy_controller.go"; do
      if [ -f "$DIR1/$file" ] && [ -f "$DIR2/$file" ]; then
          if diff "$DIR1/$file" "$DIR2/$file" > /dev/null 2>&1; then
              echo -e "${GREEN}✓ $file - identical${NC}"
          else
              echo -e "${RED}✗ $file - differs${NC}"
              echo "  Differences preview:"
              diff "$DIR1/$file" "$DIR2/$file" 2>/dev/null | head -5
          fi
      else
          echo -e "${YELLOW}⚠ $file - missing in one directory${NC}"
      fi
  done
  echo

  # Security summary
  echo -e "${YELLOW}=== SECURITY SUMMARY ===${NC}"
  echo "1. Check for suspicious patterns in all Go files"
  echo "2. Review any hardcoded credentials or secrets"
  echo "3. Examine network operations and external connections"
  echo "4. Verify file system operations are expected"
  echo "5. Review command execution if present"
  echo

  # Final safety check
  echo -e "${YELLOW}=== FINAL SAFETY VERIFICATION ===${NC}"

  # Check if operators appear to be legitimate PDB managers
  pdb_mentions1=$(grep -r "PodDisruptionBudget\|PDB" "$DIR1" --include="*.go" 2>/dev/null | wc -l)
  pdb_mentions2=$(grep -r "PodDisruptionBudget\|PDB" "$DIR2" --include="*.go" 2>/dev/null | wc -l)

  echo "PDB-related code mentions:"
  echo "  DIR1: $pdb_mentions1"
  echo "  DIR2: $pdb_mentions2"

  if [ "$pdb_mentions1" -gt 10 ] && [ "$pdb_mentions2" -gt 10 ]; then
      echo -e "${GREEN}✓ Both appear to be legitimate PDB management operators${NC}"
  else
      echo -e "${RED}⚠ Warning: Low PDB-related code mentions${NC}"
  fi

  echo
  echo "Verification complete. Review the output above for any security concerns."
  echo "Checksum files saved in /tmp/ for manual review if needed."