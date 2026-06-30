import { useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';

import { AuthModal } from '@/features/auth/components/AuthModal';
import { useAuthModalStore } from '@/features/auth/store/authModalStore';
import { supabase } from '@/lib/supabase';
import { CaseReviewPage } from '@/pages/CaseReviewPage';
import { HomePage } from '@/pages/HomePage';
import { LandingPage } from '@/pages/LandingPage';
import { LoadingPreviewPage } from '@/pages/LoadingPreviewPage';
import { ResultPage } from '@/pages/ResultPage';
import { MotionConfig } from 'framer-motion';

const PROTECTED_PATH_PREFIXES = ['/analyze', '/cases'];
const LOGIN_REQUIRED_MESSAGE = '로그인이 필요합니다. 다시 로그인해주세요.';

function AuthStateModalController() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const isProtectedPath = PROTECTED_PATH_PREFIXES.some(prefix => pathname.startsWith(prefix));
    if (!isProtectedPath) {
      return;
    }

    const openLoginModal = () => {
      useAuthModalStore.getState().switchToLoginWithMessage(LOGIN_REQUIRED_MESSAGE);
    };

    let active = true;
    const unsubscribeModal = useAuthModalStore.subscribe(state => {
      if (state.isOpen) {
        return;
      }

      void supabase.auth.getSession().then(({ data }) => {
        if (active && !data.session) {
          navigate('/', { replace: true });
        }
      });
    });

    void supabase.auth.getSession().then(({ data }) => {
      if (active && !data.session) {
        openLoginModal();
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT' || !session) {
        openLoginModal();
      }
    });

    return () => {
      active = false;
      unsubscribeModal();
      subscription.unsubscribe();
    };
  }, [navigate, pathname]);

  return null;
}

function App() {
  return (
    <MotionConfig reducedMotion="never">
      <BrowserRouter>
        <AuthStateModalController />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/loading-preview" element={<LoadingPreviewPage />} />
          <Route path="/analyze" element={<HomePage />} />
          <Route path="/cases/:caseId/review" element={<CaseReviewPage />} />
          <Route path="/cases/:caseId/result" element={<ResultPage />} />
        </Routes>
        <AuthModal />
      </BrowserRouter>
    </MotionConfig>
  );
}

export default App;
