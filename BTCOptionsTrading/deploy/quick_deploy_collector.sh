#!/bin/bash
# 快速部署数据采集器到服务器

SERVER="root@47.86.62.200"
REMOTE_DIR="/root/BTCOptionsTrading"

echo "=========================================="
echo "部署数据采集器到服务器"
echo "服务器: $SERVER"
echo "=========================================="
echo ""

# 检查SSH连接
echo "测试SSH连接..."
ssh -o ConnectTimeout=5 $SERVER "echo '连接成功'" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 无法连接到服务器"
    echo "请确保："
    echo "1. 服务器IP正确"
    echo "2. SSH服务运行中"
    echo "3. 防火墙允许SSH连接"
    exit 1
fi

echo ""
echo "步骤1: 创建远程目录..."
ssh $SERVER "mkdir -p $REMOTE_DIR/backend/logs"

echo ""
echo "步骤2: 上传采集脚本..."
scp ../backend/daily_data_collector.py $SERVER:$REMOTE_DIR/backend/

echo ""
echo "步骤3: 上传配置脚本..."
scp ../backend/setup_daily_collection.sh $SERVER:$REMOTE_DIR/backend/

echo ""
echo "步骤4: 上传文档..."
scp ../backend/DAILY_COLLECTION_GUIDE.md $SERVER:$REMOTE_DIR/backend/

echo ""
echo "步骤5: 设置执行权限..."
ssh $SERVER "chmod +x $REMOTE_DIR/backend/daily_data_collector.py"
ssh $SERVER "chmod +x $REMOTE_DIR/backend/setup_daily_collection.sh"

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "接下来的步骤："
echo ""
echo "1. SSH登录到服务器："
echo "   ssh $SERVER"
echo ""
echo "2. 进入项目目录："
echo "   cd $REMOTE_DIR/backend"
echo ""
echo "3. 测试采集脚本："
echo "   python3 daily_data_collector.py --currency BTC"
echo ""
echo "4. 设置自动采集（可选）："
echo "   ./setup_daily_collection.sh"
echo ""
echo "5. 查看日志："
echo "   tail -f logs/daily_collection.log"
echo ""
