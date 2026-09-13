import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { WorkflowProvider } from './context/WorkflowContext'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <WorkflowProvider>
      <App />
    </WorkflowProvider>
  </React.StrictMode>,
)
