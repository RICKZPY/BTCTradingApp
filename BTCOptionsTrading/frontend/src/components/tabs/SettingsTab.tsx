import { useState, useEffect } from 'react';
import { settingsApi, DeribitConfig, TradingConfig, SystemInfo } from '@/api/settings';
import { useAppStore } from '@/store/useAppStore';

const SettingsTab = () => {
  const { showToast } = useAppStore();
  
  // Deribit配置
  const [deribitConfig, setDeribitConfig] = useState<DeribitConfig>({
    api_key: '',
    api_secret: '',
    test_mode: true,
  });
  const [deribitLoading, setDeribitLoading] = useState(false);
  const [hasDeribitCredentials, setHasDeribitCredentials] = useState(false);
  
  // 交易参数
  const [tradingConfig, setTradingConfig] = useState<TradingConfig>({
    risk_free_rate: 0.05,
    default_initial_capital: 100000,
    commission_rate: 0.001,
  });
  const [tradingLoading, setTradingLoading] = useState(false);
  
  // 系统信息
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  
  // 主网切换确认
  const [showMainnetWarning, setShowMainnetWarning] = useState(false);
  
  // 加载配置
  useEffect(() => {
    loadConfigs();
  }, []);
  
  const loadConfigs = async () => {
    try {
      // 加载Deribit配置
      const deribitData = await settingsApi.getDeribitConfig();
      setHasDeribitCredentials(deribitData.has_credentials);
      setDeribitConfig(prev => ({
        ...prev,
        api_key: deribitData.api_key || prev.api_key || '',
        api_secret: deribitData.api_secret || prev.api_secret || '',
        test_mode: deribitData.test_mode,
      }));
      
      // 加载交易配置
      const tradingData = await settingsApi.getTradingConfig();
      setTradingConfig(tradingData);
      
      // 加载系统信息
      const sysInfo = await settingsApi.getSystemInfo();
      setSystemInfo(sysInfo);
    } catch (error) {
      console.error('Failed to load configurations:', error);
      showToast('加载配置失败', 'error');
    }
  };
  
  const handleSaveDeribitConfig = async () => {
    if (!deribitConfig.api_key || !deribitConfig.api_secret) {
      showToast('请输入API Key和Secret', 'error');
      return;
    }
    
    setDeribitLoading(true);
    try {
      const result = await settingsApi.updateDeribitConfig(deribitConfig);
      showToast(result.message || 'Deribit配置保存成功', 'success');
      setHasDeribitCredentials(true);
      // 重新加载系统信息
      const sysInfo = await settingsApi.getSystemInfo();
      setSystemInfo(sysInfo);
    } catch (error: any) {
      console.error('Failed to save Deribit config:', error);
      showToast(error.response?.data?.detail || '保存配置失败', 'error');
    } finally {
      setDeribitLoading(false);
    }
  };
  
  const handleSaveTradingConfig = async () => {
    setTradingLoading(true);
    try {
      const result = await settingsApi.updateTradingConfig(tradingConfig);
      showToast(result.message || '交易参数保存成功', 'success');
    } catch (error: any) {
      console.error('Failed to save trading config:', error);
      showToast(error.response?.data?.detail || '保存参数失败', 'error');
    } finally {
      setTradingLoading(false);
    }
  };
  
  const handleToggleNetwork = () => {
    // 如果要切换到主网，显示警告
    if (deribitConfig.test_mode) {
      setShowMainnetWarning(true);
    } else {
      // 切换回测试网，直接切换
      setDeribitConfig({ ...deribitConfig, test_mode: true });
    }
  };
  
  const confirmMainnetSwitch = () => {
    setDeribitConfig({ ...deribitConfig, test_mode: false });
    setShowMainnetWarning(false);
  };
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-text-primary">系统设置</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API配置 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Deribit API配置</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-3">
                网络环境
              </label>
              <div className="flex items-center justify-between p-4 bg-bg-secondary rounded-lg border border-border-primary">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${deribitConfig.test_mode ? 'bg-accent-yellow' : 'bg-accent-green'}`}></div>
                  <div>
                    <p className="text-text-primary font-medium">
                      {deribitConfig.test_mode ? '测试网络' : '主网络'}
                    </p>
                    <p className="text-xs text-text-secondary">
                      {deribitConfig.test_mode ? 'test.deribit.com (虚拟资金)' : 'www.deribit.com (真实资金)'}
                    </p>
                  </div>
                </div>
                
                {/* Toggle Switch */}
                <button
                  type="button"
                  onClick={handleToggleNetwork}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-bg-primary ${
                    deribitConfig.test_mode ? 'bg-accent-yellow' : 'bg-accent-green'
                  }`}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                      deribitConfig.test_mode ? 'translate-x-1' : 'translate-x-7'
                    }`}
                  />
                </button>
              </div>
              
              {!deribitConfig.test_mode && (
                <div className="mt-2 p-3 bg-accent-red bg-opacity-10 border border-accent-red rounded-lg">
                  <p className="text-xs text-accent-red flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    警告：主网使用真实资金，请确保充分测试后再使用！
                  </p>
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                API Key
                {hasDeribitCredentials && (
                  <span className="ml-2 text-accent-green text-xs">✓ 已配置</span>
                )}
              </label>
              <input 
                type="text" 
                className="input w-full" 
                placeholder="输入API Key"
                value={deribitConfig.api_key || ''}
                onChange={(e) => setDeribitConfig({ ...deribitConfig, api_key: e.target.value })}
              />
            </div>
            
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                API Secret
              </label>
              <input 
                type="password" 
                className="input w-full" 
                placeholder="输入API Secret"
                value={deribitConfig.api_secret || ''}
                onChange={(e) => setDeribitConfig({ ...deribitConfig, api_secret: e.target.value })}
              />
            </div>
            
            <button 
              className="btn btn-primary w-full"
              onClick={handleSaveDeribitConfig}
              disabled={deribitLoading}
            >
              {deribitLoading ? '保存中...' : '保存配置'}
            </button>
            
            <div className="text-xs text-text-secondary mt-2">
              <p>💡 提示：保存后配置将写入.env文件，重启API服务后生效</p>
              <p className="mt-1">🔒 API密钥将安全存储，不会在界面显示</p>
            </div>
          </div>
        </div>

        {/* 交易参数 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">交易参数</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                无风险利率
              </label>
              <input 
                type="number" 
                className="input w-full" 
                value={tradingConfig.risk_free_rate}
                onChange={(e) => setTradingConfig({ ...tradingConfig, risk_free_rate: parseFloat(e.target.value) })}
                step="0.01"
                min="0"
                max="1"
              />
              <p className="text-xs text-text-secondary mt-1">
                用于期权定价的无风险利率 (0-1之间)
              </p>
            </div>
            
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                默认初始资金 ($)
              </label>
              <input 
                type="number" 
                className="input w-full" 
                value={tradingConfig.default_initial_capital}
                onChange={(e) => setTradingConfig({ ...tradingConfig, default_initial_capital: parseFloat(e.target.value) })}
                step="1000"
                min="0"
              />
              <p className="text-xs text-text-secondary mt-1">
                回测时的默认初始资金
              </p>
            </div>
            
            <div>
              <label className="block text-sm text-text-secondary mb-2">
                手续费率
              </label>
              <input 
                type="number" 
                className="input w-full" 
                value={tradingConfig.commission_rate}
                onChange={(e) => setTradingConfig({ ...tradingConfig, commission_rate: parseFloat(e.target.value) })}
                step="0.0001"
                min="0"
                max="1"
              />
              <p className="text-xs text-text-secondary mt-1">
                交易手续费率 (Deribit默认0.03% = 0.0003)
              </p>
            </div>
            
            <button 
              className="btn btn-primary w-full"
              onClick={handleSaveTradingConfig}
              disabled={tradingLoading}
            >
              {tradingLoading ? '保存中...' : '保存参数'}
            </button>
          </div>
        </div>
      </div>

      {/* 系统信息 */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">系统信息</h3>
        {systemInfo ? (
          <div className="space-y-4">
            {/* 第一行：基本信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-text-secondary text-sm">版本</p>
                <p className="text-text-primary font-medium">{systemInfo.version}</p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">环境</p>
                <p className="text-text-primary font-medium capitalize">{systemInfo.environment}</p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">API状态</p>
                <p className={`font-medium ${systemInfo.api_status === 'online' ? 'text-accent-green' : 'text-accent-red'}`}>
                  ● {systemInfo.api_status === 'online' ? '在线' : '离线'}
                </p>
              </div>
              <div>
                <p className="text-text-secondary text-sm">数据库</p>
                <p className={`font-medium ${systemInfo.database_status === 'connected' ? 'text-accent-green' : 'text-accent-red'}`}>
                  ● {(systemInfo.database_type || 'unknown').toUpperCase()} 
                  <span className="text-xs ml-1">
                    ({systemInfo.database_status === 'connected' ? '已连接' : '未连接'})
                  </span>
                </p>
              </div>
            </div>
            
            {/* 第二行：Deribit状态 */}
            <div className="p-4 bg-bg-secondary rounded-lg border border-border-primary">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    systemInfo.deribit_status === 'configured' 
                      ? (systemInfo.deribit_mode === 'test' ? 'bg-accent-yellow bg-opacity-20' : 'bg-accent-green bg-opacity-20')
                      : 'bg-gray-500 bg-opacity-20'
                  }`}>
                    <svg className={`w-6 h-6 ${
                      systemInfo.deribit_status === 'configured'
                        ? (systemInfo.deribit_mode === 'test' ? 'text-accent-yellow' : 'text-accent-green')
                        : 'text-gray-500'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-text-primary font-medium">Deribit API</p>
                    <p className="text-sm text-text-secondary">
                      {systemInfo.deribit_status === 'configured' ? (
                        <>
                          <span className={systemInfo.deribit_mode === 'test' ? 'text-accent-yellow' : 'text-accent-green'}>
                            ● {systemInfo.deribit_mode === 'test' ? '测试网络' : '主网络'}
                          </span>
                          <span className="mx-2">•</span>
                          <span className="text-accent-green">已配置</span>
                        </>
                      ) : (
                        <span className="text-accent-yellow">● 未配置</span>
                      )}
                    </p>
                  </div>
                </div>
                
                {systemInfo.deribit_status === 'configured' && (
                  <div className="text-right">
                    <p className="text-xs text-text-secondary">连接地址</p>
                    <p className="text-xs text-text-primary font-mono">
                      {systemInfo.deribit_mode === 'test' ? 'test.deribit.com' : 'www.deribit.com'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-blue"></div>
            <p className="ml-3 text-text-secondary">加载系统信息...</p>
          </div>
        )}
      </div>
      
      {/* 主网切换警告对话框 */}
      {showMainnetWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-bg-primary border border-border-primary rounded-lg p-6 max-w-md mx-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <svg className="w-12 h-12 text-accent-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  切换到主网络
                </h3>
                <p className="text-text-secondary mb-4">
                  您即将切换到Deribit主网络（www.deribit.com）。主网使用真实资金进行交易。
                </p>
                <div className="bg-accent-red bg-opacity-10 border border-accent-red rounded-lg p-3 mb-4">
                  <p className="text-sm text-accent-red font-medium mb-2">⚠️ 重要提示：</p>
                  <ul className="text-xs text-accent-red space-y-1 list-disc list-inside">
                    <li>主网交易使用真实资金</li>
                    <li>所有交易都会产生实际费用</li>
                    <li>建议先在测试网充分测试</li>
                    <li>确保您了解相关风险</li>
                  </ul>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowMainnetWarning(false)}
                    className="flex-1 px-4 py-2 bg-bg-secondary text-text-primary rounded-lg hover:bg-opacity-80 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={confirmMainnetSwitch}
                    className="flex-1 px-4 py-2 bg-accent-red text-white rounded-lg hover:bg-opacity-90 transition-colors font-medium"
                  >
                    确认切换
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SettingsTab
