#!/usr/bin/env bash
# Quick-start demo: creates a tenant, submits orders, watches them process.
# Run with the Docker Compose stack up: bash demo.sh
set -euo pipefail

BASE_URL="${ORDERFLOW_API_URL:-http://localhost:8000}"

echo "=== OrderFlow Demo ==="
echo ""

# Create tenant
echo "1. Creating tenant..."
TENANT=$(curl -sf -X POST "$BASE_URL/tenants/" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Demo Corp",
    "contact_name": "Demo User",
    "email": "demo@example.com",
    "phone": "+1-555-0100",
    "config": {"maximum_price": 200.0}
  }')

TENANT_ID=$(echo "$TENANT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
API_KEY=$(echo "$TENANT" | python3 -c "import sys,json; print(json.load(sys.stdin)['api_key'])")

echo "   Tenant ID : $TENANT_ID"
echo "   API key   : $API_KEY"
echo ""

# Submit orders
echo "2. Submitting 3 orders..."
for PRICE in 49.99 99.50 149.00; do
  ORDER=$(curl -sf -X POST "$BASE_URL/tenants/$TENANT_ID/orders/" \
    -H "api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"price\": $PRICE}")
  ORDER_ID=$(echo "$ORDER" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "   Order $ORDER_ID submitted (price: \$$PRICE)"
done
echo ""

# Show rejected order
echo "3. Submitting order above price limit (expect 400)..."
curl -s -X POST "$BASE_URL/tenants/$TENANT_ID/orders/" \
  -H "api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"price": 999.99}' | python3 -m json.tool
echo ""

# Watch orders process
echo "4. Watching orders process (Ctrl+C to stop)..."
echo "   Orders move: pending -> processing -> shipped"
echo ""
orderflow orders watch --tenant "$TENANT_ID" --api-key "$API_KEY"
