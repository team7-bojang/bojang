import { ChevronDown, ExternalLink, FileCheck2 } from 'lucide-react';
import { useState } from 'react';

import { Checkbox } from '@/components/ui/checkbox';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { type InsurerId } from '@/features/insurance/data/insurers';
import { cn } from '@/lib/utils';

interface ClaimInsurerLink {
  key: string;
  insurerId: InsurerId;
  name: string;
  url: string;
}

interface ClaimDocumentsSectionProps {
  policyNames: string[];
  className?: string;
}

const COMMON_CLAIM_DOCUMENTS = [
  '보험금청구서 (보험사 양식)',
  '보험금 청구를 위한 상세동의서 (보험사 양식)',
  '청구인 신분증 사본',
  '진단서 (질병분류코드 포함)',
  '진료비 영수증',
  '진료비 세부내역서',
] as const;

const CLAIM_LINKS = {
  kb: {
    key: 'kb',
    insurerId: 'kb',
    name: 'KB손해보험',
    url: 'https://www.kbinsure.co.kr/CG205020003.ec',
  },
  db: {
    key: 'db',
    insurerId: 'db',
    name: 'DB손해보험',
    url: 'https://www.idbins.com/pc/bizxpress/ct/dc/FWCUSV1301.shtm',
  },
  hyundai: {
    key: 'hyundai',
    insurerId: 'hyundai',
    name: '현대해상',
    url: 'https://www.hi.co.kr/serviceAction.do?menuId=100631',
  },
  meritz: {
    key: 'meritz',
    insurerId: 'meritz',
    name: '메리츠화재',
    url: 'https://msea.meritzfire.com/mblAtcDocGuid/mblAtcDocGuid.do#!/01',
  },
  hanwhaLife: {
    key: 'hanwhaLife',
    insurerId: 'hanwha',
    name: '한화생명',
    url: 'https://www.hanwhalife.com/static/main/myPage/insurance/accident/document/MY_INAPADC_T10000.jsp?network=g&device=c&keyword=%EB%B3%B4%ED%97%98%ED%95%9C%ED%99%94%EC%83%9D%EB%AA%85&creative=771565853684&gclid=CjwKCAjw3ejRBhAdEiwADkqPnxl_QEGyvNSSQE1HHTMy09Lr34rMeNyctUD-VyDYioE_K5wdSFuFixoC3PoQAvD_BwE&campaignid=22933903625&adgroupid=185883379673&matchtype=b&placement=&sourceid={sourceid}&gad_source=1&gad_campaignid=22933903625&gbraid=0AAAAABsaf4QKmCpbGOsuZBbUPwSD36krR&gclid=CjwKCAjw3ejRBhAdEiwADkqPnxl_QEGyvNSSQE1HHTMy09Lr34rMeNyctUD-VyDYioE_K5wdSFuFixoC3PoQAvD_BwE',
  },
  hanwhaGeneral: {
    key: 'hanwhaGeneral',
    insurerId: 'hanwha',
    name: '한화손해보험',
    url: 'https://www.hanwhalife.com/static/main/myPage/insurance/accident/document/MY_INAPADC_T10000.jsp?network=g&device=c&keyword=%EB%B3%B4%ED%97%98%ED%95%9C%ED%99%94%EC%83%9D%EB%AA%85&creative=771565853684&gclid=CjwKCAjw3ejRBhAdEiwADkqPnxl_QEGyvNSSQE1HHTMy09Lr34rMeNyctUD-VyDYioE_K5wdSFuFixoC3PoQAvD_BwE&campaignid=22933903625&adgroupid=185883379673&matchtype=b&placement=&sourceid={sourceid}&gad_source=1&gad_campaignid=22933903625&gbraid=0AAAAABsaf4QKmCpbGOsuZBbUPwSD36krR&gclid=CjwKCAjw3ejRBhAdEiwADkqPnxl_QEGyvNSSQE1HHTMy09Lr34rMeNyctUD-VyDYioE_K5wdSFuFixoC3PoQAvD_BwE',
  },
  kyobo: {
    key: 'kyobo',
    insurerId: 'kyobo',
    name: '교보생명',
    url: 'https://www.kyobo.com/dgt/web/customer/support/need-papers/list',
  },
} satisfies Record<string, ClaimInsurerLink>;

function inferClaimLink(policyName: string): ClaimInsurerLink | null {
  if (policyName.includes('KB')) {
    return CLAIM_LINKS.kb;
  }
  if (policyName.includes('DB')) {
    return CLAIM_LINKS.db;
  }
  if (policyName.includes('현대')) {
    return CLAIM_LINKS.hyundai;
  }
  if (policyName.includes('메리츠')) {
    return CLAIM_LINKS.meritz;
  }
  if (policyName.includes('한화손해')) {
    return CLAIM_LINKS.hanwhaGeneral;
  }
  if (policyName.includes('한화')) {
    return CLAIM_LINKS.hanwhaLife;
  }
  if (policyName.includes('교보')) {
    return CLAIM_LINKS.kyobo;
  }
  return null;
}

function getClaimLinks(policyNames: string[]) {
  const links = new Map<string, ClaimInsurerLink>();
  for (const policyName of policyNames) {
    const link = inferClaimLink(policyName);
    if (link) {
      links.set(link.key, link);
    }
  }
  return [...links.values()];
}

function toCheckedMap(documents: readonly string[]) {
  return Object.fromEntries(documents.map(document => [document, false]));
}

function ClaimDocumentChecklist({
  checkedDocuments,
  onToggle,
}: {
  checkedDocuments: Record<string, boolean>;
  onToggle: (document: string, checked: boolean | 'indeterminate') => void;
}) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {COMMON_CLAIM_DOCUMENTS.map(document => {
        const checked = checkedDocuments[document] ?? false;
        return (
          <li key={document}>
            <label
              className={cn(
                'flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border px-2.5 py-2 transition-colors',
                checked
                  ? 'border-primary/30 bg-primary-tint/50 text-primary'
                  : 'border-line bg-canvas/50 text-ink hover:border-primary/30 hover:bg-primary-tint/20'
              )}
            >
              <Checkbox
                checked={checked}
                onCheckedChange={value => onToggle(document, value)}
                aria-label={`${document} 준비 완료`}
                className="size-4 rounded"
              />
              <span
                className={cn(
                  'text-xs font-semibold leading-5 sm:text-sm',
                  checked && 'line-through decoration-primary/60'
                )}
              >
                {document}
              </span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}

function InsurerQuickLinks({ links }: { links: ClaimInsurerLink[] }) {
  return (
    <div className="mt-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-black text-ink">보험사 바로가기</h3>
        {links.length > 0 && <span className="text-xs font-bold text-muted">{links.length}곳</span>}
      </div>
      {links.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {links.map(link => (
            <a
              key={link.key}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-2 text-sm font-bold text-ink transition-colors hover:border-primary/40 hover:bg-primary-tint/30 hover:text-primary"
              title={`${link.name} 청구 서류 안내`}
              aria-label={`${link.name} 청구 서류 안내 페이지 열기`}
            >
              <InsurerLogo insurerId={link.insurerId} size="sm" className="rounded-full" />
              <span>{link.name}</span>
              <ExternalLink className="size-3.5" aria-hidden="true" />
            </a>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm font-semibold text-muted">
          연결할 보험사를 확인하지 못했습니다.
        </p>
      )}
    </div>
  );
}

export function ClaimDocumentsSection({ policyNames, className }: ClaimDocumentsSectionProps) {
  const [open, setOpen] = useState(false);
  const [checkedDocuments, setCheckedDocuments] = useState<Record<string, boolean>>(() =>
    toCheckedMap(COMMON_CLAIM_DOCUMENTS)
  );
  const insurerLinks = getClaimLinks(policyNames);
  const checkedCount = COMMON_CLAIM_DOCUMENTS.filter(document => checkedDocuments[document]).length;
  const progress = Math.round((checkedCount / COMMON_CLAIM_DOCUMENTS.length) * 100);

  if (policyNames.length === 0) {
    return null;
  }

  const toggleDocument = (document: string, checked: boolean | 'indeterminate') => {
    setCheckedDocuments(prev => ({ ...prev, [document]: checked === true }));
  };

  return (
    <section className={className}>
      <div className="overflow-hidden rounded-card bg-surface shadow-sm">
        <button
          type="button"
          className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left transition-colors hover:bg-canvas/50 sm:px-6"
          onClick={() => setOpen(prev => !prev)}
          aria-expanded={open}
        >
          <span className="min-w-0">
            <span className="flex items-center gap-2 text-lg font-extrabold text-ink">
              <FileCheck2 className="size-5 text-primary" aria-hidden="true" />
              청구 준비
            </span>
            <span className="mt-1 block text-xs font-semibold text-muted">
              {checkedCount} / {COMMON_CLAIM_DOCUMENTS.length} 준비 · 보험사 바로가기{' '}
              {insurerLinks.length}곳
            </span>
          </span>
          <ChevronDown
            className={cn('size-5 shrink-0 text-muted transition-transform', open && 'rotate-180')}
            aria-hidden="true"
          />
        </button>

        <div className="border-t border-line px-4 py-4 sm:px-6">
          <div className="h-1.5 overflow-hidden rounded-full bg-line/70">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>

          <InsurerQuickLinks links={insurerLinks} />

          {open && (
            <div className="mt-4 border-t border-line pt-4">
              <ClaimDocumentChecklist
                checkedDocuments={checkedDocuments}
                onToggle={toggleDocument}
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
