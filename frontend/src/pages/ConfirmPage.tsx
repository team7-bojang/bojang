import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard, saveCaseDashboard } from '@/features/case/queries';
import { useCaseStore } from '@/features/case/store/caseStore';
import { ClaimSection, type ClaimOption } from '@/features/confirm/components/ClaimSection';
import { ConfirmActions } from '@/features/confirm/components/ConfirmActions';
import { ConfirmFormSkeleton } from '@/features/confirm/components/ConfirmFormSkeleton';
import { DiagnosisSection } from '@/features/confirm/components/DiagnosisSection';
import { PolicyEnrollmentSection } from '@/features/confirm/components/PolicyEnrollmentSection';
import { TreatmentSection } from '@/features/confirm/components/TreatmentSection';
import { VisitSection } from '@/features/confirm/components/VisitSection';
import { AppHeader } from '@/components/common/AppHeader';
import { INSURERS } from '@/features/insurance/data/insurers';
import { fetchMyPolicyOptions } from '@/features/insurance/queries';
import type { PolicyOption } from '@/features/insurance/model';
import { compareCaseAnalysis, searchCaseAnalysis } from '@/features/result/api/analysis';
import type { CaseDashboard, ServiceType } from '@/types/case';

const MIN_SKELETON_MS = 500;

export function ConfirmPage() {
  const { caseId = '' } = useParams();
  const navigate = useNavigate();
  const selectedPolicyIds = useCaseStore(state => state.selectedPolicyIds);
  const selectedPolicies = useCaseStore(state => state.selectedPolicies);
  const uploadedPdfs = useCaseStore(state => state.uploadedPdfs);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState<CaseDashboard | null>(null);
  const [serviceType, setServiceType] = useState<ServiceType>('CASE1');
  const [saving, setSaving] = useState(false);
  const [claimedPolicyIds, setClaimedPolicyIds] = useState<string[]>([]);
  const [enrollmentDate, setEnrollmentDate] = useState<string | null>(null);
  const [fetchedPolicyOptions, setFetchedPolicyOptions] = useState<PolicyOption[]>([]);

  useEffect(() => {
    let alive = true;

    const minimumDelay = new Promise(resolve => {
      window.setTimeout(resolve, MIN_SKELETON_MS);
    });

    Promise.all([fetchCaseDashboard(caseId), minimumDelay])
      .then(([res]) => {
        if (alive) {
          setForm(res.dashboard);
          setServiceType(res.service_type);
          setLoading(false);
        }
      })
      .catch(() => {
        if (alive) {
          setError(true);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, [caseId, reloadKey]);

  useEffect(() => {
    if (selectedPolicies.length > 0) {
      return;
    }

    let alive = true;
    fetchMyPolicyOptions()
      .then(options => {
        if (alive) {
          setFetchedPolicyOptions(options);
        }
      })
      .catch(error => {
        console.warn('[Policies] 내 보험 목록 조회 실패:', error);
      });

    return () => {
      alive = false;
    };
  }, [selectedPolicies]);

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

  const policyOptions = selectedPolicies.length > 0 ? selectedPolicies : fetchedPolicyOptions;

  // 홈에서 선택/업로드한 보험만 후보로 (선택 보험 + 업로드 PDF).
  const claimOptions: ClaimOption[] = [
    ...(selectedPolicyIds.length > 0
      ? selectedPolicyIds
      : policyOptions.map(policy => policy.id)
    ).map(id => {
      const policy = policyOptions.find(p => p.id === id);
      return { id, label: policy ? INSURERS[policy.insurerId].name : id };
    }),
    ...uploadedPdfs.map(pdf => ({ id: pdf.id, label: pdf.name })),
  ];

  // 분석 대상 = 후보 − 기청구 보험 (자동 계산, 잠금 표시).
  const analysisTargets = claimOptions.filter(o => !claimedPolicyIds.includes(o.id));

  const canSubmit = Boolean(form?.disease_name.trim());
  const submit = async () => {
    if (!form || saving) {
      return;
    }

    setSaving(true);
    try {
      await saveCaseDashboard(caseId, form);
      if (serviceType === 'CASE2') {
        const currentDays = form.admission_days_current ?? 0;
        const targetDays = form.admission_days_diagnosed ?? currentDays;
        const comparison = await compareCaseAnalysis(caseId, currentDays, targetDays);
        navigate(`/cases/${caseId}/result`, { state: { comparison, serviceType } });
        return;
      }
      const analysis = await searchCaseAnalysis(caseId);
      navigate(`/cases/${caseId}/result`, { state: { analysis, serviceType } });
    } catch {
      setError(true);
    } finally {
      setSaving(false);
    }
  };

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

        {loading ? (
          <ConfirmFormSkeleton />
        ) : error || !form ? (
          <div className="mt-6 flex flex-col items-center gap-4 rounded-card bg-surface p-10 text-center shadow-sm ring-1 ring-line">
            <p className="text-sm text-muted">
              정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setLoading(true);
                setError(false);
                setReloadKey(k => k + 1);
              }}
            >
              다시 시도
            </Button>
          </div>
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
            <ConfirmActions disabled={!canSubmit || saving} onSubmit={submit} />
          </div>
        )}
      </main>
    </div>
  );
}

export default ConfirmPage;
