import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';

import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { useCaseStore, type UploadedPdf } from '@/features/case/store/caseStore';
import { Chatbot } from '@/features/home/components/Chatbot';
import { AppHeader } from '@/components/common/AppHeader';
import { PdfUpload } from '@/features/home/components/PdfUpload';
import { PolicySelector } from '@/features/insurance/components/PolicySelector';
import { POLICIES } from '@/features/insurance/data/policies';
import { cn } from '@/lib/utils';

type Step = 'select' | 'input';

export function HomePage() {
  const navigate = useNavigate();
  const setSelection = useCaseStore(state => state.setSelection);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [uploadedPdfs, setUploadedPdfs] = useState<UploadedPdf[]>([]);
  const [step, setStep] = useState<Step>('select');

  // 게이팅: 보험을 1개 이상 선택했거나 PDF를 올리면 상황 입력 가능.
  const ready = selectedIds.size > 0 || uploadedPdfs.length > 0;

  const toggle = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const startAnalysis = () => {
    // 선택/업로드 정보를 확인 페이지로 전달.
    setSelection([...selectedIds], uploadedPdfs);
    // TODO: 백엔드가 생성한 실제 case_id로 이동 (현재는 mock 케이스).
    navigate('/cases/demo/confirm');
  };

  return (
    <div className="flex min-h-screen flex-col bg-linear-to-b from-surface to-primary-tint lg:h-screen lg:overflow-hidden">
      <AppHeader />

      <div className="shrink-0 border-b border-line bg-surface/80">
        <div className="mx-auto max-w-7xl px-5 py-3 sm:px-8">
          <Stepper current={1} />
        </div>
      </div>

      <main className="mx-auto grid w-full max-w-7xl flex-1 gap-6 px-5 py-6 sm:px-8 lg:min-h-0 lg:grid-cols-[minmax(0,1fr)_minmax(360px,440px)]">
        {/* 1단계: 보험/PDF 선택 (모바일은 select 스텝에서만 표시) */}
        <div
          className={cn('flex-col gap-6 lg:flex lg:min-h-0', step === 'select' ? 'flex' : 'hidden')}
        >
          <PolicySelector
            policies={POLICIES}
            selectedIds={selectedIds}
            onToggle={toggle}
            className="lg:min-h-0 lg:flex-8"
          />
          <PdfUpload
            onSelect={file =>
              setUploadedPdfs(prev => [...prev, { id: `pdf-${Date.now()}`, name: file.name }])
            }
            className="lg:min-h-0 lg:flex-2"
          />

          {/* 모바일 전용: 다음 단계로 넘어가는 스티키 CTA */}
          <div className="sticky bottom-4 z-10 lg:hidden">
            <Button
              type="button"
              size="lg"
              className="w-full shadow-lg"
              disabled={!ready}
              onClick={() => setStep('input')}
            >
              {ready ? '상황 입력하기' : '보험을 먼저 선택해주세요'}
              {ready && <ArrowRight />}
            </Button>
          </div>
        </div>

        {/* 2단계: 챗봇으로 상황 입력 (모바일은 input 스텝에서만 표시) */}
        <div
          className={cn(
            'flex-col gap-3 lg:flex lg:h-auto lg:min-h-0',
            step === 'input' ? 'flex h-[calc(100dvh-6rem)]' : 'hidden'
          )}
        >
          {/* 모바일 전용: 선택 단계로 돌아가기 */}
          <button
            type="button"
            onClick={() => setStep('select')}
            className="flex shrink-0 items-center gap-1.5 self-start text-sm font-medium text-muted transition-colors hover:text-ink lg:hidden"
          >
            <ArrowLeft className="size-4" />
            보험 다시 선택
          </button>

          <Chatbot locked={!ready} className="min-h-0 flex-1" onStartAnalysis={startAnalysis} />
        </div>
      </main>
    </div>
  );
}

export default HomePage;
