import { useCallback, useRef, useState } from 'react';

import type { TreatmentType } from '@/types/case';

import type { AnswerValue, CreateCaseResponse, NextQuestion, ServiceType } from '../model';
import {
  answerCase,
  startCaseAnalysis,
  submitCasePayment,
  submitMedicalDetailStatement,
} from '../queries';

export interface ChatMessage {
  role: 'bot' | 'user';
  text: string;
}

interface ApplyTarget {
  next_question?: NextQuestion | null;
  message?: string | null;
  treatment_types?: TreatmentType[] | null;
}

interface UseChatFlowParams {
  serviceType: ServiceType;
  selectedPolicyIds: string[];
  onCaseCreated?: (caseId: string, selectedPolicyIds: string[]) => void;
  onDone?: (caseId: string) => void;
}

const DONE_MESSAGE = '필요한 정보를 모두 확인했어요. 분석을 준비할게요.';
const DISEASE_CONFIRMATION_MESSAGE =
  '입력하신 상황과 가장 가까운 질병명을 골라주세요. 정확한 보장 판단을 위해 확인이 필요합니다.';

const INPUT_METHOD_QUESTION: NextQuestion = {
  question_id: 'input_method',
  question_text:
    '상황을 확인했어요. 분석을 진행할 자료의 입력 방식을 선택해 주세요.\n\n💳 문자나 카드내역만 있어도 빠르게 확인할 수 있어요.\n(대신 치료 내용이 부족하면 제가 짧게 몇 가지 더 여쭤볼게요)\n\n📄 진료비 세부산정내역서가 있다면 치료 항목을 직접 고르는 과정이 생략됩니다.',
  input_type: 'radio_button',
  options: [
    { value: 'PAYMENT', label: '문자·카드내역으로 빠르게 확인' },
    { value: 'MEDICAL_DETAIL_STATEMENT', label: '진료비 세부산정내역서로 자세히 확인' },
  ],
};

const PAYMENT_TEXT_QUESTION: NextQuestion = {
  question_id: 'payment_text',
  question_text: '결제 문자나 카드내역을 그대로 붙여넣어 주세요.',
  input_type: 'text_input',
  placeholder: '예: OO정형외과 2026.06.10 결제금액 80,000원',
};

const MEDICAL_DETAIL_STATEMENT_QUESTION: NextQuestion = {
  question_id: 'medical_detail_statement',
  question_text: '진료비 세부산정내역서 PDF를 업로드해 주세요.',
  input_type: 'file_upload',
};

function getDiseaseCandidates(res: CreateCaseResponse) {
  return res.disease_candidates?.length
    ? res.disease_candidates
    : (res.disease_kcd_candidates ?? []);
}

function buildDiseaseQuestion(res: CreateCaseResponse): NextQuestion | null {
  if (res.disease_match_confidence !== 'need_user_confirmation') {
    return null;
  }

  const options = getDiseaseCandidates(res)
    .map(candidate => ({
      kcd: candidate.kcd ?? candidate.code ?? '',
      name: candidate.friendly_name ?? candidate.name,
    }))
    .filter(candidate => candidate.kcd && candidate.name);

  if (options.length === 0) {
    return null;
  }

  return {
    question_id: 'disease_kcd',
    question_text: DISEASE_CONFIRMATION_MESSAGE,
    input_type: 'select_button',
    options,
  };
}

export function useChatFlow({
  serviceType,
  selectedPolicyIds,
  onCaseCreated,
  onDone,
}: UseChatFlowParams) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const submittingRef = useRef(false);

  const pushMessage = useCallback(
    (role: ChatMessage['role'], text: string) => setMessages(prev => [...prev, { role, text }]),
    []
  );

  const setQuestion = useCallback(
    (question: NextQuestion) => {
      pushMessage('bot', question.question_text);
      setPendingQuestion(question);
      setDone(false);
    },
    [pushMessage]
  );

  const finish = useCallback(
    (resolvedCaseId: string, message?: string | null) => {
      pushMessage('bot', message ?? DONE_MESSAGE);
      setPendingQuestion(null);
      setDone(true);
      onDone?.(resolvedCaseId);
    },
    [onDone, pushMessage]
  );

  const applyResponse = useCallback(
    (res: ApplyTarget, resolvedCaseId: string, fallbackToInputMethod = false) => {
      const next = res.next_question ?? null;
      if (next) {
        setQuestion({ ...next, treatment_types: res.treatment_types ?? next.treatment_types });
        return;
      }

      if (fallbackToInputMethod) {
        setQuestion(INPUT_METHOD_QUESTION);
        return;
      }

      finish(resolvedCaseId, res.message);
    },
    [finish, setQuestion]
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
      setDone(false);
      setSubmitting(true);

      try {
        const res = await startCaseAnalysis({
          service_type: serviceType,
          policy_ids: selectedPolicyIds,
          initial_situation: value,
        });

        if (!res.case_id) {
          setError(res.message ?? '분석 가능한 케이스를 만들지 못했습니다.');
          return;
        }

        setCaseId(res.case_id);
        onCaseCreated?.(res.case_id, selectedPolicyIds);

        const diseaseQuestion = buildDiseaseQuestion(res);
        if (diseaseQuestion) {
          setQuestion(diseaseQuestion);
          return;
        }

        applyResponse(res, res.case_id, true);
      } catch (err) {
        setError(err instanceof Error ? err.message : '분석 세션을 시작하지 못했습니다.');
      } finally {
        submittingRef.current = false;
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, onCaseCreated, pushMessage, selectedPolicyIds, serviceType, setQuestion]
  );

  const answer = useCallback(
    async (questionId: string, value: AnswerValue, label: string) => {
      if (!caseId || submittingRef.current) {
        return;
      }

      if (questionId === 'input_method') {
        setError(null);
        if (value === 'PAYMENT') {
          setQuestion(PAYMENT_TEXT_QUESTION);
          return;
        }
        if (value === 'MEDICAL_DETAIL_STATEMENT') {
          setQuestion(MEDICAL_DETAIL_STATEMENT_QUESTION);
          return;
        }
        setError('자료 입력 방식을 다시 선택해주세요.');
        return;
      }

      submittingRef.current = true;
      pushMessage('user', label);
      setError(null);
      setSubmitting(true);

      try {
        if (questionId === 'payment_text') {
          if (typeof value !== 'string') {
            setError('결제 내역 텍스트를 입력해주세요.');
            return;
          }
          const res = await submitCasePayment(caseId, { payment_text: value });
          applyResponse(res, caseId);
          return;
        }

        if (questionId === 'medical_detail_statement') {
          if (!(value instanceof File)) {
            setError('PDF 파일을 선택해주세요.');
            return;
          }
          const res = await submitMedicalDetailStatement(caseId, value);
          applyResponse(res, caseId);
          return;
        }

        const res = await answerCase(caseId, { answers: [{ question_id: questionId, value }] });
        applyResponse(res, caseId, questionId === 'disease_kcd' || questionId === 'disease_name');
      } catch (err) {
        setError(err instanceof Error ? err.message : '답변을 저장하지 못했습니다.');
      } finally {
        submittingRef.current = false;
        setSubmitting(false);
      }
    },
    [applyResponse, caseId, pushMessage, setQuestion]
  );

  return { messages, caseId, pendingQuestion, submitting, error, done, start, answer };
}
