import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { apiClient, formDataClient } from './api/client';
import { setupHttpInterceptors } from './api/axios.interceptor';
import App from './App.tsx';

setupHttpInterceptors(apiClient);
setupHttpInterceptors(formDataClient);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
