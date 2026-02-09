"""
Deribit连接器使用示例
演示如何使用Deribit API连接器获取期权数据
"""

import asyncio
from datetime import datetime, timedelta

from src.connectors.deribit_connector import DeribitConnector
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main():
    """主函数"""
    connector = DeribitConnector()
    
    try:
        logger.info("=== Deribit连接器测试 ===")
        
        # 1. 获取期权链数据
        logger.info("\n1. 获取BTC期权链数据...")
        contracts = await connector.get_options_chain("BTC")
        logger.info(f"获取到 {len(contracts)} 个期权合约")
        
        if contracts:
            # 显示前3个合约的信息
            for i, contract in enumerate(contracts[:3]):
                logger.info(
                    f"\n合约 {i+1}:",
                    instrument=contract.instrument_name,
                    type=contract.option_type.value,
                    strike=float(contract.strike_price),
                    expiry=contract.expiration_date.strftime("%Y-%m-%d"),
                    price=float(contract.current_price),
                    iv=f"{contract.implied_volatility*100:.2f}%",
                    delta=f"{contract.delta:.4f}"
                )
        
        # 2. 获取实时数据
        if contracts:
            logger.info("\n2. 获取实时市场数据...")
            instruments = [contracts[0].instrument_name]
            market_data = await connector.get_real_time_data(instruments)
            
            for symbol, data in market_data.items():
                logger.info(
                    f"\n{symbol} 实时数据:",
                    price=float(data.price),
                    bid=float(data.bid),
                    ask=float(data.ask),
                    spread=float(data.ask - data.bid),
                    volume=data.volume
                )
        
        # 3. 获取历史数据
        if contracts:
            logger.info("\n3. 获取历史数据...")
            instrument = contracts[0].instrument_name
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            historical = await connector.get_historical_data(
                instrument,
                start_date,
                end_date
            )
            
            logger.info(f"获取到 {len(historical)} 条历史数据")
            if historical:
                latest = historical[-1]
                logger.info(
                    f"\n最新数据 ({latest.timestamp.strftime('%Y-%m-%d')}):",
                    open=float(latest.open_price),
                    high=float(latest.high_price),
                    low=float(latest.low_price),
                    close=float(latest.close_price),
                    volume=latest.volume
                )
        
        # 4. 获取波动率曲面
        logger.info("\n4. 构建波动率曲面...")
        vol_surface = await connector.get_volatility_surface("BTC")
        logger.info(
            "波动率曲面:",
            num_strikes=len(vol_surface.strikes),
            num_expiries=len(vol_surface.expiries),
            shape=vol_surface.volatilities.shape
        )
        
        logger.info("\n=== 测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)
    
    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
