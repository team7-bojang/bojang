import { useCallback, useRef, useState } from 'react';

import type { AnswerValue, NextQuestion } from './model';
import { answerCase, startCaseAnalysis } from './queries';

export interface ChatMessage {
  role: 'bot' | 'user';
  text: string;
}

// 백엔드 응답 JSON 형태를 반영(snake_case)
interface ApplyTarget {
  next_question?: NextQuestion | null;
  message?: string | null;
}

interface UseChatFlowParams {
  selectedPolicyIds: string[];
  onCaseCreated?: (caseId: string, selectedPolicyIds: string[]) => void;
  onDone?: (caseId: string) => void;
}

const DONE_MESSAGE = '필요한 정보를 모두 확인했어요. 분석을 준비할게요.';

export function useChatFlow({ selectedPolicyIds, onCaseCreated, onDone }: UseChatFlowParams) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  // setState 비동기 배치로 인한 빠른 중복 제출을 막기 위한 동기 가드.
  const submittingRef = useRef(false);

  const pushMessage = useCallback(
    (role: ChatMessage['role'], text: string) => setMessages(prev => [...prev, { role, text }]),
    []
  );

  const applyResponse = useCallback(
    (res: ApplyTarget, resolvedCaseId: string) => {
      const next = res.next_question ?? null;
      if (next) {
        pushMessage('bot', next.question_text);
        setPendingQuestion(next);
        return;
      }
      pushMessage('bot', res.message ?? DONE_MESSAGE);
      setPendingQuestion(null);
      setDone(true);
      onDone?.(resolvedCaseId);
    },
    [onDone, pushMessage]
  );

  const start = useCallback(
    async (situation: string) => {
      const value = situation.trim();
      if (!value || caseId || submittingRef.current) {
        return;
      }
      submittingRef.current = true;
      pushMessage('user', value);
      setError(null);
      setSubmitting(true);
      try {
        const res = await startCaseAnalysis({
          service_type: 'CASE1',
          policy_ids: selectedPolicyIds,
          initial_situation: value,
        });
        if (!res.case_id) {
          setError(res.message ?? '분석 가능한 케이스를 만들지 못했습니다.');
          return;
        }
        setCaseId(res.case_id);
        onCaseCreated?.(res.case_id, selectedPolicyIds);
        applyResponse(res, res.case_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : '분석 세션을 시작하지 못했습니다.');
      } finally {
        submittingRef.current = false;
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, onCaseCreated, pushMessage, selectedPolicyIds]
  );

  const answer = useCallback(
    async (questionId: string, value: AnswerValue, label: string) => {
      if (!caseId || submittingRef.current) {
        return;
      }
      submittingRef.current = true;
      pushMessage('user', label);
      setError(null);
      setSubmitting(true);
      try {
        const res = await answerCase(caseId, { answers: [{ question_id: questionId, value }] });
        applyResponse(res, caseId);
      } catch (err) {
        setError(err instanceof Error ? err.message : '답변을 저장하지 못했습니다.');
      } finally {
        submittingRef.current = false;
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, pushMessage]
  );

  return { messages, caseId, pendingQuestion, submitting, error, done, start, answer };
}
