type PromiseSettledResultLike = {
  status: 'fulfilled' | 'rejected';
  reason?: unknown;
};

export function getParseRiderFailureMessage(results: PromiseSettledResultLike[]) {
  if (results.every(result => result.status === 'fulfilled')) {
    return null;
  }

  return '일부 약관 파싱에 실패했습니다. 분석은 계속 진행되지만, 특약 정보가 비어 있을 수 있습니다.';
}
