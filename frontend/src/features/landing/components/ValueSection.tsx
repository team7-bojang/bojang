import { FileText, ShieldCheck, Sparkles } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface ValueItem {
  icon: LucideIcon;
  title: string;
  desc: string;
}

const VALUES: ValueItem[] = [
  {
    icon: FileText,
    title: '약관 원문 근거',
    desc: '분석 결과를 약관 원문과 함께 보여드려요. 근거 없는 추정은 하지 않습니다.',
  },
  {
    icon: ShieldCheck,
    title: 'AI 환각 방지',
    desc: '약관 원문 컨텍스트 안에서만 분석해, 사실과 다른 답을 막습니다.',
  },
  {
    icon: Sparkles,
    title: '무료 · 간편',
    desc: '보험을 고르거나 약관을 올리기만 하면, 놓친 보장을 바로 찾아드려요.',
  },
];

/** 3페이지: 서비스 핵심 가치 3가지. */
export function ValueSection() {
  return (
    <section className="bg-surface py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="text-center">
          <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">왜 보장체크인가요?</h2>
          <p className="mt-3 text-sm text-muted sm:text-base">
            믿을 수 있는 근거와 함께, 놓친 보장을 정확하게 찾아드립니다.
          </p>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          {VALUES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="flex flex-col gap-3 rounded-card bg-canvas/60 p-6 ring-1 ring-line"
            >
              <span className="flex size-11 items-center justify-center rounded-xl bg-primary-tint text-primary">
                <Icon className="size-5" />
              </span>
              <h3 className="text-lg font-bold text-ink">{title}</h3>
              <p className="text-sm leading-6 text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
