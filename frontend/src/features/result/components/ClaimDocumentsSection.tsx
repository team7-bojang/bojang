import { ChevronDown, ExternalLink, FileCheck2 } from 'lucide-react';
import { useState } from 'react';

import { Checkbox } from '@/components/ui/checkbox';
import { InsurerLogo } from '@/features/insurance/components/InsurerLogo';
import { INSURERS, type InsurerId } from '@/features/insurance/data/insurers';
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
  variant?: 'card' | 'inline' | 'accordion' | 'summary';
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
    url: 'https://www.kbinsure.co.kr/',
  },
  db: {
    key: 'db',
    insurerId: 'db',
    name: 'DB손해보험',
    url: 'https://www.idbins.com/',
  },
  hyundai: {
    key: 'hyundai',
    insurerId: 'hyundai',
    name: '현대해상',
    url: 'https://www.hi.co.kr/',
  },
  meritz: {
    key: 'meritz',
    insurerId: 'meritz',
    name: '메리츠화재',
    url: 'https://www.meritzfire.com/',
  },
  hanwhaLife: {
    key: 'hanwhaLife',
    insurerId: 'hanwha',
    name: '한화생명',
    url: 'https://www.hanwhalife.com/',
  },
  hanwhaGeneral: {
    key: 'hanwhaGeneral',
    insurerId: 'hanwha',
    name: '한화손해보험',
    url: 'https://www.hwgeneralins.com/',
  },
  kyobo: {
    key: 'kyobo',
    insurerId: 'kyobo',
    name: '교보생명',
    url: 'https://www.kyobo.com/',
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

export function ClaimDocumentsSection({
  policyNames,
  className,
  variant = 'card',
}: ClaimDocumentsSectionProps) {
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

  const documentItems = (size: 'compact' | 'regular') => (
    <ul
      className={cn(
        size === 'regular'
          ? 'grid gap-2 sm:grid-cols-2 lg:grid-cols-3'
          : 'grid gap-2 sm:grid-cols-2 lg:grid-cols-3'
      )}
    >
      {COMMON_CLAIM_DOCUMENTS.map(document => {
        const checked = checkedDocuments[document] ?? false;
        return (
          <li key={document}>
            <label
              className={cn(
                'flex cursor-pointer items-center gap-3 rounded-xl border transition-colors',
                checked
                  ? 'border-primary/30 bg-primary-tint/50 text-primary'
                  : 'border-line bg-canvas/50 text-ink hover:border-primary/30 hover:bg-primary-tint/20',
                size === 'regular' ? 'min-h-12 px-3 py-2' : 'min-h-11 px-2.5 py-2'
              )}
            >
              <Checkbox
                checked={checked}
                onCheckedChange={value => toggleDocument(document, value)}
                aria-label={`${document} 준비 완료`}
                className={size === 'regular' ? 'size-5' : 'size-4 rounded'}
              />
              <span
                className={cn(
                  'font-semibold leading-5',
                  'text-xs sm:text-sm',
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

  const insurerLinksContent = (size: 'compact' | 'regular') => {
    if (insurerLinks.length === 0) {
      return null;
    }

    return (
      <div className={cn(size === 'regular' ? 'mt-6' : 'mt-4 border-t border-line pt-4')}>
        <div className="flex items-center justify-between gap-3">
          <h3 className={cn('font-black text-ink', size === 'regular' ? 'text-sm' : 'text-xs')}>
            보험사별 상세 안내
          </h3>
          {size === 'compact' && (
            <span className="text-[11px] font-semibold text-muted">새 탭</span>
          )}
        </div>
        <div className={cn('mt-3 flex flex-wrap', size === 'regular' ? 'gap-3' : 'gap-2')}>
          {insurerLinks.map(link => (
            <a
              key={link.key}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className={cn(
                'group border border-line bg-surface transition-colors hover:border-primary/40 hover:bg-primary-tint/30',
                size === 'regular'
                  ? 'flex items-center gap-3 rounded-xl px-3 py-2.5'
                  : 'relative rounded-full p-0.5'
              )}
              title={`${link.name} 청구 서류 안내`}
              aria-label={`${link.name} 청구 서류 안내 페이지 열기`}
            >
              <span className="relative">
                <InsurerLogo
                  insurerId={link.insurerId}
                  size={size === 'regular' ? 'md' : 'sm'}
                  className="rounded-full"
                />
                <span
                  className={cn(
                    'absolute -bottom-1 -right-1 flex items-center justify-center rounded-full border border-line bg-primary text-surface shadow-sm',
                    size === 'regular' ? 'size-5' : 'size-4'
                  )}
                >
                  <ExternalLink
                    className={size === 'regular' ? 'size-3' : 'size-2.5'}
                    aria-hidden="true"
                  />
                </span>
              </span>
              {size === 'regular' && (
                <span className="pr-1 text-sm font-bold text-ink group-hover:text-primary">
                  {link.name || INSURERS[link.insurerId].name}
                </span>
              )}
            </a>
          ))}
        </div>
      </div>
    );
  };

  if (variant === 'inline') {
    return (
      <section className={className}>
        <div className="overflow-hidden rounded-card bg-surface shadow-sm ring-1 ring-line">
          <div className="grid gap-4 p-4 lg:grid-cols-[12rem_minmax(0,1fr)_auto] lg:items-center">
            <div>
              <span className="flex size-10 items-center justify-center rounded-full bg-primary-tint text-primary">
                <FileCheck2 className="size-4.5" aria-hidden="true" />
              </span>
              <h2 className="mt-3 text-base font-black text-ink">청구 서류 준비</h2>
              <p className="mt-1 text-xs font-semibold text-muted">
                {checkedCount}/{COMMON_CLAIM_DOCUMENTS.length} 완료
              </p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line/70">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <div className="min-w-0">{documentItems('compact')}</div>

            {insurerLinks.length > 0 && (
              <div className="border-t border-line pt-4 lg:border-l lg:border-t-0 lg:py-1 lg:pl-4">
                <p className="text-xs font-black text-ink">상세 안내</p>
                <div className="mt-3 flex flex-wrap gap-2 lg:max-w-28">
                  {insurerLinks.map(link => (
                    <a
                      key={link.key}
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="group relative rounded-full p-0.5"
                      title={`${link.name} 청구 서류 안내`}
                      aria-label={`${link.name} 청구 서류 안내 페이지 열기`}
                    >
                      <InsurerLogo insurerId={link.insurerId} size="sm" className="rounded-full" />
                      <span className="absolute -bottom-1 -right-1 flex size-4 items-center justify-center rounded-full border border-line bg-primary text-surface shadow-sm">
                        <ExternalLink className="size-2.5" aria-hidden="true" />
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  }

  if (variant === 'accordion') {
    return (
      <section className={className}>
        <div className="rounded-card bg-surface shadow-sm">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left"
            onClick={() => setOpen(prev => !prev)}
            aria-expanded={open}
          >
            <span className="flex min-w-0 items-center gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
                <FileCheck2 className="size-4.5" aria-hidden="true" />
              </span>
              <span className="min-w-0">
                <span className="block text-base font-black text-ink">청구 서류 안내</span>
                <span className="block truncate text-xs font-semibold text-muted">
                  {checkedCount}/{COMMON_CLAIM_DOCUMENTS.length} 준비 완료 · 보험사{' '}
                  {insurerLinks.length}곳
                </span>
              </span>
            </span>
            <ChevronDown
              className={`size-5 shrink-0 text-muted transition-transform ${open ? 'rotate-180' : ''}`}
              aria-hidden="true"
            />
          </button>

          {open && (
            <div className="border-t border-line px-4 pb-4 pt-3">
              {documentItems('compact')}
              {insurerLinksContent('regular')}
            </div>
          )}
        </div>
      </section>
    );
  }

  if (variant === 'summary') {
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
              className={`size-5 shrink-0 text-muted transition-transform ${open ? 'rotate-180' : ''}`}
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

            <div className="mt-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-black text-ink">보험사 바로가기</h3>
                {insurerLinks.length > 0 && (
                  <span className="text-xs font-bold text-muted">{insurerLinks.length}곳</span>
                )}
              </div>
              {insurerLinks.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {insurerLinks.map(link => (
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
                      <span>{link.name || INSURERS[link.insurerId].name}</span>
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

            {open && (
              <div className="mt-4 border-t border-line pt-4">{documentItems('compact')}</div>
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={className}>
      <div className="rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6">
        <div className="flex items-start gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary-tint text-primary">
            <FileCheck2 className="size-5" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h2 className="text-xl font-black text-ink">청구 서류 안내</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              공통 서류를 먼저 준비하고, 질병 종류와 청구 금액에 따라 달라지는 추가 서류는 보험사
              안내 페이지에서 확인해 주세요.
            </p>
          </div>
        </div>

        <div className="mt-5">
          <h3 className="text-sm font-black text-ink">공통 준비 서류</h3>
          <div className="mt-3">{documentItems('regular')}</div>
        </div>

        {insurerLinksContent('regular')}
      </div>
    </section>
  );
}
