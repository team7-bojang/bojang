import { AppHeader } from '@/components/common/AppHeader';

/** 서비스 소개 랜딩페이지 (루트 진입점). 섹션은 후속 태스크에서 채운다. */
export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <AppHeader />
      <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-10 sm:px-8">
        <p className="text-muted">랜딩페이지 준비 중</p>
      </main>
    </div>
  );
}

export default LandingPage;
