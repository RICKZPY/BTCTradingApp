# Bitcoin Trading System Frontend

A React-based frontend application for the Bitcoin Trading System with real-time data visualization and trading capabilities.

## Features

- **Dashboard**: Overview of portfolio performance, system status, and recent alerts
- **Portfolio**: Real-time position tracking with P&L calculations
- **Trading**: Manual order placement and order history management
- **Analysis**: Market sentiment and technical analysis visualization
- **Settings**: System configuration and connection management

## Real-time Features

- WebSocket integration for live price updates
- Real-time portfolio value changes
- Live order status updates
- System alerts and notifications
- Market analysis updates

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will be available at `http://localhost:3000`.

### Backend Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1` and WebSocket at `ws://localhost:8000/api/v1/ws/stream`.

Make sure the backend server is running before starting the frontend.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx      # Main layout with navigation
├── contexts/           # React contexts for state management
│   ├── ApiContext.tsx  # REST API client and types
│   └── WebSocketContext.tsx  # WebSocket connection management
├── pages/              # Main application pages
│   ├── Dashboard.tsx   # Portfolio overview and system status
│   ├── Portfolio.tsx   # Position tracking and P&L
│   ├── Trading.tsx     # Order placement and history
│   ├── Analysis.tsx    # Market analysis visualization
│   └── Settings.tsx    # System configuration
├── App.tsx             # Main application component
├── index.tsx           # Application entry point
└── index.css           # Global styles with Tailwind CSS
```

## API Integration

The frontend uses two main integration points:

1. **REST API** (`ApiContext`): For data fetching and command execution
2. **WebSocket** (`WebSocketContext`): For real-time updates and notifications

### Available API Endpoints

- System management (start/stop/status)
- Portfolio and position data
- Trading operations (place/cancel orders)
- Market data and analysis
- Health monitoring

### WebSocket Subscriptions

- Price updates (`price_data`)
- Order updates (`order_updates`)
- Portfolio updates (`portfolio_updates`)
- System alerts (`system_alerts`)
- Analysis updates (`analysis_updates`)

## Development

### Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App

### Styling

The application uses Tailwind CSS for styling with a clean, modern design focused on data visualization and usability.

## Production Deployment

1. Build the application:
   ```bash
   npm run build
   ```

2. Serve the `build` directory with a web server

3. Configure the backend API URL in production environment

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**: Ensure backend server is running and WebSocket endpoint is accessible
2. **API calls fail**: Check backend server status and CORS configuration
3. **Real-time updates not working**: Verify WebSocket subscriptions are active

### Development Tips

- Use browser developer tools to monitor WebSocket messages
- Check the Network tab for API request/response details
- Monitor console for error messages and warnings