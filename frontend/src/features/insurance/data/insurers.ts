import kbLogo from '@/assets/logo/kb.svg';
import dbLogo from '@/assets/logo/db.svg';
import hyundaiLogo from '@/assets/logo/hyundai.svg';
import meritzLogo from '@/assets/logo/meritz.svg';
import hanwhaLogo from '@/assets/logo/hanwha.svg';
import kyoboLogo from '@/assets/logo/kyobo.svg';

/** 보험사 식별자 (assets/logo 파일명과 1:1). */
export type InsurerId = 'kb' | 'db' | 'hyundai' | 'meritz' | 'hanwha' | 'kyobo';

export interface Insurer {
  id: InsurerId;
  name: string;
  logo: string;
}

export const INSURERS: Record<InsurerId, Insurer> = {
  kb: { id: 'kb', name: 'KB손해보험', logo: kbLogo },
  db: { id: 'db', name: 'DB손해보험', logo: dbLogo },
  hyundai: { id: 'hyundai', name: '현대해상', logo: hyundaiLogo },
  meritz: { id: 'meritz', name: '메리츠화재', logo: meritzLogo },
  hanwha: { id: 'hanwha', name: '한화손해보험', logo: hanwhaLogo },
  kyobo: { id: 'kyobo', name: '교보생명', logo: kyoboLogo },
};

export const INSURER_LIST: Insurer[] = Object.values(INSURERS);
