import { describe, expect, it } from 'vitest';

import { getParseRiderFailureMessage } from './utils';

describe('getParseRiderFailureMessage', () => {
  it('파싱이 하나라도 실패하면 안내 메시지를 반환한다', () => {
    const results = [
      { status: 'fulfilled' as const, value: { ok: true } },
      { status: 'rejected' as const, reason: 'network error' },
    ];

    expect(getParseRiderFailureMessage(results)).toBe(
      '일부 약관 파싱에 실패했습니다. 분석은 계속 진행되지만, 특약 정보가 비어 있을 수 있습니다.'
    );
  });

  it('모든 파싱이 성공하면 null을 반환한다', () => {
    const results = [{ status: 'fulfilled' as const, value: { ok: true } }];

    expect(getParseRiderFailureMessage(results)).toBeNull();
  });
});
