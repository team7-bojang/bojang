export function getAuthErrorMessage(message: string) {
  const normalized = message.toLowerCase();

  if (normalized.includes('email rate limit exceeded')) {
    return '확인 이메일 요청이 너무 많습니다. 잠시 후 다시 시도하거나 다른 이메일을 사용해 주세요.';
  }

  if (normalized.includes('invalid login credentials')) {
    return '이메일 또는 비밀번호가 올바르지 않습니다.';
  }

  if (normalized.includes('already registered')) {
    return '이미 가입된 이메일입니다. 로그인으로 진행해 주세요.';
  }

  return message;
}
