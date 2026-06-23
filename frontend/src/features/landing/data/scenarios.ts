/** 랜딩 2페이지 마퀴에 노출할 질문형 시나리오. (정적 마케팅 데이터) */
export interface Scenario {
  id: string;
  /** 사용자 상황/질문 한 줄. */
  question: string;
  /** 카드 보조 태그(질병/상황 분류). */
  tag: string;
  /** 상황을 상징하는 이모지 (Tossface 폰트로 렌더). */
  emoji: string;
}

export const SCENARIOS: Scenario[] = [
  { id: 'disc', question: '허리디스크로 입원했어요. 청구가 가능할까요?', tag: '입원', emoji: '🦴' },
  { id: 'fracture', question: '계단에서 넘어져 골절됐는데 보장되나요?', tag: '상해', emoji: '🤕' },
  {
    id: 'cancer',
    question: '갑상선암 진단을 받았어요. 받을 수 있는 보험금이 있을까요?',
    tag: '진단',
    emoji: '🎗️',
  },
  { id: 'surgery', question: '백내장 수술을 했는데 청구할 수 있나요?', tag: '수술', emoji: '👁️' },
  {
    id: 'childbirth',
    question: '제왕절개로 출산했어요. 특약으로 보장되나요?',
    tag: '출산',
    emoji: '👶',
  },
  { id: 'pet', question: '반려견 치료비도 청구 대상이 되나요?', tag: '특약', emoji: '🐶' },
  {
    id: 'dental',
    question: '임플란트 치료, 놓친 치아 보장이 있는지 궁금해요.',
    tag: '치과',
    emoji: '🦷',
  },
  {
    id: 'mental',
    question: '공황장애로 통원 치료 중인데 청구 가능할까요?',
    tag: '통원',
    emoji: '🧠',
  },
];
