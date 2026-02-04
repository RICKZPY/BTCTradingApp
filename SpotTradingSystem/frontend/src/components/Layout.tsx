import React, { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useWebSocket, ConnectionState } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { connectionState, connectionId, messageCount } = useWebSocket();
  const { language, setLanguage, t } = useLanguage();

  const navigation = [
    { name: t('nav.dashboard'), href: '/', icon: '📊' },
    { name: t('nav.portfolio'), href: '/portfolio', icon: '💼' },
    { name: t('nav.trading'), href: '/trading', icon: '📈' },
    { name: t('nav.strategies'), href: '/strategies', icon: '🧠' },
    { name: t('nav.analysis'), href: '/analysis', icon: '🔍' },
    { name: t('nav.backtesting'), href: '/backtesting', icon: '⏮️' },
    { name: t('nav.monitoring'), href: '/monitoring', icon: '🔧' },
    { name: t('nav.settings'), href: '/settings', icon: '⚙️' }
  ];

  const getConnectionStatusColor = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return 'bg-green-500';
      case ConnectionState.CONNECTING:
        return 'bg-yellow-500';
      case ConnectionState.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return t('settings.connected');
      case ConnectionState.CONNECTING:
        return t('settings.connecting');
      case ConnectionState.ERROR:
        return t('settings.connection_error');
      default:
        return t('settings.disconnected');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Bitcoin Trading System
              </h1>
            </div>

            {/* Language Switcher and Connection Status */}
            <div className="flex items-center space-x-4">
              {/* Language Switcher */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">{t('language.switch')}:</span>
                <button
                  onClick={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  {language === 'zh' ? 'English' : '中文'}
                </button>
              </div>

              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`}></div>
                <span className="text-sm text-gray-600">
                  {getConnectionStatusText()}
                </span>
                {connectionId && (
                  <span className="text-xs text-gray-400">
                    ID: {connectionId.slice(-8)}
                  </span>
                )}
                {messageCount > 0 && (
                  <span className="text-xs text-gray-400">
                    {t('settings.message_count')}: {messageCount}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm min-h-screen">
          <div className="p-4">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      to={item.href}
                      className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span>{item.name}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;