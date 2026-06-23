import { AppHeader } from '@/components/common/AppHeader';
import { HeroSection } from '@/features/landing/components/HeroSection';
import { ScenarioSection } from '@/features/landing/components/ScenarioSection';
import { ValueSection } from '@/features/landing/components/ValueSection';
import { LandingFooter } from '@/features/landing/components/LandingFooter';

/** 서비스 소개 랜딩페이지 (루트 진입점). */
export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <AppHeader />
      <main className="flex-1">
        <HeroSection />
        <ScenarioSection />
        <ValueSection />
      </main>
      <LandingFooter />
    </div>
  );
}

export default LandingPage;
