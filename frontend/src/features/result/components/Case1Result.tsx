import type { AnalysisSearchResult, MedicalCostInput } from '../model';
import { ClaimDocumentsSection } from './ClaimDocumentsSection';
import { CoverageAmountForm, type CoverageGroupRow } from './CoverageAmountForm';
import { ResultSection } from './ResultSection';

interface Case1ResultProps {
  coverageGroups: CoverageGroupRow[];
  coverageAmounts: Record<string, number>;
  displayExpectedAmount: number | null;
  recomputing: boolean;
  onApplyInputs: (amountsByGroup: Record<string, number>, costs: MedicalCostInput) => void;
  onMeasurePanel: (height: number) => void;
  hasReimbursementRiders: boolean;
  medicalCosts: MedicalCostInput;
  payableResults: AnalysisSearchResult[];
  conditionalResults: AnalysisSearchResult[];
  payablePolicyNames: string[];
  onSelect: (result: AnalysisSearchResult) => void;
}

// CASE1 — 가입금액·병원비 입력으로 예상 보험금을 산출하고 청구 가능/조건 확인 보장을 보여준다.
export function Case1Result({
  coverageGroups,
  coverageAmounts,
  displayExpectedAmount,
  recomputing,
  onApplyInputs,
  onMeasurePanel,
  hasReimbursementRiders,
  medicalCosts,
  payableResults,
  conditionalResults,
  payablePolicyNames,
  onSelect,
}: Case1ResultProps) {
  return (
    <>
      <CoverageAmountForm
        groups={coverageGroups}
        initialAmounts={coverageAmounts}
        expectedAmount={displayExpectedAmount}
        hasReimbursementRiders={hasReimbursementRiders}
        initialMedicalCosts={medicalCosts}
        submitting={recomputing}
        onApply={onApplyInputs}
        onMeasure={onMeasurePanel}
      />

      <div className="mt-6 border-t border-line pt-6">
        <ResultSection
          title="청구 가능한 보장"
          countClassName="text-primary"
          results={payableResults}
          emptyText="현재 입력 조건에서 청구 가능한 보장은 확인되지 않았습니다."
          delay="90ms"
          onSelect={onSelect}
        />
      </div>

      {conditionalResults.length > 0 && (
        <div className="mt-6 border-t border-line pt-6">
          <ResultSection
            title="조건 확인 필요"
            countClassName="text-amber-600"
            results={conditionalResults}
            emptyText="조건 확인이 필요한 보장이 없습니다."
            delay="125ms"
            collapsible
            defaultOpen={false}
            onSelect={onSelect}
          />
        </div>
      )}

      <div className="mt-6 border-t border-line pt-6">
        <ClaimDocumentsSection policyNames={payablePolicyNames} />
      </div>
    </>
  );
}
