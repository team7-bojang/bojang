import { useEffect, useState } from 'react';

import hanwhaAd from '@/assets/advertisement/한화광고.png';
import hyundaiAd from '@/assets/advertisement/현대해상.png';
import kbAd from '@/assets/advertisement/kb손해보험.png';

const advertisements = [
  {
    src: kbAd,
    alt: 'KB손해보험 광고',
    message: '실손 보장은 급여 본인부담금과 비급여 금액을 나누어 확인하면 더 정확해요.',
  },
  {
    src: hanwhaAd,
    alt: '한화손해보험 광고',
    message: '입원일당은 입원 일수와 약관의 지급 제한 일수를 함께 확인해야 해요.',
  },
  {
    src: hyundaiAd,
    alt: '현대해상 광고',
    message: '진단비는 질병코드와 약관의 보장 범위가 맞는지 확인하는 것이 중요해요.',
  },
] as const;

const ROTATION_INTERVAL_MS = 3_000;

/** 분석 대기 중 시간대별로 보험 광고 이미지를 보여준다. */
export function AdvertisementRotator() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setActiveIndex(current => (current + 1) % advertisements.length);
    }, ROTATION_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  const advertisement = advertisements[activeIndex];

  return (
    <div className="space-y-3">
      <div className="flex aspect-video w-full items-center justify-center overflow-hidden rounded-card bg-white">
        <img
          src={advertisement.src}
          alt={advertisement.alt}
          className="h-full w-full object-contain"
        />
      </div>
      <p className="text-center text-sm font-semibold leading-6 text-ink">
        <span className="mr-2 rounded-full bg-primary-tint px-2 py-0.5 text-xs font-bold text-primary">
          보험 정보
        </span>
        {advertisement.message}
      </p>
    </div>
  );
}
