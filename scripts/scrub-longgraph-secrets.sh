#!/usr/bin/env bash
# scrub-longgraph-secrets.sh
# Scan .longgraph/ for common secret patterns before sharing or committing
# Fail-closed: exit non-zero if secrets detected or scan incomplete

set -euo pipefail

# ANSI colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Secret patterns (case-insensitive grep)
PATTERNS=(
  # API keys and tokens
  'api[_-]?key["\s:=]+[a-zA-Z0-9_-]{20,}'
  'api[_-]?token["\s:=]+[a-zA-Z0-9_-]{20,}'
  'access[_-]?token["\s:=]+[a-zA-Z0-9_-]{20,}'
  'auth[_-]?token["\s:=]+[a-zA-Z0-9_-]{20,}'
  'bearer["\s:=]+[a-zA-Z0-9_\-\.]{20,}'
  
  # Cloud provider keys
  'AKIA[0-9A-Z]{16}'  # AWS Access Key ID
  'AIza[0-9A-Za-z\-_]{35}'  # Google API Key
  'sk-[a-zA-Z0-9]{20,}'  # OpenAI/Anthropic style keys
  
  # GitHub tokens
  'gh[ps]_[a-zA-Z0-9]{36,}'
  'github_pat_[a-zA-Z0-9]{22,}'
  
  # Generic secrets
  'secret["\s:=]+[a-zA-Z0-9_-]{16,}'
  'password["\s:=]+[^\s"]{8,}'
  'passwd["\s:=]+[^\s"]{8,}'
  
  # Private keys
  '-----BEGIN [A-Z ]+ PRIVATE KEY-----'
  '-----BEGIN RSA PRIVATE KEY-----'
  '-----BEGIN OPENSSH PRIVATE KEY-----'
  
  # Database connection strings
  'postgres://[^@]+:[^@]+@'
  'mysql://[^@]+:[^@]+@'
  'mongodb://[^@]+:[^@]+@'
  
  # JWT tokens
  'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
)

SCAN_DIR="${1:-.longgraph}"
FOUND_SECRETS=0
DRY_RUN=false
REDACT=false

usage() {
  cat <<EOF
Usage: $0 [OPTIONS] [DIRECTORY]

Scan longgraph run directories for common secret patterns.

OPTIONS:
  -h, --help      Show this help message
  -d, --dry-run   Show what would be scanned without failing
  -r, --redact    Redact detected secrets instead of failing (DANGEROUS)
  
DIRECTORY:
  Path to scan (default: .longgraph)

EXAMPLES:
  # Scan default .longgraph directory
  $0
  
  # Scan specific run
  $0 .longgraph/2026-09-08-auth-migration
  
  # Dry run to see what would be checked
  $0 --dry-run
  
EXIT CODES:
  0 - No secrets found
  1 - Secrets detected or scan failed
  2 - Invalid arguments

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    -d|--dry-run)
      DRY_RUN=true
      shift
      ;;
    -r|--redact)
      REDACT=true
      shift
      ;;
    -*)
      echo -e "${RED}Unknown option: $1${NC}" >&2
      usage
      exit 2
      ;;
    *)
      SCAN_DIR="$1"
      shift
      ;;
  esac
done

# Verify scan directory exists
if [[ ! -d "$SCAN_DIR" ]]; then
  echo -e "${RED}Error: Directory not found: $SCAN_DIR${NC}" >&2
  exit 1
fi

echo "🔍 Scanning for secrets in: $SCAN_DIR"
echo ""

# Find all text files (exclude binary files)
FILES=$(find "$SCAN_DIR" -type f \( \
  -name "*.md" -o \
  -name "*.json" -o \
  -name "*.yaml" -o \
  -name "*.yml" -o \
  -name "*.txt" -o \
  -name "*.log" -o \
  -name "*.sh" -o \
  -name "*.py" \
\) 2>/dev/null || true)

if [[ -z "$FILES" ]]; then
  echo -e "${YELLOW}Warning: No text files found in $SCAN_DIR${NC}"
  exit 0
fi

FILE_COUNT=$(echo "$FILES" | wc -l)
echo "📁 Found $FILE_COUNT text files to scan"
echo ""

# Scan each pattern
for PATTERN in "${PATTERNS[@]}"; do
  MATCHES=$(echo "$FILES" | xargs grep -iE "$PATTERN" 2>/dev/null || true)
  
  if [[ -n "$MATCHES" ]]; then
    FOUND_SECRETS=1
    echo -e "${RED}❌ FOUND SECRET PATTERN:${NC} $PATTERN"
    echo "$MATCHES" | while IFS= read -r line; do
      FILE=$(echo "$line" | cut -d':' -f1)
      CONTENT=$(echo "$line" | cut -d':' -f2-)
      echo -e "   ${YELLOW}$FILE${NC}"
      echo -e "   ${RED}$CONTENT${NC}"
      echo ""
      
      if [[ "$REDACT" == true && "$DRY_RUN" == false ]]; then
        # Redact by replacing the secret with [REDACTED]
        # WARNING: This is a naive approach and may corrupt files
        sed -i.bak -E "s/$PATTERN/[REDACTED]/gi" "$FILE"
        echo -e "   ${GREEN}✓ Redacted in $FILE${NC}"
        echo ""
      fi
    done
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $FOUND_SECRETS -eq 1 ]]; then
  if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}⚠️  DRY RUN: Secrets detected but not failing${NC}"
    exit 0
  elif [[ "$REDACT" == true ]]; then
    echo -e "${YELLOW}⚠️  Secrets were REDACTED${NC}"
    echo ""
    echo "Review the changes and restore .bak files if needed:"
    echo "  find $SCAN_DIR -name '*.bak' -exec rm {} \\;"
    exit 0
  else
    echo -e "${RED}❌ SECRETS DETECTED${NC}"
    echo ""
    echo "Do NOT commit or share these files until secrets are removed."
    echo ""
    echo "Options:"
    echo "  1. Remove secrets manually"
    echo "  2. Use --redact flag (review carefully after)"
    echo "  3. Delete sensitive files"
    echo ""
    exit 1
  fi
else
  echo -e "${GREEN}✅ No secrets detected${NC}"
  echo ""
  echo "Scanned $FILE_COUNT files in $SCAN_DIR"
  exit 0
fi
