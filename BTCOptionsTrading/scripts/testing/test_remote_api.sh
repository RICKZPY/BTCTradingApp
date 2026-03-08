#!/bin/bash
# 测试远程API访问

SERVER="http://47.86.62.200:5002"

echo "=========================================="
echo "测试情绪交易API - 47.86.62.200:5002"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试1: 健康检查
echo "1. 健康检查..."
response=$(curl -s -w "\n%{http_code}" $SERVER/api/health 2>/dev/null)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ API服务正常运行${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ API服务异常 (HTTP $http_code)${NC}"
    echo "$body"
fi

echo ""
echo "2. 完整状态..."
curl -s $SERVER/api/status | python3 -m json.tool 2>/dev/null || echo "无法获取状态"

echo ""
echo "3. 持仓信息..."
curl -s $SERVER/api/positions | python3 -m json.tool 2>/dev/null || echo "无法获取持仓"

echo ""
echo "4. 交易历史（最近5条）..."
curl -s "$SERVER/api/history?limit=5" | python3 -m json.tool 2>/dev/null || echo "无法获取历史"

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "可用的API端点："
echo "  - $SERVER/api/health"
echo "  - $SERVER/api/status"
echo "  - $SERVER/api/positions"
echo "  - $SERVER/api/orders"
echo "  - $SERVER/api/history"
echo "  - $SERVER/api/live/positions"
echo "  - $SERVER/api/live/orders"
echo ""
