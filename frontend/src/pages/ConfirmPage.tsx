import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Stepper } from '@/components/common/Stepper';
import { getCaseDashboard } from '@/features/case/api/cases';
import { useCaseStore } from '@/features/case/store/caseStore';
import { ClaimSection, type ClaimOption } from '@/features/confirm/components/ClaimSection';
import { ConfirmActions } from '@/features/confirm/components/ConfirmActions';
import { ConfirmFormSkeleton } from '@/features/confirm/components/ConfirmFormSkeleton';
import { DiagnosisSection } from '@/features/confirm/components/DiagnosisSection';
import { PolicyEnrollmentSection } from '@/features/confirm/components/PolicyEnrollmentSection';
import { TreatmentSection } from '@/features/confirm/components/TreatmentSection';
import { VisitSection } from '@/features/confirm/components/VisitSection';
import { AppHeader } from '@/features/home/components/AppHeader';
import { INSURERS } from '@/features/insurance/data/insurers';
import { POLICIES } from '@/features/insurance/data/policies';
import type { CaseDashboard } from '@/types/case';

const MIN_SKELETON_MS = 500;

export function ConfirmPage() {
  const { caseId = '' } = useParams();
  const navigate = useNavigate();
  const selectedPolicyIds = useCaseStore(state => state.selectedPolicyIds);
  const uploadedPdfs = useCaseStore(state => state.uploadedPdfs);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<CaseDashboard | null>(null);
  const [claimedPolicyIds, setClaimedPolicyIds] = useState<string[]>([]);
  const [enrollmentDate, setEnrollmentDate] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    const minimumDelay = new Promise(resolve => {
      window.setTimeout(resolve, MIN_SKELETON_MS);
    });

    Promise.all([getCaseDashboard(caseId), minimumDelay]).then(([res]) => {
      if (alive) {
        setForm(res.dashboard);
        setLoading(false);
      }
    });
    return () => {
      alive = false;
    };
  }, [caseId]);

  const patch = (partial: Partial<CaseDashboard>) =>
    setForm(prev => (prev ? { ...prev, ...partial } : prev));

  const toggleTreatment = (item: string) =>
    setForm(prev =>
      prev
        ? {
            ...prev,
            treatment_items: prev.treatment_items.includes(item)
              ? prev.treatment_items.filter(t => t !== item)
              : [...prev.treatment_items, item],
          }
        : prev
    );

  const addVisitDate = (date: string) => {
    if (!date) {
      return;
    }
    setForm(prev =>
      prev && !prev.visit_dates.includes(date)
        ? { ...prev, visit_dates: [...prev.visit_dates, date] }
        : prev
    );
  };

  const removeVisitDate = (date: string) =>
    setForm(prev =>
      prev ? { ...prev, visit_dates: prev.visit_dates.filter(d => d !== date) } : prev
    );

  const toggleClaimed = (id: string) =>
    setClaimedPolicyIds(prev => (prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]));

  // 홈에서 선택/업로드한 보험만 후보로 (선택 보험 + 업로드 PDF).
  const claimOptions: ClaimOption[] = [
    ...selectedPolicyIds.map(id => {
      const policy = POLICIES.find(p => p.id === id);
      return { id, label: policy ? INSURERS[policy.insurerId].name : id };
    }),
    ...uploadedPdfs.map(pdf => ({ id: pdf.id, label: pdf.name })),
  ];

  // 분석 대상 = 후보 − 기청구 보험 (자동 계산, 잠금 표시).
  const analysisTargets = claimOptions.filter(o => !claimedPolicyIds.includes(o.id));

  const canSubmit = Boolean(form?.disease_name.trim());

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-linear-to-b from-surface to-primary-tint">
      <AppHeader />

      <div className="shrink-0 border-b border-line bg-surface/80">
        <div className="mx-auto max-w-5xl px-5 py-4 sm:px-8">
          <Stepper current={2} />
        </div>
      </div>

      <main className="scrollbar-hide mx-auto min-h-0 w-full max-w-5xl flex-1 overflow-y-auto px-5 py-8 sm:px-8">
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">입력하신 내용을 확인해주세요</h1>
        <p className="mt-2 text-sm text-muted">
          정확한 분석을 위해 아래 정보를 확인하고 입력해주세요.
        </p>

        {loading || !form ? (
          <ConfirmFormSkeleton />
        ) : (
          <div className="animate-confirm-form-enter mt-6 rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-7">
            <DiagnosisSection form={form} patch={patch} />
            <TreatmentSection form={form} onToggleTreatment={toggleTreatment} />
            <VisitSection
              form={form}
              patch={patch}
              onAddVisitDate={addVisitDate}
              onRemoveVisitDate={removeVisitDate}
            />
            <PolicyEnrollmentSection
              enrollmentDate={enrollmentDate}
              onChangeEnrollmentDate={setEnrollmentDate}
            />
            <ClaimSection
              claimOptions={claimOptions}
              claimedPolicyIds={claimedPolicyIds}
              analysisTargets={analysisTargets}
              onToggleClaimed={toggleClaimed}
            />
            <ConfirmActions
              disabled={!canSubmit}
              onSubmit={() => navigate(`/cases/${caseId}/result`)}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default ConfirmPage;
