import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { HomePage } from '@/pages/HomePage';
import { ConfirmPage } from '@/pages/ConfirmPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cases/:caseId/confirm" element={<ConfirmPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
