import React from 'react';
import StrategyEditor from '../components/StrategyEditor';
import { useLanguage } from '../contexts/LanguageContext';

const StrategiesPage: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('nav.strategies')}</h1>
        <p className="text-gray-600">{t('strategy.page_description')}</p>
      </div>

      {/* Strategy Editor */}
      <StrategyEditor />
    </div>
  );
};

export default StrategiesPage;