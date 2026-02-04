"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create news_items table
    op.create_table('news_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('impact_assessment', sa.JSON(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_data table
    op.create_table('market_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create technical_indicators table
    op.create_table('technical_indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('rsi', sa.Float(), nullable=True),
        sa.Column('macd', sa.Float(), nullable=True),
        sa.Column('macd_signal', sa.Float(), nullable=True),
        sa.Column('macd_histogram', sa.Float(), nullable=True),
        sa.Column('sma_20', sa.Float(), nullable=True),
        sa.Column('sma_50', sa.Float(), nullable=True),
        sa.Column('ema_12', sa.Float(), nullable=True),
        sa.Column('ema_26', sa.Float(), nullable=True),
        sa.Column('bollinger_upper', sa.Float(), nullable=True),
        sa.Column('bollinger_middle', sa.Float(), nullable=True),
        sa.Column('bollinger_lower', sa.Float(), nullable=True),
        sa.Column('signal_strength', sa.Float(), nullable=True),
        sa.Column('signal_type', sa.String(length=10), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create sentiment_analysis table
    op.create_table('sentiment_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('news_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('key_factors', sa.JSON(), nullable=True),
        sa.Column('short_term_impact', sa.Float(), nullable=True),
        sa.Column('long_term_impact', sa.Float(), nullable=True),
        sa.Column('impact_confidence', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['news_item_id'], ['news_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trading_records table
    op.create_table('trading_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('decision_reasoning', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('technical_signals', sa.JSON(), nullable=True),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('executed_amount', sa.Float(), nullable=True),
        sa.Column('executed_price', sa.Float(), nullable=True),
        sa.Column('fees', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trading_decisions table
    op.create_table('trading_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('suggested_amount', sa.Float(), nullable=False),
        sa.Column('min_price', sa.Float(), nullable=False),
        sa.Column('max_price', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('technical_signals', sa.JSON(), nullable=True),
        sa.Column('executed', sa.Boolean(), nullable=True),
        sa.Column('trading_record_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trading_record_id'], ['trading_records.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create risk_assessments table
    op.create_table('risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trading_decision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('max_loss_potential', sa.Float(), nullable=False),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('recommended_position_size', sa.Float(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trading_decision_id'], ['trading_decisions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create positions table
    op.create_table('positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create portfolio table
    op.create_table('portfolio',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('btc_balance', sa.Float(), nullable=True),
        sa.Column('usdt_balance', sa.Float(), nullable=True),
        sa.Column('total_value_usdt', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('realized_pnl', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create account_balances table
    op.create_table('account_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('btc_balance', sa.Float(), nullable=False),
        sa.Column('usdt_balance', sa.Float(), nullable=False),
        sa.Column('btc_locked', sa.Float(), nullable=True),
        sa.Column('usdt_locked', sa.Float(), nullable=True),
        sa.Column('total_value_usdt', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create system_config table
    op.create_table('system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('key'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create alert_logs table
    op.create_table('alert_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create backtest_results table
    op.create_table('backtest_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('final_capital', sa.Float(), nullable=False),
        sa.Column('total_return', sa.Float(), nullable=False),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('strategy_config', sa.JSON(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better performance
    op.create_index('idx_news_items_published_at', 'news_items', ['published_at'])
    op.create_index('idx_news_items_source', 'news_items', ['source'])
    op.create_index('idx_news_items_processed', 'news_items', ['processed'])
    
    op.create_index('idx_market_data_symbol_timestamp', 'market_data', ['symbol', 'timestamp'])
    op.create_index('idx_market_data_timestamp', 'market_data', ['timestamp'])
    
    op.create_index('idx_technical_indicators_symbol_timestamp', 'technical_indicators', ['symbol', 'timestamp'])
    
    op.create_index('idx_trading_records_timestamp', 'trading_records', ['timestamp'])
    op.create_index('idx_trading_records_status', 'trading_records', ['status'])
    op.create_index('idx_trading_records_symbol', 'trading_records', ['symbol'])
    
    op.create_index('idx_positions_status', 'positions', ['status'])
    op.create_index('idx_positions_symbol', 'positions', ['symbol'])
    
    op.create_index('idx_portfolio_timestamp', 'portfolio', ['timestamp'])
    
    op.create_index('idx_account_balances_timestamp', 'account_balances', ['timestamp'])
    
    op.create_index('idx_alert_logs_resolved', 'alert_logs', ['resolved'])
    op.create_index('idx_alert_logs_created_at', 'alert_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_alert_logs_created_at', table_name='alert_logs')
    op.drop_index('idx_alert_logs_resolved', table_name='alert_logs')
    op.drop_index('idx_account_balances_timestamp', table_name='account_balances')
    op.drop_index('idx_portfolio_timestamp', table_name='portfolio')
    op.drop_index('idx_positions_symbol', table_name='positions')
    op.drop_index('idx_positions_status', table_name='positions')
    op.drop_index('idx_trading_records_symbol', table_name='trading_records')
    op.drop_index('idx_trading_records_status', table_name='trading_records')
    op.drop_index('idx_trading_records_timestamp', table_name='trading_records')
    op.drop_index('idx_technical_indicators_symbol_timestamp', table_name='technical_indicators')
    op.drop_index('idx_market_data_timestamp', table_name='market_data')
    op.drop_index('idx_market_data_symbol_timestamp', table_name='market_data')
    op.drop_index('idx_news_items_processed', table_name='news_items')
    op.drop_index('idx_news_items_source', table_name='news_items')
    op.drop_index('idx_news_items_published_at', table_name='news_items')
    
    # Drop tables
    op.drop_table('backtest_results')
    op.drop_table('alert_logs')
    op.drop_table('system_config')
    op.drop_table('account_balances')
    op.drop_table('portfolio')
    op.drop_table('positions')
    op.drop_table('risk_assessments')
    op.drop_table('trading_decisions')
    op.drop_table('trading_records')
    op.drop_table('sentiment_analysis')
    op.drop_table('technical_indicators')
    op.drop_table('market_data')
    op.drop_table('news_items')