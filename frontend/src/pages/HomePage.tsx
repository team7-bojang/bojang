import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { useCaseStore, type UploadedPdf } from '@/features/case/store/caseStore';
import { Chatbot } from '@/features/home/components/Chatbot';
import { AppHeader } from '@/components/common/AppHeader';
import { PdfUpload } from '@/features/home/components/PdfUpload';
import { PolicySelector } from '@/features/insurance/components/PolicySelector';
import type { PolicyOption } from '@/features/insurance/model';
import { fetchPolicyOptions, uploadUserPolicy } from '@/features/insurance/queries';
import { cn } from '@/lib/utils';
import type { ServiceType } from '@/types/case';

type Step = 'select' | 'input';

export function HomePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const setSelection = useCaseStore(state => state.setSelection);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [uploadedPdfs, setUploadedPdfs] = useState<UploadedPdf[]>([]);
  const [policies, setPolicies] = useState<PolicyOption[]>([]);
  const [step, setStep] = useState<Step>('select');
  const [loadingPolicies, setLoadingPolicies] = useState(true);
  const [policyError, setPolicyError] = useState<string | null>(null);
  const [uploadingPolicy, setUploadingPolicy] = useState(false);
  const serviceType: ServiceType = searchParams.get('serviceType') === 'CASE2' ? 'CASE2' : 'CASE1';

  useEffect(() => {
    let alive = true;

    fetchPolicyOptions()
      .then(options => {
        if (alive) {
          setPolicies(options);
          setPolicyError(null);
        }
      })
      .catch(error => {
        if (alive) {
          setPolicyError(
            error instanceof Error ? error.message : '보험 목록을 불러오지 못했습니다.'
          );
        }
      })
      .finally(() => {
        if (alive) {
          setLoadingPolicies(false);
        }
      });

    return () => {
      alive = false;
    };
  }, []);

  // 게이팅: 케이스 생성 API는 policy_ids가 필요하므로 보험 선택을 필수로 둔다.
  const ready = selectedIds.size > 0;

  const toggle = (id: string) => {
    setSelectedIds(prev => {
      if (serviceType === 'CASE2') {
        return prev.has(id) ? new Set<string>() : new Set([id]);
      }

      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectedPolicyIds = [...selectedIds];

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
            policies={policies}
            selectedIds={selectedIds}
            onToggle={toggle}
            className="lg:min-h-0 lg:flex-8"
          />
          {(loadingPolicies || uploadingPolicy) && (
            <p className="rounded-card border border-line bg-surface px-4 py-3 text-sm text-muted">
              {uploadingPolicy
                ? '약관 PDF를 업로드하는 중입니다.'
                : '보험 목록을 불러오는 중입니다.'}
            </p>
          )}
          {policyError && (
            <p className="rounded-card border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {policyError}
            </p>
          )}
          <PdfUpload
            onSelect={async file => {
              setUploadingPolicy(true);
              setPolicyError(null);
              try {
                const result = await uploadUserPolicy(file);
                const previousUploadedPdfs = uploadedPdfs;
                setUploadedPdfs([{ id: result.policy_id, name: file.name }]);
                setSelectedIds(prev => {
                  const next = serviceType === 'CASE2' ? new Set<string>() : new Set(prev);
                  previousUploadedPdfs.forEach(pdf => next.delete(pdf.id));
                  next.add(result.policy_id);
                  return next;
                });
              } catch (error) {
                setPolicyError(
                  error instanceof Error ? error.message : '약관 PDF 업로드에 실패했습니다.'
                );
              } finally {
                setUploadingPolicy(false);
              }
            }}
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

          <Chatbot
            locked={!ready}
            serviceType={serviceType}
            selectedPolicyIds={selectedPolicyIds}
            className="min-h-0 flex-1"
            onCaseCreated={(_caseId, policyIds) => {
              setSelection(
                policyIds,
                uploadedPdfs,
                policies.filter(policy => policyIds.includes(policy.id))
              );
            }}
            onDone={caseId => navigate(`/cases/${caseId}/confirm`)}
          />
        </div>
      </main>
    </div>
  );
}

export default HomePage;
