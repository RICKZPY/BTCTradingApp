import React, { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useLanguage } from '../contexts/LanguageContext';

interface Strategy {
  info: {
    id: string;
    name: string;
    description: string;
    author: string;
    version: string;
    created_at: string;
    updated_at: string;
    tags: string[];
  };
  code: string;
  parameters: Record<string, any>;
}

interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  code: string;
  parameters: Record<string, any>;
  tags: string[];
}

const StrategyEditor: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    code: '',
    parameters: '{}',
    tags: '',
    author: 'User'
  });
  
  // Validation state
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
  } | null>(null);

  // Load strategies and templates
  const loadData = async () => {
    try {
      setError(null);
      
      // Load strategies
      try {
        const strategiesResponse = await api.request('/api/v1/strategies');
        if (strategiesResponse && strategiesResponse.success && strategiesResponse.data) {
          const strategiesData = Array.isArray(strategiesResponse.data) ? strategiesResponse.data : [];
          setStrategies(strategiesData);
        } else {
          console.warn('Failed to load strategies:', strategiesResponse);
          setStrategies([]);
        }
      } catch (strategiesError: any) {
        console.error('Error loading strategies:', strategiesError);
        setStrategies([]);
      }
      
      // Load templates
      try {
        const templatesResponse = await api.request('/api/v1/strategies/templates');
        if (templatesResponse && templatesResponse.success && templatesResponse.data) {
          const templatesData = Array.isArray(templatesResponse.data) ? templatesResponse.data : [];
          setTemplates(templatesData);
        } else {
          console.warn('Failed to load templates:', templatesResponse);
          setTemplates([]);
        }
      } catch (templatesError: any) {
        console.error('Error loading templates:', templatesError);
        setTemplates([]);
      }
      
    } catch (err: any) {
      console.error('Error loading strategy data:', err);
      setError(`加载数据失败: ${err.message || 'Unknown error'}`);
      setStrategies([]);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initializeData = async () => {
      try {
        await loadData();
      } catch (error) {
        console.error('Failed to initialize strategy data:', error);
        setError('初始化失败，请刷新页面重试');
        setLoading(false);
      }
    };
    
    initializeData();
  }, []);

  const handleFormChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear validation when code changes
    if (field === 'code') {
      setValidationResult(null);
    }
  };

  const validateCode = async () => {
    if (!formData.code.trim()) {
      setValidationResult({ valid: false, errors: ['代码不能为空'] });
      return;
    }
    
    try {
      const response = await api.request('/api/v1/strategies/validate', {
        method: 'POST',
        body: JSON.stringify({ code: formData.code })
      });
      
      if (response && response.success && response.data) {
        setValidationResult(response.data);
      } else {
        setValidationResult({ valid: false, errors: ['验证失败'] });
      }
    } catch (err: any) {
      console.error('Error validating code:', err);
      setError(`代码验证失败: ${err.message || 'Unknown error'}`);
      setValidationResult({ valid: false, errors: ['验证错误'] });
    }
  };

  const handleSave = async () => {
    try {
      setError(null);
      setSuccess(null);
      
      // Validate required fields
      if (!formData.name.trim()) {
        setError('策略名称不能为空');
        return;
      }
      
      if (!formData.code.trim()) {
        setError('策略代码不能为空');
        return;
      }
      
      // Parse parameters
      let parameters = {};
      try {
        parameters = JSON.parse(formData.parameters);
      } catch (e) {
        setError('参数格式错误，请输入有效的JSON');
        return;
      }
      
      // Parse tags
      const tags = formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
      
      const requestData = {
        name: formData.name,
        description: formData.description,
        code: formData.code,
        parameters,
        tags,
        author: formData.author
      };
      
      let response;
      if (isCreating) {
        response = await api.request('/api/v1/strategies', {
          method: 'POST',
          body: JSON.stringify(requestData)
        });
      } else if (selectedStrategy) {
        response = await api.request(`/api/v1/strategies/${selectedStrategy.info.id}`, {
          method: 'PUT',
          body: JSON.stringify(requestData)
        });
      }
      
      if (response?.success) {
        setSuccess(isCreating ? t('strategy.created') : t('strategy.updated'));
        setIsCreating(false);
        setIsEditing(false);
        await loadData();
        
        // Select the created/updated strategy
        if (response.data) {
          const updatedStrategy = response.data;
          setSelectedStrategy(updatedStrategy);
        }
      } else {
        setError(response?.message || '保存失败');
      }
      
    } catch (err: any) {
      console.error('Error saving strategy:', err);
      const errorMessage = err.response?.data?.detail || err.message || '保存策略失败';
      setError(errorMessage);
    }
  };

  const handleDelete = async (strategyId: string) => {
    if (!window.confirm(t('strategy.delete_confirm'))) {
      return;
    }
    
    try {
      setError(null);
      
      const response = await api.request(`/api/v1/strategies/${strategyId}`, {
        method: 'DELETE'
      });
      
      if (response.success) {
        setSuccess(t('strategy.deleted'));
        if (selectedStrategy?.info.id === strategyId) {
          setSelectedStrategy(null);
        }
        await loadData();
      } else {
        setError(response.message || t('common.error'));
      }
      
    } catch (err: any) {
      console.error('Error deleting strategy:', err);
      setError(err.response?.data?.detail || '删除策略失败');
    }
  };

  const handleTestStrategy = async (strategyId: string) => {
    try {
      setError(null);
      
      const response = await api.request(`/api/v1/strategies/${strategyId}/test`, {
        method: 'POST'
      });
      
      if (response.success) {
        if (response.data.test_passed) {
          setSuccess(t('strategy.test_passed'));
        } else {
          setError(`${t('strategy.test_failed')}: ${response.data.error_message}`);
        }
      } else {
        setError(response.message || t('strategy.test_failed'));
      }
      
    } catch (err: any) {
      console.error('Error testing strategy:', err);
      setError(err.response?.data?.detail || '测试策略失败');
    }
  };

  const startCreating = (template?: StrategyTemplate) => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedStrategy(null);
    setValidationResult(null);
    
    if (template) {
      setFormData({
        name: `${template.name} (副本)`,
        description: template.description,
        code: template.code,
        parameters: JSON.stringify(template.parameters, null, 2),
        tags: template.tags.join(', '),
        author: 'User'
      });
    } else {
      setFormData({
        name: '',
        description: '',
        code: '',
        parameters: '{}',
        tags: '',
        author: 'User'
      });
    }
  };

  const startEditing = (strategy: Strategy) => {
    setIsEditing(true);
    setIsCreating(false);
    setSelectedStrategy(strategy);
    setValidationResult(null);
    
    setFormData({
      name: strategy.info.name,
      description: strategy.info.description,
      code: strategy.code,
      parameters: JSON.stringify(strategy.parameters, null, 2),
      tags: strategy.info.tags.join(', '),
      author: strategy.info.author
    });
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setIsCreating(false);
    setValidationResult(null);
    setFormData({
      name: '',
      description: '',
      code: '',
      parameters: '{}',
      tags: '',
      author: 'User'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="text-green-800">{success}</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow">
            {/* Header */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">{t('strategy.list')}</h3>
                <button
                  onClick={() => startCreating()}
                  className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  {t('strategy.create')}
                </button>
              </div>
            </div>
            
            {/* Strategy List */}
            <div className="max-h-96 overflow-y-auto">
              {strategies.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  {t('strategy.no_strategies')}
                </div>
              ) : (
                strategies.map((strategy) => (
                  <div
                    key={strategy.info.id}
                    className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                      selectedStrategy?.info.id === strategy.info.id ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => setSelectedStrategy(strategy)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{strategy.info.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{strategy.info.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {strategy.info.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="flex space-x-1 ml-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(strategy);
                          }}
                          className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                          title={t('common.edit')}
                        >
                          ✏️
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTestStrategy(strategy.info.id);
                          }}
                          className="p-1 text-green-600 hover:bg-green-100 rounded"
                          title={t('common.test')}
                        >
                          🧪
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(strategy.info.id);
                          }}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                          title={t('common.delete')}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Templates Section */}
            <div className="p-4 border-t border-gray-200">
              <h4 className="font-medium text-gray-900 mb-3">{t('strategy.templates')}</h4>
              <div className="space-y-2">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                    onClick={() => startCreating(template)}
                  >
                    <div className="font-medium text-sm text-gray-900">{template.name}</div>
                    <div className="text-xs text-gray-600 mt-1">{template.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Editor/Viewer */}
        <div className="lg:col-span-2">
          {(isEditing || isCreating) ? (
            /* Edit Form */
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  {isCreating ? t('strategy.creating') : t('strategy.editing')}
                </h3>
                <div className="space-x-2">
                  <button
                    onClick={cancelEditing}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {t('common.save')}
                  </button>
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('strategy.name')} *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => handleFormChange('name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={t('strategy.name')}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('strategy.author')}
                    </label>
                    <input
                      type="text"
                      value={formData.author}
                      onChange={(e) => handleFormChange('author', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('strategy.description')}
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleFormChange('description', e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={t('strategy.description')}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('strategy.tags')}
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => handleFormChange('tags', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={t('strategy.tags')}
                  />
                </div>
                
                {/* Code Editor */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      {t('strategy.code')} *
                    </label>
                    <button
                      onClick={validateCode}
                      className="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                    >
                      {t('strategy.validate_code')}
                    </button>
                  </div>
                  <textarea
                    value={formData.code}
                    onChange={(e) => handleFormChange('code', e.target.value)}
                    rows={20}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    placeholder={t('strategy.code')}
                  />
                  
                  {/* Validation Results */}
                  {validationResult && (
                    <div className={`mt-2 p-3 rounded-md ${
                      validationResult.valid 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className={`font-medium ${
                        validationResult.valid ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {validationResult.valid ? t('strategy.code_valid') : t('strategy.code_invalid')}
                      </div>
                      {!validationResult.valid && validationResult.errors.length > 0 && (
                        <ul className="mt-2 text-sm text-red-700">
                          {validationResult.errors.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Parameters */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('strategy.parameters')}
                  </label>
                  <textarea
                    value={formData.parameters}
                    onChange={(e) => handleFormChange('parameters', e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    placeholder='{"param1": "value1", "param2": 123}'
                  />
                </div>
              </div>
            </div>
          ) : selectedStrategy ? (
            /* Strategy Viewer */
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{selectedStrategy.info.name}</h3>
                  <p className="text-gray-600">{selectedStrategy.info.description}</p>
                </div>
                <div className="space-x-2">
                  <button
                    onClick={() => handleTestStrategy(selectedStrategy.info.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    {t('strategy.test_strategy')}
                  </button>
                  <button
                    onClick={() => startEditing(selectedStrategy)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {t('common.edit')}
                  </button>
                </div>
              </div>
              
              {/* Strategy Info */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <span className="text-sm text-gray-600">{t('strategy.author')}:</span>
                  <span className="ml-2 font-medium">{selectedStrategy.info.author}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600">{t('strategy.version')}:</span>
                  <span className="ml-2 font-medium">{selectedStrategy.info.version}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600">{t('strategy.created_at')}:</span>
                  <span className="ml-2 font-medium">
                    {new Date(selectedStrategy.info.created_at).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-sm text-gray-600">{t('strategy.updated_at')}:</span>
                  <span className="ml-2 font-medium">
                    {new Date(selectedStrategy.info.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>
              
              {/* Tags */}
              <div className="mb-6">
                <span className="text-sm text-gray-600">{t('strategy.tags')}:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {selectedStrategy.info.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Code Display */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">{t('strategy.code_display')}</h4>
                <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-sm">
                  <code>{selectedStrategy.code}</code>
                </pre>
              </div>
              
              {/* Parameters */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">{t('strategy.default_params')}</h4>
                <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-sm">
                  <code>{JSON.stringify(selectedStrategy.parameters, null, 2)}</code>
                </pre>
              </div>
            </div>
          ) : (
            /* Welcome Message */
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🧠</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{t('strategy.welcome_title')}</h3>
                <p className="text-gray-600 mb-6">
                  {t('strategy.welcome_subtitle')}
                </p>
                <div className="space-x-4">
                  <button
                    onClick={() => startCreating()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    {t('strategy.create_new')}
                  </button>
                  {templates.length > 0 && (
                    <button
                      onClick={() => startCreating(templates[0])}
                      className="px-6 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                    >
                      {t('strategy.from_template')}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyEditor;