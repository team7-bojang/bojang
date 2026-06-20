import type { InsurerId } from './insurers';

export interface Policy {
  id: string;
  insurerId: InsurerId;
  /** 상품명. */
  name: string;
  /** 분류 태그 (예: 손해보험, 질병). */
  tags: string[];
}

/**
 * 등록된 보험 목록 (mock).
 * TODO: 백엔드 `/api/v1` 연동 시 이 상수를 API 응답으로 교체.
 */
export const POLICIES: Policy[] = [
  {
    id: 'kb-cancer-plus',
    insurerId: 'kb',
    name: 'KB 9회주는 암보험 Plus 무배당',
    tags: ['손해보험', '질병'],
  },
  {
    id: 'db-double-plus',
    insurerId: 'db',
    name: '백년친구 더블플러스 종합보험',
    tags: ['손해보험', '질병'],
  },
  {
    id: 'hyundai-silson',
    insurerId: 'hyundai',
    name: '현대해상 실손의료비보장보험',
    tags: ['손해보험', '실손'],
  },
  {
    id: 'meritz-injury',
    insurerId: 'meritz',
    name: '메리츠 상해안심보험',
    tags: ['손해보험', '상해'],
  },
  {
    id: 'hanwha-health',
    insurerId: 'hanwha',
    name: '한화 건강플러스 종합보험',
    tags: ['손해보험', '건강'],
  },
  {
    id: 'kyobo-lifelong',
    insurerId: 'kyobo',
    name: '교보 New 내생애맞춤건강',
    tags: ['생명보험', '입원'],
  },
];
