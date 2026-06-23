import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AuthModal } from '@/features/auth/components/AuthModal';
import { LandingPage } from '@/pages/LandingPage';
import { HomePage } from '@/pages/HomePage';
import { CaseReviewPage } from '@/pages/CaseReviewPage';
import { ResultPage } from '@/pages/ResultPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/cases/:caseId/review" element={<CaseReviewPage />} />
        <Route path="/cases/:caseId/result" element={<ResultPage />} />
      </Routes>
      <AuthModal />
    </BrowserRouter>
  );
}

export default App;
