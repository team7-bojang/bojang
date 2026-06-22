import { ScenarioCard } from '@/features/landing/components/ScenarioCard';
import { SCENARIOS } from '@/features/landing/data/scenarios';

/** 2페이지: 질문형 시나리오 무한 마퀴. */
export function ScenarioSection() {
  // 끊김 없는 루프를 위해 목록을 2배로 복제 (translateX(-50%) 기준).
  const loop = [...SCENARIOS, ...SCENARIOS];

  return (
    <section className="bg-canvas py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 text-center sm:px-8">
        <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">
          이런 상황, <span className="text-primary">청구 가능할까요?</span>
        </h2>
        <p className="mt-3 text-sm text-muted sm:text-base">
          실제로 많이 묻는 상황들이에요. 내 경우도 청구할 수 있는지 확인해보세요.
        </p>
      </div>

      {/* 복제된 마퀴는 장식용이므로 스크린리더에서 숨긴다 (질문 중복 낭독 방지). */}
      <div className="group mt-10 overflow-hidden" aria-hidden="true">
        {/* 간격은 카드별 우측 마진(mr-5)으로 줘서 translateX(-50%)가 정확히 한 세트와 일치하게 한다. */}
        <div className="animate-marquee flex w-max group-hover:[animation-play-state:paused]">
          {loop.map((scenario, index) => (
            <ScenarioCard key={`${scenario.id}-${index}`} scenario={scenario} />
          ))}
        </div>
      </div>
    </section>
  );
}
