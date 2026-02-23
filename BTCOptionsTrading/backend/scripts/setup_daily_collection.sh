#!/bin/bash
# 设置每日数据采集的cron job

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Daily Options Data Collection Setup"
echo "=========================================="
echo ""

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
COLLECTOR_SCRIPT="$SCRIPT_DIR/daily_data_collector.py"
PYTHON_PATH=$(which python3)

# 检查Python
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${RED}Error: Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python found: $PYTHON_PATH"

# 检查采集脚本
if [ ! -f "$COLLECTOR_SCRIPT" ]; then
    echo -e "${RED}Error: Collector script not found at $COLLECTOR_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Collector script found: $COLLECTOR_SCRIPT"
echo ""

# 显示当前cron jobs
echo "Current cron jobs:"
echo "----------------------------------------"
crontab -l 2>/dev/null || echo "No cron jobs found"
echo "----------------------------------------"
echo ""

# 询问用户
echo "This will set up a daily cron job to collect options data."
echo ""
echo "Proposed schedule:"
echo "  - Time: 00:00 (midnight) every day"
echo "  - Currency: BTC"
echo "  - Output: CSV + Database"
echo ""
echo "Cron expression: 0 0 * * * $PYTHON_PATH $COLLECTOR_SCRIPT --currency BTC"
echo ""
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# 创建临时cron文件
TEMP_CRON=$(mktemp)

# 保存现有的cron jobs
crontab -l 2>/dev/null > "$TEMP_CRON" || true

# 检查是否已存在相同的job
if grep -q "daily_data_collector.py" "$TEMP_CRON"; then
    echo -e "${YELLOW}Warning: A similar cron job already exists${NC}"
    echo "Existing job will be replaced."
    # 删除旧的job
    grep -v "daily_data_collector.py" "$TEMP_CRON" > "${TEMP_CRON}.new"
    mv "${TEMP_CRON}.new" "$TEMP_CRON"
fi

# 添加新的cron job
echo "" >> "$TEMP_CRON"
echo "# Daily BTC Options Data Collection" >> "$TEMP_CRON"
echo "# Runs at midnight every day" >> "$TEMP_CRON"
echo "0 0 * * * cd $SCRIPT_DIR && $PYTHON_PATH $COLLECTOR_SCRIPT --currency BTC >> $SCRIPT_DIR/logs/daily_collection.log 2>&1" >> "$TEMP_CRON"

# 安装新的crontab
crontab "$TEMP_CRON"

# 清理
rm "$TEMP_CRON"

echo ""
echo -e "${GREEN}✓${NC} Cron job installed successfully!"
echo ""
echo "New cron jobs:"
echo "----------------------------------------"
crontab -l
echo "----------------------------------------"
echo ""
echo "Log file: $SCRIPT_DIR/logs/daily_collection.log"
echo ""
echo "To test the collector manually, run:"
echo "  python3 $COLLECTOR_SCRIPT --currency BTC"
echo ""
echo "To remove the cron job, run:"
echo "  crontab -e"
echo "  (then delete the line containing 'daily_data_collector.py')"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
