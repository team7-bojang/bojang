import { ScenarioCard } from '@/features/landing/components/ScenarioCard';
import { SCENARIOS } from '@/features/landing/data/scenarios';

/** 2페이지: 질문형 시나리오 무한 마퀴 (1줄). */
export function ScenarioSection() {
  // 끊김 없는 루프를 위해 목록을 2배로 복제 (translateX(-50%) 기준).
  const loop = [...SCENARIOS, ...SCENARIOS];

  return (
    <section className="flex min-h-screen flex-col justify-center gap-12 bg-primary-tint/15 py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 text-center sm:px-8">
        <h2 className="text-3xl font-extrabold text-ink sm:text-4xl">
          이런 상황, <span className="text-primary">청구 가능할까요?</span>
        </h2>
        <p className="mt-4 text-base text-muted sm:text-lg">
          실제로 많이 묻는 상황들이에요. 내 경우도 청구할 수 있는지 확인해보세요.
        </p>
      </div>

      {/* 복제된 마퀴는 장식용이므로 스크린리더에서 숨긴다 (질문 중복 낭독 방지). */}
      {/* 양옆 페이드 마스크로 하드 컷 대신 자연스럽게 사라지게 한다. */}
      <div
        className="group mask-[linear-gradient(to_right,transparent,#000_6%,#000_94%,transparent)]"
        aria-hidden="true"
      >
        {/* py-3는 카드 그림자가 상하로 잘리지 않게 하는 여유. 간격은 카드별 우측 마진(mr-5). */}
        <div className="overflow-hidden py-3">
          <div className="animate-marquee flex w-max group-hover:[animation-play-state:paused]">
            {loop.map((scenario, index) => (
              <ScenarioCard key={`${scenario.id}-${index}`} scenario={scenario} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
