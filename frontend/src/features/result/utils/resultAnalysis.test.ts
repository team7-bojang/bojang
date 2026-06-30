import { describe, expect, it } from 'vitest';

import type { AnalysisSearchResult } from '../model';
import { buildCoverageGroups } from './resultAnalysis';

function makeResult(overrides: Partial<AnalysisSearchResult>): AnalysisSearchResult {
  return {
    policy: 'KB 건강보험',
    rider: '특약',
    rider_id: 'r1',
    status: 'eligible',
    coverage_kind: '정액',
    is_daily: false,
    gap_days: null,
    payable_days: null,
    estimated_amount: 0,
    calc: null,
    explanation: '',
    ...overrides,
  };
}

describe('buildCoverageGroups', () => {
  it('상품 × 일당/정액 단위로 묶고 입력 순서를 유지한다', () => {
    const { coverageGroups, groupRiderIds } = buildCoverageGroups([
      makeResult({ policy: 'KB 건강', rider_id: 'a', rider: '암진단', is_daily: false }),
      makeResult({ policy: 'KB 건강', rider_id: 'b', rider: '입원일당', is_daily: true }),
      makeResult({ policy: 'KB 건강', rider_id: 'c', rider: '뇌진단', is_daily: false }),
    ]);

    expect(coverageGroups.map(g => g.key)).toEqual(['KB 건강|fixed', 'KB 건강|daily']);
    // 같은 상품·정액 그룹에 정액 특약 2개가 묶인다.
    expect(groupRiderIds['KB 건강|fixed']).toEqual(['a', 'c']);
    expect(groupRiderIds['KB 건강|daily']).toEqual(['b']);
    expect(coverageGroups[0].riders).toEqual(['암진단', '뇌진단']);
  });

  it('실손·rider_id 없는 결과는 제외한다', () => {
    const { coverageGroups } = buildCoverageGroups([
      makeResult({ rider_id: 'a', coverage_kind: '실손' }),
      makeResult({ rider_id: undefined }),
      makeResult({ rider_id: 'c', coverage_kind: '정액' }),
    ]);

    expect(coverageGroups).toHaveLength(1);
    expect(groupRiderIdsKeys(coverageGroups)).toEqual(['KB 건강보험|fixed']);
  });

  it('같은 rider_id 중복 입력은 한 번만 담는다', () => {
    const { groupRiderIds } = buildCoverageGroups([
      makeResult({ policy: 'DB손해', rider_id: 'x', rider: '입원일당', is_daily: true }),
      makeResult({ policy: 'DB손해', rider_id: 'x', rider: '입원일당', is_daily: true }),
    ]);

    expect(groupRiderIds['DB손해|daily']).toEqual(['x']);
  });
});

function groupRiderIdsKeys(groups: { key: string }[]) {
  return groups.map(g => g.key);
}
