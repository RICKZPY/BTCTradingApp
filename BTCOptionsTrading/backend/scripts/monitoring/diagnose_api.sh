#!/bin/bash
# API服务诊断脚本 - 在服务器上运行

echo "=========================================="
echo "情绪交易API服务诊断"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查API进程是否运行
echo "1. 检查API服务进程..."
if ps aux | grep -v grep | grep "sentiment_api.py" > /dev/null; then
    echo -e "${GREEN}✓ API服务进程正在运行${NC}"
    ps aux | grep -v grep | grep "sentiment_api.py"
else
    echo -e "${RED}✗ API服务进程未运行${NC}"
    echo "  请运行: cd /root/BTCTradingApp/BTCOptionsTrading/backend && python3 sentiment_api.py"
fi
echo ""

# 2. 检查端口5002是否被监听
echo "2. 检查端口5002..."
if netstat -tlnp 2>/dev/null | grep ":5002" > /dev/null || ss -tlnp 2>/dev/null | grep ":5002" > /dev/null; then
    echo -e "${GREEN}✓ 端口5002正在监听${NC}"
    netstat -tlnp 2>/dev/null | grep ":5002" || ss -tlnp 2>/dev/null | grep ":5002"
else
    echo -e "${RED}✗ 端口5002未被监听${NC}"
    echo "  API服务可能未启动或启动失败"
fi
echo ""

# 3. 测试本地连接
echo "3. 测试本地连接..."
if curl -s http://localhost:5002/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 本地连接成功${NC}"
    curl -s http://localhost:5002/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5002/api/health
else
    echo -e "${RED}✗ 本地连接失败${NC}"
    echo "  API服务可能未正常启动"
fi
echo ""

# 4. 检查防火墙状态
echo "4. 检查防火墙..."
if command -v ufw > /dev/null; then
    echo "UFW防火墙状态:"
    ufw status | grep -E "Status|5002"
    if ufw status | grep "5002.*ALLOW" > /dev/null; then
        echo -e "${GREEN}✓ UFW已允许5002端口${NC}"
    else
        echo -e "${YELLOW}⚠ UFW未配置5002端口${NC}"
        echo "  运行: sudo ufw allow 5002/tcp"
    fi
elif command -v firewall-cmd > /dev/null; then
    echo "Firewalld状态:"
    if firewall-cmd --list-ports 2>/dev/null | grep "5002" > /dev/null; then
        echo -e "${GREEN}✓ Firewalld已允许5002端口${NC}"
    else
        echo -e "${YELLOW}⚠ Firewalld未配置5002端口${NC}"
        echo "  运行: sudo firewall-cmd --permanent --add-port=5002/tcp && sudo firewall-cmd --reload"
    fi
else
    echo -e "${YELLOW}⚠ 未检测到防火墙管理工具${NC}"
fi
echo ""

# 5. 检查日志文件
echo "5. 检查最近的日志..."
if [ -f "logs/sentiment_api.log" ]; then
    echo "最近10行日志:"
    tail -10 logs/sentiment_api.log
else
    echo -e "${YELLOW}⚠ 日志文件不存在: logs/sentiment_api.log${NC}"
fi
echo ""

# 6. 检查.env配置
echo "6. 检查配置文件..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env文件存在${NC}"
    
    # 检查测试网配置
    if grep -q "^DERIBIT_TESTNET_API_KEY=" .env; then
        testnet_key=$(grep "^DERIBIT_TESTNET_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$testnet_key" ] && [ "$testnet_key" != "your_testnet_api_key_here" ]; then
            echo -e "  ${GREEN}✓ 测试网API密钥已配置${NC}"
        else
            echo -e "  ${RED}✗ 测试网API密钥未配置${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ 未找到测试网配置${NC}"
    fi
    
    # 检查主网配置
    if grep -q "^DERIBIT_MAINNET_API_KEY=" .env; then
        mainnet_key=$(grep "^DERIBIT_MAINNET_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$mainnet_key" ] && [ "$mainnet_key" != "your_mainnet_api_key_here" ]; then
            echo -e "  ${GREEN}✓ 主网API密钥已配置${NC}"
        else
            echo -e "  ${YELLOW}⚠ 主网API密钥未配置（可选）${NC}"
        fi
    fi
    
    # 检查旧配置
    if grep -q "^DERIBIT_API_KEY=" .env; then
        old_key=$(grep "^DERIBIT_API_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$old_key" ] && [ "$old_key" != "your_api_key_here" ]; then
            echo -e "  ${GREEN}✓ 旧格式API密钥已配置${NC}"
        fi
    fi
    
    echo ""
    echo "  运行详细配置检查: ./check_env_config.sh"
else
    echo -e "${RED}✗ .env文件不存在${NC}"
    echo "  请从.env.example复制并配置"
fi
echo ""

# 7. 检查Python依赖
echo "7. 检查Python依赖..."
if python3 -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}✓ Flask已安装${NC}"
else
    echo -e "${RED}✗ Flask未安装${NC}"
    echo "  运行: pip3 install flask"
fi

if python3 -c "import aiohttp" 2>/dev/null; then
    echo -e "${GREEN}✓ aiohttp已安装${NC}"
else
    echo -e "${RED}✗ aiohttp未安装${NC}"
    echo "  运行: pip3 install aiohttp"
fi
echo ""

# 8. 测试外部访问
echo "8. 测试外部访问..."
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo "服务器公网IP: $PUBLIC_IP"
    echo "外部访问地址: http://$PUBLIC_IP:5002/api/health"
else
    echo -e "${YELLOW}⚠ 无法获取公网IP${NC}"
fi
echo ""

# 总结和建议
echo "=========================================="
echo "诊断总结"
echo "=========================================="
echo ""
echo "如果API无法从外部访问，请检查："
echo "1. API服务是否正在运行（检查1）"
echo "2. 端口5002是否被监听（检查2）"
echo "3. 服务器防火墙是否开放5002端口（检查4）"
echo "4. 云服务商安全组是否允许5002端口"
echo ""
echo "快速修复命令："
echo "  启动API服务: cd /root/BTCTradingApp/BTCOptionsTrading/backend && python3 sentiment_api.py &"
echo "  开放防火墙: sudo ufw allow 5002/tcp && sudo ufw reload"
echo "  查看日志: tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_api.log"
echo ""
