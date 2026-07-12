import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { AppHeader } from '@/components/common/AppHeader';
import { Stepper } from '@/components/common/Stepper';
import { Button } from '@/components/ui/button';
import { fetchCaseDashboard, saveCaseDashboard } from '@/features/case/queries';
import { useCaseStore } from '@/features/case/store/caseStore';
import { AnalysisLoadingScreen } from '@/features/confirm/components/AnalysisLoadingScreen';
import { ClaimSection, type ClaimOption } from '@/features/confirm/components/ClaimSection';
import { ConfirmActions } from '@/features/confirm/components/ConfirmActions';
import { ConfirmFormSkeleton } from '@/features/confirm/components/ConfirmFormSkeleton';
import { DiagnosisSection } from '@/features/confirm/components/DiagnosisSection';
import { PolicyEnrollmentSection } from '@/features/confirm/components/PolicyEnrollmentSection';
import { TreatmentSection } from '@/features/confirm/components/TreatmentSection';
import { VisitSection } from '@/features/confirm/components/VisitSection';
import { getPolicyElapsedLabel } from '@/features/confirm/policyElapsed';
import { getTreatmentCode, getTreatmentDisplayName } from '@/features/confirm/treatmentTypes';
import { parsePolicyRiders } from '@/features/insurance/queries';
import { getParseRiderFailureMessage } from '@/features/insurance/utils';
import { searchCaseAnalysis } from '@/features/result/queries';
import { cn } from '@/lib/utils';
import type { CaseDashboard, DashboardPolicy, ServiceType, TreatmentType } from '@/types/case';
import { ChevronDown } from 'lucide-react';

const MIN_SKELETON_MS = 500;
type ConfirmSectionId = 'diagnosis' | 'treatment' | 'visit' | 'enrollment' | 'claim';

function formatWon(value: number | null) {
  return value === null ? '미입력' : `${value.toLocaleString()}원`;
}

function summarizeDiagnosis(form: CaseDashboard) {
  const visitType = form.is_inpatient ? '입원' : form.is_outpatient ? '통원' : '미선택';
  const surgery = form.is_inpatient ? ` · ${form.surgery ? '수술함' : '수술 없음'}` : '';
  const kcd = form.disease_kcd ? ` (${form.disease_kcd})` : '';

  return `${form.disease_name || '질병명 미입력'}${kcd} · ${visitType}${surgery}`;
}

function summarizeTreatments(form: CaseDashboard, treatmentTypes: TreatmentType[]) {
  if (form.treatment_items.length === 0) {
    return '선택 없음';
  }

  return form.treatment_items.map(item => getTreatmentDisplayName(item, treatmentTypes)).join(', ');
}

function summarizeVisit(form: CaseDashboard) {
  const visits = form.annual_visit_count === null ? '횟수 미입력' : `${form.annual_visit_count}회`;

  return `${formatWon(form.payment_amount)} · ${visits}`;
}

function summarizeClaim(
  claimedPolicyIds: string[],
  analysisTargets: ClaimOption[],
  claimOptions: ClaimOption[]
) {
  const labelOf = (id: string) => claimOptions.find(option => option.id === id)?.label ?? id;
  const claimedNames = claimedPolicyIds.map(labelOf);
  const claimed = `이미 청구한 보험: ${claimedNames.length > 0 ? claimedNames.join(', ') : '없음'}`;
  const targets = `확인할 보험: ${
    analysisTargets.length > 0 ? analysisTargets.map(target => target.label).join(', ') : '없음'
  }`;

  return `${claimed} · ${targets}`;
}

function AccordionSection({
  title,
  summary,
  open,
  onToggle,
  children,
}: {
  title: string;
  summary: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-card bg-surface shadow-sm ring-1 ring-line">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-canvas/60 sm:px-6"
      >
        <span className="min-w-0">
          <span className="block text-base font-bold text-ink">{title}</span>
          <span className="mt-1 block truncate text-sm text-muted">{summary}</span>
        </span>
        <ChevronDown
          className={cn(
            'size-5 shrink-0 text-muted transition-transform',
            open && 'rotate-180 text-primary'
          )}
        />
      </button>
      {open && <div className="border-t border-line px-5 py-5 sm:px-6">{children}</div>}
    </section>
  );
}

export function CaseReviewPage() {
  const { caseId = '' } = useParams();
  const navigate = useNavigate();
  const uploadedPdfs = useCaseStore(state => state.uploadedPdfs);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [parseWarning, setParseWarning] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState<CaseDashboard | null>(null);
  const [serviceType, setServiceType] = useState<ServiceType>('CASE1');
  const [saving, setSaving] = useState(false);
  const [claimedPolicyIds, setClaimedPolicyIds] = useState<string[]>([]);
  const [dashboardPolicies, setDashboardPolicies] = useState<DashboardPolicy[]>([]);
  const [treatmentTypes, setTreatmentTypes] = useState<TreatmentType[]>([]);
  const [openSections, setOpenSections] = useState<ConfirmSectionId[]>(['diagnosis']);

  useEffect(() => {
    let alive = true;

    const minimumDelay = new Promise(resolve => {
      window.setTimeout(resolve, MIN_SKELETON_MS);
    });

    const loadDashboard = async () => {
      try {
        const [res] = await Promise.all([fetchCaseDashboard(caseId), minimumDelay]);
        if (alive) {
          setForm(res.dashboard);
          setServiceType(res.service_type);
          setTreatmentTypes(res.treatment_types ?? []);
          setDashboardPolicies(res.policies ?? []);
          setLoading(false);
        }
      } catch {
        if (alive) {
          setError(true);
          setLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      alive = false;
    };
  }, [caseId, reloadKey]);

  useEffect(() => {
    if (!saving) {
      return;
    }

    const preventUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    window.addEventListener('beforeunload', preventUnload);
    return () => {
      window.removeEventListener('beforeunload', preventUnload);
    };
  }, [saving]);

  const patch = (partial: Partial<CaseDashboard>) =>
    setForm(prev => (prev ? { ...prev, ...partial } : prev));

  const toggleTreatment = (displayName: string, code: string) =>
    setForm(prev =>
      prev
        ? {
            ...prev,
            treatment_items:
              prev.treatment_items.includes(displayName) || prev.treatment_items.includes(code)
                ? prev.treatment_items.filter(t => t !== displayName && t !== code)
                : [...prev.treatment_items, displayName],
          }
        : prev
    );

  const toggleClaimed = (id: string) =>
    setClaimedPolicyIds(prev => (prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]));

  // 청구 후보 = 대시보드 응답의 케이스 보험 (서버가 진실의 원천 → 새로고침에도 일관).
  // 업로드 PDF는 스토어에 파일명이 있으면 그 라벨을 우선 사용한다.
  const claimOptions: ClaimOption[] = dashboardPolicies
    .filter((policy): policy is DashboardPolicy & { id: string } => Boolean(policy.id))
    .map(policy => {
      const uploaded = uploadedPdfs.find(pdf => pdf.id === policy.id);
      return { id: policy.id, label: uploaded?.name ?? policy.insurer ?? policy.name };
    });

  // 분석 대상 = 후보 − 기청구 보험 (자동 계산, 잠금 표시).
  const analysisTargets = claimOptions.filter(o => !claimedPolicyIds.includes(o.id));
  const toggleSection = (sectionId: ConfirmSectionId) =>
    setOpenSections(prev =>
      prev.includes(sectionId) ? prev.filter(id => id !== sectionId) : [...prev, sectionId]
    );

  const canSubmit = Boolean(form?.disease_name.trim());
  const submit = async () => {
    if (!form || saving) {
      return;
    }

    setSaving(true);
    try {
      const normalizedTreatmentItems = form.treatment_items.map(item =>
        getTreatmentCode(item, treatmentTypes)
      );
      const dashboardPayload = {
        ...form,
        treatment_items: normalizedTreatmentItems,
        policy_elapsed_days: form.policy_elapsed_days,
      };

      await saveCaseDashboard(caseId, dashboardPayload);

      // 분석 전 온디맨드 파싱: 분석 대상 약관에서 이 질병/처치 조건에 맞는 특약을 미리 추출해둔다.
      // (riders가 없으면 아래 searchCaseAnalysis 가 매칭할 특약이 없어 결과가 비게 된다.)
      // 캐시 우선(policy_id+query_hash)이라 이미 파싱된 조합이면 즉시 반환되므로 매번 호출해도 된다.
      if (form.disease_kcd) {
        const visitType = form.is_inpatient
          ? 'INPATIENT'
          : form.is_outpatient
            ? 'OUTPATIENT'
            : undefined;
        const parseResults = await Promise.allSettled(
          analysisTargets.map(target =>
            parsePolicyRiders(target.id, {
              disease_kcd: form.disease_kcd ?? '',
              disease_name: form.disease_name,
              treatment_items: normalizedTreatmentItems,
              visit_type: visitType,
              surgery: form.surgery,
            })
          )
        );
        setParseWarning(getParseRiderFailureMessage(parseResults));
      }

      // CASE1·CASE2 모두 judge 결과(analysis, case2_summary 포함)로 분석한다.
      const analysis = await searchCaseAnalysis(caseId);
      // CASE2 그래프에 필요한 입원일수는 여기서 이미 알고 있으므로 함께 넘긴다(결과 페이지의 대시보드 재호출 방지).
      const scenarioDays =
        form.admission_days_current !== null && form.admission_days_current !== undefined
          ? {
              current: form.admission_days_current,
              target: form.admission_days_diagnosed ?? form.admission_days_current,
            }
          : null;
      navigate(`/cases/${caseId}/result`, { state: { analysis, serviceType, scenarioDays } });
    } catch {
      setError(true);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-b from-surface to-primary-tint">
      <AppHeader />

      <div className="border-b border-line bg-surface/80">
        <div className="mx-auto max-w-5xl px-5 py-4 sm:px-8">
          <Stepper current={2} />
        </div>
      </div>

      <main
        className={cn(
          'mx-auto w-full max-w-5xl px-5 pt-8 sm:px-8',
          !saving && !loading && !error && form ? 'pb-40 sm:pb-32' : 'pb-8'
        )}
      >
        {!saving && (
          <>
            <h1 className="text-2xl font-bold text-ink sm:text-3xl">보장 확인에 필요한 정보에요</h1>
            <p className="mt-2 text-sm text-muted">빠진 내용이나 다른 부분이 있다면 수정해주세요</p>
          </>
        )}

        {parseWarning ? (
          <div className="mt-4 rounded-card border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {parseWarning}
          </div>
        ) : null}

        {saving ? (
          <AnalysisLoadingScreen serviceType={serviceType} />
        ) : loading ? (
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
          <div className="animate-confirm-form-enter mt-6 space-y-3">
            <AccordionSection
              title="진단 정보"
              summary={summarizeDiagnosis(form)}
              open={openSections.includes('diagnosis')}
              onToggle={() => toggleSection('diagnosis')}
            >
              <DiagnosisSection form={form} patch={patch} />
            </AccordionSection>

            <AccordionSection
              title="추가 진료"
              summary={summarizeTreatments(form, treatmentTypes)}
              open={openSections.includes('treatment')}
              onToggle={() => toggleSection('treatment')}
            >
              <div className="[&>div:first-child]:mt-0">
                <TreatmentSection
                  form={form}
                  treatmentTypes={treatmentTypes}
                  onToggleTreatment={toggleTreatment}
                  onSelectNone={() => patch({ treatment_items: [] })}
                />
              </div>
            </AccordionSection>

            <AccordionSection
              title="결제 및 방문 정보"
              summary={summarizeVisit(form)}
              open={openSections.includes('visit')}
              onToggle={() => toggleSection('visit')}
            >
              <div className="[&>div:first-child]:mt-0">
                <VisitSection form={form} patch={patch} />
              </div>
            </AccordionSection>

            <AccordionSection
              title="가입 경과일"
              summary={getPolicyElapsedLabel(form.policy_elapsed_days)}
              open={openSections.includes('enrollment')}
              onToggle={() => toggleSection('enrollment')}
            >
              <div className="[&>div:first-child]:mt-0 [&>div:first-child]:border-t-0 [&>div:first-child]:pt-0">
                <PolicyEnrollmentSection form={form} patch={patch} />
              </div>
            </AccordionSection>

            <AccordionSection
              title="청구 보험"
              summary={summarizeClaim(claimedPolicyIds, analysisTargets, claimOptions)}
              open={openSections.includes('claim')}
              onToggle={() => toggleSection('claim')}
            >
              <div className="[&>div:first-child]:mt-0">
                <ClaimSection
                  claimOptions={claimOptions}
                  claimedPolicyIds={claimedPolicyIds}
                  analysisTargets={analysisTargets}
                  onToggleClaimed={toggleClaimed}
                />
              </div>
            </AccordionSection>
          </div>
        )}
      </main>

      {!saving && !loading && !error && form && (
        <footer className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 px-5 py-3 shadow-[0_-8px_24px_rgba(15,23,42,0.06)] backdrop-blur sm:px-8">
          <div className="mx-auto max-w-5xl">
            <ConfirmActions
              disabled={!canSubmit || saving}
              onSubmit={submit}
              className="mt-0 rounded-none bg-transparent p-0"
            />
          </div>
        </footer>
      )}
    </div>
  );
}

export default CaseReviewPage;
