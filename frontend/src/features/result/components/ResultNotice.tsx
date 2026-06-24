import { Button } from '@/components/ui/button';
import type { ServiceType } from '@/types/case';

interface ResultNoticeProps {
  notice?: string | null;
  serviceType: ServiceType;
}

export function ResultNotice({ notice, serviceType }: ResultNoticeProps) {
  const fallback =
    serviceType === 'CASE2'
      ? '비교 결과는 현재 입력한 입원 일수와 목표 일수를 기준으로 계산한 예상 결과입니다. 실제 지급 여부는 보험사 심사에 따라 달라질 수 있습니다.'
      : '분석 결과는 입력하신 내용과 약관 근거를 바탕으로 한 예상 결과입니다. 실제 보험금 지급 여부는 보험사 심사에 따라 달라질 수 있습니다.';

  return (
    <section className="mt-10 flex flex-col gap-4 rounded-card bg-surface/85 p-5 ring-1 ring-line sm:flex-row sm:items-center sm:justify-between">
      <p className="flex gap-3 text-sm leading-6 text-muted">
        <span className="font-tossface mt-0.5 shrink-0 text-lg">💬</span>
        <span>{notice ?? fallback}</span>
      </p>
      <Button type="button" variant="outline" size="lg" className="shrink-0">
        <span className="font-tossface">📄</span>
        분석 결과 리포트 다운로드
      </Button>
    </section>
  );
}
