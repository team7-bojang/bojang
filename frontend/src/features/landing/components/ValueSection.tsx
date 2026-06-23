interface ValueItem {
  emoji: string;
  title: string;
  desc: string;
}

const VALUES: ValueItem[] = [
  {
    emoji: '📄',
    title: '약관 원문 근거',
    desc: '분석 결과를 약관 원문과 함께 보여드려요. 근거 없는 추정은 하지 않습니다.',
  },
  {
    emoji: '🛡️',
    title: 'AI 환각 방지',
    desc: '약관 원문 컨텍스트 안에서만 분석해, 사실과 다른 답을 막습니다.',
  },
  {
    emoji: '✨',
    title: '무료 · 간편',
    desc: '보험을 고르거나 약관을 올리기만 하면, 놓친 보장을 바로 찾아드려요.',
  },
];

/** 3페이지: 서비스 핵심 가치 3가지 (대비를 위한 어두운 마무리 섹션). */
export function ValueSection() {
  return (
    <section className="flex min-h-screen flex-col justify-center bg-linear-to-b from-ink to-[#0a3f3a] py-20 text-white sm:py-24">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="text-center">
          <span className="inline-flex w-fit items-center rounded-full bg-primary-soft/15 px-3 py-1 text-xs font-semibold text-primary-soft">
            WHY 보장체크
          </span>
          <h2 className="mt-4 text-3xl font-extrabold sm:text-4xl">왜 보장체크인가요?</h2>
          <p className="mt-4 text-base text-white/65 sm:text-lg">
            믿을 수 있는 근거와 함께, 놓친 보장을 정확하게 찾아드립니다.
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {VALUES.map(({ emoji, title, desc }) => (
            <div
              key={title}
              className="flex flex-col gap-4 rounded-card bg-white/4 p-8 ring-1 ring-white/10 transition-colors hover:bg-white/8"
            >
              <span className="font-tossface flex size-12 items-center justify-center rounded-xl bg-white/10 text-2xl">
                {emoji}
              </span>
              <h3 className="text-xl font-bold text-white">{title}</h3>
              <p className="text-sm leading-7 text-white/65">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
