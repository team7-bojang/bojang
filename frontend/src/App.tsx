import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { HomePage } from '@/pages/HomePage';
import { ConfirmPage } from '@/pages/ConfirmPage';
import { ResultPage } from '@/pages/ResultPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cases/:caseId/confirm" element={<ConfirmPage />} />
        <Route path="/cases/:caseId/result" element={<ResultPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
