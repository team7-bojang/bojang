import { AnalysisLoadingScreen } from '@/features/confirm/components/AnalysisLoadingScreen';

/** 광고 로딩 화면 확인용 임시 페이지. 확인이 끝나면 App 라우트와 함께 삭제한다. */
export function LoadingPreviewPage() {
  return (
    <main className="min-h-screen bg-linear-to-b from-surface to-primary-tint px-5 py-8 sm:px-8">
      <div className="mx-auto w-full max-w-5xl">
        <AnalysisLoadingScreen serviceType="CASE1" />
      </div>
    </main>
  );
}

export default LoadingPreviewPage;
