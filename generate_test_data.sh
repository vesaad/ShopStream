#!/bin/bash

echo "Ì∫Ä Generating test data for Grafana Dashboard..."

API_GATEWAY="http://localhost:8000"

# Register 15 users
echo "Ì±• Registering users..."
for i in {1..15}; do
  curl -s -X POST $API_GATEWAY/api/users/register \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"user$i\",
      \"email\": \"user$i@shopstream.com\",
      \"password\": \"test123\"
    }" > /dev/null
  echo "  ‚úì User $i registered"
  sleep 0.2
done

# Login some users
echo "Ì¥ê Logging in users..."
for i in {1..5}; do
  curl -s -X POST $API_GATEWAY/api/users/login \
    -H "Content-Type: application/json" \
    -d "{
      \"username\": \"user$i\",
      \"password\": \"test123\"
    }" > /dev/null
  echo "  ‚úì User $i logged in"
  sleep 0.2
done

# Create 10 products
echo "Ì≥¶ Creating products..."
PRODUCTS=(
  "MacBook Pro:2499.99:Electronics"
  "iPhone 15:999.99:Electronics"
  "iPad Air:599.99:Electronics"
  "AirPods Pro:249.99:Electronics"
  "Samsung TV:1299.99:Electronics"
  "Nike Shoes:129.99:Clothing"
  "Adidas Jacket:89.99:Clothing"
  "Python Book:49.99:Books"
  "Coffee Maker:79.99:Home"
  "Yoga Mat:29.99:Sports"
)

for product in "${PRODUCTS[@]}"; do
  IFS=':' read -r name price category <<< "$product"
  
  curl -s -X POST $API_GATEWAY/api/products/products \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$name\",
      \"price\": $price,
      \"stock\": $((RANDOM % 50 + 10)),
      \"category\": \"$category\",
      \"description\": \"High quality $name\"
    }" > /dev/null
  echo "  ‚úì Created: $name (\$$price)"
  sleep 0.3
done

echo "‚úÖ Test data generation complete!"
echo ""
echo "Ì≥ä Grafana Dashboard: http://localhost:3000"
echo "Ì¥ê Login: admin / admin123"
echo "Ì≥à Analytics API: http://localhost:8004/analytics/summary"
