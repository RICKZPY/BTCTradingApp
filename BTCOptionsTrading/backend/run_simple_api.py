#!/usr/bin/env python3
"""
简化的后端API服务器
用于提供历史数据分析功能，不需要复杂的依赖
"""

import json
import csv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 数据目录
DATA_DIR = Path(__file__).parent / 'data' / 'downloads'

# 策略模板数据
STRATEGY_TEMPLATES = {
    "templates": [
        {
            "type": "single_leg",
            "name": "单腿策略",
            "description": "买入或卖出单个期权合约",
            "market_condition": "方向性市场",
            "key_features": [
                "最简单的期权策略",
                "风险和收益都较高",
                "适合有明确方向判断时使用"
            ],
            "detailed_description": "单腿策略是最基础的期权交易策略，通过买入或卖出单个看涨或看跌期权来表达对市场方向的看法。",
            "risk_profile": {
                "max_profit": "无限（买入看涨）或权利金（买入看跌）",
                "max_loss": "权利金（买入）或无限（卖出）",
                "breakeven": "执行价 ± 权利金"
            }
        },
        {
            "type": "straddle",
            "name": "跨式策略",
            "description": "同时买入相同执行价的看涨和看跌期权",
            "market_condition": "高波动率预期",
            "key_features": [
                "适合预期大幅波动但方向不明时",
                "需要较大的价格变动才能盈利",
                "时间价值衰减较快"
            ],
            "detailed_description": "跨式策略通过同时买入相同执行价和到期日的看涨和看跌期权，在市场大幅波动时获利，无论涨跌。",
            "risk_profile": {
                "max_profit": "无限",
                "max_loss": "两个期权的权利金之和",
                "breakeven": "执行价 ± 总权利金"
            }
        },
        {
            "type": "strangle",
            "name": "宽跨式策略",
            "description": "买入不同执行价的看涨和看跌期权",
            "market_condition": "预期大幅波动",
            "key_features": [
                "成本低于跨式策略",
                "需要更大的价格变动",
                "风险有限，潜在收益无限"
            ],
            "detailed_description": "宽跨式策略类似跨式，但使用不同执行价的期权，降低成本但需要更大的价格变动才能盈利。",
            "risk_profile": {
                "max_profit": "无限",
                "max_loss": "两个期权的权利金之和",
                "breakeven": "看涨执行价 + 总权利金 或 看跌执行价 - 总权利金"
            }
        },
        {
            "type": "iron_condor",
            "name": "铁鹰策略",
            "description": "组合看涨和看跌价差，在区间内获利",
            "market_condition": "低波动率预期",
            "key_features": [
                "适合横盘整理市场",
                "风险和收益都有限",
                "需要价格保持在特定区间"
            ],
            "detailed_description": "铁鹰策略通过卖出中间执行价的期权并买入外侧保护，在价格保持在区间内时获得权利金收入。",
            "risk_profile": {
                "max_profit": "净权利金收入",
                "max_loss": "价差宽度 - 净权利金",
                "breakeven": "两个盈亏平衡点"
            }
        },
        {
            "type": "butterfly",
            "name": "蝶式策略",
            "description": "三个执行价的组合，中性策略",
            "market_condition": "预期价格稳定",
            "key_features": [
                "风险有限，收益有限",
                "最大收益在中间执行价",
                "成本较低"
            ],
            "detailed_description": "蝶式策略通过买入两个外侧执行价的期权，卖出两个中间执行价的期权，在价格接近中间执行价时获得最大收益。",
            "risk_profile": {
                "max_profit": "中间执行价 - 低执行价 - 净成本",
                "max_loss": "净成本",
                "breakeven": "两个盈亏平衡点"
            }
        }
    ]
}

def load_csv_data():
    """加载所有CSV文件中的数据"""
    all_data = []
    csv_files = list(DATA_DIR.glob('*.csv'))
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    return all_data

def get_overview_stats(data):
    """获取数据概览统计"""
    if not data:
        return {
            'csv_files': 0,
            'database_records': 0,
            'memory_cache_size_mb': 0,
            'unique_instruments': 0
        }
    
    csv_files = list(DATA_DIR.glob('*.csv'))
    instruments = set(row['instrument_name'] for row in data if 'instrument_name' in row)
    
    return {
        'csv_files': len(csv_files),
        'database_records': len(data),
        'memory_cache_size_mb': len(json.dumps(data).encode()) / (1024 * 1024),
        'unique_instruments': len(instruments)
    }

def get_contracts_list(data):
    """获取合约列表"""
    instruments = set()
    for row in data:
        if 'instrument_name' in row:
            instruments.add(row['instrument_name'])
    return sorted(list(instruments))

def get_contract_details(data, contract_name):
    """获取特定合约的详细信息"""
    contract_data = [row for row in data if row.get('instrument_name') == contract_name]
    
    if not contract_data:
        return None
    
    # 计算统计信息
    prices = []
    volumes = []
    for row in contract_data:
        try:
            if row.get('mark_price'):
                prices.append(float(row['mark_price']))
            if row.get('volume'):
                volumes.append(float(row['volume']))
        except (ValueError, TypeError):
            continue
    
    first_row = contract_data[0]
    
    return {
        'instrument_name': contract_name,
        'underlying': first_row.get('underlying_symbol', 'BTC'),
        'strike_price': float(first_row.get('strike_price', 0)),
        'expiry_date': first_row.get('expiry_date', ''),
        'option_type': first_row.get('option_type', ''),
        'data_points': len(contract_data),
        'avg_price': sum(prices) / len(prices) if prices else 0,
        'total_volume': sum(volumes),
        'price_history': [
            {
                'timestamp': row.get('timestamp', ''),
                'mark_price': float(row.get('mark_price', 0)),
                'bid_price': float(row.get('bid_price', 0)),
                'ask_price': float(row.get('ask_price', 0)),
                'volume': float(row.get('volume', 0)),
                'open_interest': float(row.get('open_interest', 0)),
                'implied_volatility': float(row.get('implied_volatility', 0))
            }
            for row in contract_data[:100]  # 限制返回数量
        ]
    }

class SimpleAPIHandler(BaseHTTPRequestHandler):
    # 缓存数据
    _cached_data = None
    _cache_time = None
    
    @classmethod
    def get_data(cls):
        """获取数据（带缓存）"""
        now = datetime.now()
        if cls._cached_data is None or (cls._cache_time and (now - cls._cache_time).seconds > 60):
            print("Loading CSV data...")
            cls._cached_data = load_csv_data()
            cls._cache_time = now
            print(f"Loaded {len(cls._cached_data)} records")
        return cls._cached_data
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            if path == '/api/strategies/templates' or path == '/api/strategies/templates/list':
                # 策略模板
                response = STRATEGY_TEMPLATES
                
            elif path == '/api/settings/deribit':
                # Deribit配置
                response = {
                    'has_credentials': False,
                    'test_mode': True,
                    'api_key': '',
                    'api_secret': ''
                }
                
            elif path == '/api/settings/trading':
                # 交易配置
                response = {
                    'risk_free_rate': 0.05,
                    'default_initial_capital': 100000,
                    'commission_rate': 0.0005
                }
                
            elif path == '/api/settings/system-info':
                # 系统信息
                response = {
                    'version': '1.0.0',
                    'environment': 'development',
                    'database_type': 'sqlite',
                    'database_status': 'connected',
                    'api_status': 'running',
                    'cache_status': 'active'
                }
                
            elif path == '/api/historical/overview':
                # 数据概览
                data = self.get_data()
                stats = get_overview_stats(data)
                response = stats
                
            elif path == '/api/historical/contracts':
                # 合约列表
                data = self.get_data()
                contracts = get_contracts_list(data)
                response = contracts
                
            elif path.startswith('/api/historical/contract/'):
                # 特定合约详情
                data = self.get_data()
                contract_name = path.split('/')[-1]
                contract_details = get_contract_details(data, contract_name)
                if contract_details:
                    response = contract_details
                else:
                    response = {'error': 'Contract not found'}
            
            else:
                response = {'error': 'Not found', 'path': path}
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            if path == '/api/settings/deribit':
                # 保存Deribit配置（简化版，只返回成功）
                request_data = json.loads(post_data.decode('utf-8'))
                response = {
                    'message': 'Deribit配置已保存（演示模式）',
                    'success': True
                }
            elif path == '/api/settings/trading':
                # 保存交易配置（简化版，只返回成功）
                request_data = json.loads(post_data.decode('utf-8'))
                response = {
                    'message': '交易配置已保存（演示模式）',
                    'success': True
                }
            else:
                response = {'error': 'Not found', 'path': path}
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"{self.address_string()} - {format % args}")

def run_server(port=8000):
    """运行服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleAPIHandler)
    print(f"Starting simple API server on port {port}...")
    print(f"Data directory: {DATA_DIR}")
    print(f"Available endpoints:")
    print(f"  - http://localhost:{port}/api/historical/overview")
    print(f"  - http://localhost:{port}/api/historical/contracts")
    print(f"  - http://localhost:{port}/api/historical/contract/<name>")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
