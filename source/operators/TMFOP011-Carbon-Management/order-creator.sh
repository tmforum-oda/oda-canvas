#!/bin/bash

URL="https://136.113.31.182/ocv1-productordercaptureandvalidation/tmf-api/productOrderingManagement/v4/productOrder"

# Optional headers (update if needed)
HEADERS=(
  "-H" "Content-Type: application/json"
  # "-H" "Authorization: Bearer <YOUR_TOKEN>"
)

echo "Starting order creation..."

for i in $(seq 21 40)
do
  # Vary speed for testing
  SPEED=$((50 + i * 10))"Mbps"

  PAYLOAD=$(cat <<EOF
{
  "productOrderItem": [
    {
      "id": "$i",
      "action": "add",
      "quantity": 1,
      "product": {
        "name": "Fiber Broadband",
        "productCharacteristic": [
          {
            "name": "speed",
            "value": "$SPEED"
          }
        ]
      }
    }
  ]
}
EOF
)

  echo "Creating order #$i with speed $SPEED..."

  curl -sk -X POST "$URL" \
    "${HEADERS[@]}" \
    -d "$PAYLOAD"

  echo -e "\n-----------------------------\n"

done

echo "All 20 orders submitted."