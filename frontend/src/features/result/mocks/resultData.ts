import type { AdditionalCoverageResultData, MissingBenefit, PayableBenefit } from '../types';

export const payableBenefits: PayableBenefit[] = [
  {
    id: 'db-hospitalization',
    title: '질병입원일당',
    insurerId: 'db',
    insurerName: 'DB손해보험',
    policyName: '참좋은상해보험',
    amount: 150000,
    analysis: {
      decision: '청구 가능',
      decisionDescription:
        '질병으로 진단 확정 후 치료 목적으로 3일 입원한 내역이 약관상 질병입원일당 지급 조건을 충족합니다.',
      clauseTitle: '질병입원일당 특약 제8조',
      clausePage: 'PDF p.42',
      clauseQuote:
        '피보험자가 질병으로 진단확정되고 치료를 목적으로 병원에 입원하여 치료를 받은 경우, 입원 1일당 보험가입금액을 지급합니다.',
      clauseHighlight: '입원 1일당 보험가입금액을 지급합니다.',
      paymentBasis: '50,000원 / 1일',
      period: '3일',
      formula: '50,000원 × 3일',
      expectedAmount: 150000,
      paymentCalculationDescription:
        '챗봇 입력 결제내역 150,000원과 별개로, 이 특약은 약관상 정액 보장이므로 가입금액 50,000원에 적용 입원일수 3일을 곱해 계산했습니다.',
    },
  },
  {
    id: 'kb-injury-hospitalization',
    title: '상해입원일당',
    insurerId: 'kb',
    insurerName: 'KB손해보험',
    policyName: 'KB건강플러스보험',
    amount: 95000,
    analysis: {
      decision: '청구 가능',
      decisionDescription:
        '상해 치료를 위한 입원 기록과 보험 가입 담보가 확인되어 입원일당 산정 대상입니다.',
      clauseTitle: '상해입원일당 특별약관 제5조',
      clausePage: 'PDF p.31',
      clauseQuote:
        '피보험자가 보험기간 중 상해의 직접 결과로 병원에 입원하여 치료를 받은 때에는 입원 1일당 약정한 보험금을 지급합니다.',
      clauseHighlight: '입원 1일당 약정한 보험금을 지급합니다.',
      paymentBasis: '95,000원 / 1일',
      period: '1일',
      formula: '95,000원 × 1일',
      expectedAmount: 95000,
      paymentCalculationDescription:
        '결제금액은 실제 치료비 참고값으로만 사용했고, 본 담보는 정액형 입원일당이므로 약관의 1일 지급 기준으로 예상 보험금을 계산했습니다.',
    },
  },
];

export const missingBenefits: MissingBenefit[] = [
  {
    id: 'samsung-fracture',
    title: '골절진단비',
    insurerId: 'hyundai',
    insurerName: '삼성화재',
    policyName: '삼성건강보험',
    reason: '1일 부족',
    condition: '입원 3일 이상',
    analysis: {
      decision: '조건 미달',
      decisionDescription:
        '현재 입력된 입원일수는 2일이며, 약관상 골절진단비 부가 담보의 입원 조건 3일 이상을 충족하지 못했습니다.',
      clauseTitle: '골절진단비 특별약관 제3조',
      clausePage: 'PDF p.18',
      clauseQuote:
        '골절로 진단확정되고 그 치료를 직접 목적으로 3일 이상 계속 입원한 경우 보험금을 지급합니다.',
      clauseHighlight: '3일 이상 계속 입원한 경우',
      paymentBasis: '지급 기준 미충족',
      period: '현재 2일 / 필요 3일',
      formula: '조건 충족 후 재산정',
      expectedAmount: 0,
      paymentCalculationDescription:
        '결제내역이 있더라도 입원일수 조건이 먼저 충족되어야 하므로 현재 단계에서는 결제금액 기반 보험금 계산을 적용하지 않았습니다.',
    },
  },
  {
    id: 'hanwha-surgery',
    title: '수술비(특정질병)',
    insurerId: 'hanwha',
    insurerName: '한화손해보험',
    policyName: '한화건강보험',
    reason: '진단명 미충족',
    condition: '특정 질병 진단 확정',
    analysis: {
      decision: '확인 필요',
      decisionDescription:
        '수술 기록은 있으나 입력된 진단명이 특약에서 정한 특정 질병 목록과 직접 매칭되지 않아 추가 확인이 필요합니다.',
      clauseTitle: '특정질병 수술비 특별약관 제4조',
      clausePage: 'PDF p.56',
      clauseQuote:
        '보장대상 특정질병으로 진단확정되고 그 치료를 직접 목적으로 수술을 받은 경우 수술 1회당 보험금을 지급합니다.',
      clauseHighlight: '보장대상 특정질병으로 진단확정',
      paymentBasis: '진단명 매칭 후 확정',
      period: '수술 1회',
      formula: '담보 가입금액 × 인정 수술 횟수',
      expectedAmount: 0,
      paymentCalculationDescription:
        '결제내역상 수술 관련 비용은 확인되지만, 해당 담보는 진단명과 수술분류가 우선 매칭되어야 하므로 현재는 예상액을 표시하지 않습니다.',
    },
  },
];

export const expectedAmount = payableBenefits.reduce((sum, benefit) => sum + benefit.amount, 0);

export const additionalCoverageResult: AdditionalCoverageResultData = {
  currentAmount: 71830,
  expectedAmount: 230000,
  explanation:
    '추가 진단, 수술, 입원일수 충족, 추가 서류 제출 등을 통해 현재 예상 금액보다 더 많은 보험금을 받을 수 있습니다.',
  candidates: [
    {
      id: 'samsung-fracture-diagnosis',
      title: '골절진단비',
      insurerId: 'hyundai',
      insurerName: '삼성화재',
      policyName: '삼성건강보험',
      potentialAmount: 100000,
      condition: '골절 진단 확정 필요',
    },
    {
      id: 'hanwha-specific-surgery',
      title: '수술비(특정질병)',
      insurerId: 'hanwha',
      insurerName: '한화손해보험',
      policyName: '한화건강보험',
      potentialAmount: 58170,
      condition: '특정 질병 진단 확정 필요',
    },
  ],
};
