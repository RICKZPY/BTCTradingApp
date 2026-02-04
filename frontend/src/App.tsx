import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Trading from './pages/Trading';
import Strategies from './pages/Strategies';
import Analysis from './pages/Analysis';
import Backtesting from './pages/Backtesting';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';
import { ApiProvider } from './contexts/ApiContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { LanguageProvider } from './contexts/LanguageContext';

function App() {
  return (
    <LanguageProvider>
      <ApiProvider>
        <WebSocketProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/portfolio" element={<Portfolio />} />
                <Route path="/trading" element={<Trading />} />
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/backtesting" element={<Backtesting />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </Router>
        </WebSocketProvider>
      </ApiProvider>
    </LanguageProvider>
  );
}

export default App;