# BTC期权交易系统 - 前端

基于React 18 + TypeScript + Vite构建的现代化期权交易回测系统前端界面，采用Deribit风格的暗黑主题设计。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **状态管理**: Zustand
- **路由**: React Router v6
- **样式**: Tailwind CSS
- **图表**: Recharts + Plotly.js
- **表格**: TanStack Table
- **表单**: React Hook Form + Zod
- **动画**: Framer Motion
- **HTTP客户端**: Axios

## 设计特点

### Deribit风格暗黑主题
- **深色背景**: 专业交易平台风格，减少眼睛疲劳
- **圆润现代**: 使用圆角设计和现代化字体
- **单页多Tab**: 避免页面跳转，所有功能通过Tab切换
- **信息密度**: 在有限空间内展示丰富的数据和图表

### 色彩系统
- 主背景: #0B0E11 (深黑)
- 次背景: #161A1E (深灰)
- 卡片背景: #1E2329 (中灰)
- 主色: #3861FB (蓝色)
- 成功: #0ECB81 (绿色)
- 危险: #F6465D (红色)
- 警告: #F0B90B (黄色)

## 快速开始

### 1. 安装依赖

```bash
cd BTCOptionsTrading/frontend
npm install
```

### 2. 配置环境变量

复制`.env.example`到`.env`:

```bash
cp .env.example .env
```

编辑`.env`文件，配置API地址:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:3000` 启动

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到`dist`目录

### 5. 预览生产构建

```bash
npm run preview
```

## 功能模块

### 1. 策略管理 (StrategiesTab)
- 查看和管理期权策略
- 支持多种策略类型：单腿、跨式、宽跨式、铁鹰、蝶式
- 创建自定义策略
- 策略模板库

### 2. 回测分析 (BacktestTab)
- 配置回测参数
- 运行历史回测
- 查看盈亏曲线
- 分析绩效指标：收益率、夏普比率、最大回撤、胜率
- 查看交易明细
- 导出回测报告

### 3. 期权链 (OptionsChainTab)
- 实时期权链数据
- 看涨/看跌期权并排显示
- 隐含波动率热力图
- 希腊字母显示
- 执行价筛选和排序

### 4. 波动率分析 (VolatilityTab)
- 3D波动率曲面图
- 波动率期限结构
- 历史波动率vs隐含波动率对比
- 波动率微笑/偏斜图

### 5. 系统设置 (SettingsTab)
- API配置
- Deribit API密钥管理
- 交易参数设置
- 系统状态监控

## 项目结构

```
frontend/
├── src/
│   ├── api/                 # API客户端
│   │   ├── client.ts        # Axios配置
│   │   ├── types.ts         # 类型定义
│   │   ├── strategies.ts    # 策略API
│   │   ├── backtest.ts      # 回测API
│   │   └── data.ts          # 数据API
│   ├── components/          # React组件
│   │   ├── Layout.tsx       # 主布局
│   │   ├── TabNavigation.tsx # Tab导航
│   │   ├── Toast.tsx        # 通知组件
│   │   └── tabs/            # Tab页面组件
│   │       ├── StrategiesTab.tsx
│   │       ├── BacktestTab.tsx
│   │       ├── OptionsChainTab.tsx
│   │       ├── VolatilityTab.tsx
│   │       └── SettingsTab.tsx
│   ├── store/               # 状态管理
│   │   └── useAppStore.ts   # Zustand store
│   ├── App.tsx              # 应用根组件
│   ├── main.tsx             # 应用入口
│   └── index.css            # 全局样式
├── public/                  # 静态资源
├── index.html               # HTML模板
├── package.json             # 依赖配置
├── tsconfig.json            # TypeScript配置
├── vite.config.ts           # Vite配置
├── tailwind.config.js       # Tailwind配置
└── README.md                # 本文件
```

## 开发指南

### 添加新的Tab页面

1. 在`src/components/tabs/`创建新组件
2. 在`src/store/useAppStore.ts`的`TabType`添加新类型
3. 在`src/components/TabNavigation.tsx`添加Tab配置
4. 在`src/components/Layout.tsx`的`renderTab`添加路由

### 调用API

```typescript
import { strategiesApi } from '@/api/strategies'

// 获取策略列表
const strategies = await strategiesApi.list()

// 创建策略
const newStrategy = await strategiesApi.create({
  name: '我的策略',
  strategy_type: 'single_leg',
  legs: [...]
})
```

### 使用状态管理

```typescript
import { useAppStore } from '@/store/useAppStore'

function MyComponent() {
  const { activeTab, setActiveTab } = useAppStore()
  
  return (
    <button onClick={() => setActiveTab('backtest')}>
      切换到回测
    </button>
  )
}
```

## 性能优化

- 使用Vite进行快速开发和构建
- 代码分割和懒加载
- 虚拟滚动处理大数据表格
- 防抖和节流优化用户交互
- 图表按需加载

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 部署

### 静态部署

构建后将`dist`目录部署到任何静态文件服务器：

```bash
npm run build
# 将dist目录上传到服务器
```

### Docker部署

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 故障排除

### 端口冲突

如果3000端口被占用，修改`vite.config.ts`中的端口配置：

```typescript
server: {
  port: 3001, // 改为其他端口
}
```

### API连接失败

检查`.env`文件中的`VITE_API_BASE_URL`是否正确，确保后端API服务正在运行。

### 构建失败

清除缓存并重新安装依赖：

```bash
rm -rf node_modules package-lock.json
npm install
```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用MIT许可证

## 支持

如有问题，请参考：
- 后端API文档: `../backend/API_README.md`
- 项目进度: `../PROGRESS.md`
- 设计文档: `../../.kiro/specs/btc-options-trading-system/design.md`
