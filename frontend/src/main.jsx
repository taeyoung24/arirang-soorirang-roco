import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'src/settings'
import App from './App.jsx'
import './i18n'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
