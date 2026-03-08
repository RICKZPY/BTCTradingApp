#!/bin/bash
# 测试所有API端点

SERVER="http://47.86.62.200:5002"

echo "=========================================="
echo "测试所有API端点"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

test_endpoint() {
    local name=$1
    local url=$2
    
    echo -e "${BLUE}测试: $name${NC}"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ 成功 (HTTP $http_code)${NC}"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo -e "${RED}✗ 失败 (HTTP $http_code)${NC}"
        echo "$body"
    fi
    echo ""
}

# 测试所有端点
test_endpoint "1. 健康检查" "$SERVER/api/health"
test_endpoint "2. 完整状态" "$SERVER/api/status"
test_endpoint "3. 持仓信息" "$SERVER/api/positions"
test_endpoint "4. 订单信息" "$SERVER/api/orders"
test_endpoint "5. 交易历史" "$SERVER/api/history?limit=3"
test_endpoint "6. 实时持仓" "$SERVER/api/live/positions"
test_endpoint "7. 实时订单" "$SERVER/api/live/orders"

echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "所有端点："
echo "  健康检查: $SERVER/api/health"
echo "  完整状态: $SERVER/api/status"
echo "  持仓信息: $SERVER/api/positions"
echo "  订单信息: $SERVER/api/orders"
echo "  交易历史: $SERVER/api/history"
echo "  实时持仓: $SERVER/api/live/positions"
echo "  实时订单: $SERVER/api/live/orders"
echo ""
