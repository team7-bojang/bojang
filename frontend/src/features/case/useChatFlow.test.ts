import { act, renderHook, waitFor } from '@testing-library/react';

import * as queries from './queries';
import { useChatFlow } from './useChatFlow';

vi.mock('./queries');

const mockedStart = vi.mocked(queries.startCaseAnalysis);
const mockedAnswer = vi.mocked(queries.answerCase);
const mockedPayment = vi.mocked(queries.submitCasePayment);
const mockedMedical = vi.mocked(queries.submitMedicalDetailStatement);

const renderUseChatFlow = (params: Parameters<typeof useChatFlow>[0]) =>
  renderHook(() => useChatFlow(params));

const defaultParams = { serviceType: 'CASE1' as const, selectedPolicyIds: ['p1'] };

const diseaseQuestion = {
  question_id: 'disease_kcd',
  question_text: '가장 가까운 질병을 골라주세요.',
  input_type: 'select_button' as const,
  options: [{ kcd: 'G56', name: '손목터널증후군' }],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useChatFlow', () => {
  it('start: /cases 응답의 disease 후보 확인이 필요하면 프론트 질문을 만든다', async () => {
    mockedStart.mockResolvedValue({
      case_id: 'c1',
      disease_match_confidence: 'need_user_confirmation',
      disease_kcd_candidates: [
        { kcd: 'G56', name: '손목터널증후군' },
        { kcd: 'S60', name: '손목 타박상' },
      ],
      next_question: null,
    } as never);

    const { result } = renderUseChatFlow(defaultParams);

    await act(async () => {
      await result.current.start('계단에서 넘어져 손목이 저릿해요');
    });

    expect(mockedStart).toHaveBeenCalledWith({
      service_type: 'CASE1',
      policy_ids: ['p1'],
      initial_situation: '계단에서 넘어져 손목이 저릿해요',
    });
    expect(result.current.caseId).toBe('c1');
    expect(result.current.pendingQuestion).toMatchObject({
      question_id: 'disease_kcd',
      input_type: 'select_button',
      options: [
        { kcd: 'G56', name: '손목터널증후군' },
        { kcd: 'S60', name: '손목 타박상' },
      ],
    });
    expect(result.current.messages.at(-1)?.text).toContain('질병명을 골라주세요');
  });

  it('start: 명시적인 next_question이 오면 그대로 pendingQuestion으로 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);

    const { result } = renderUseChatFlow(defaultParams);

    await act(async () => {
      await result.current.start('손목이 아파요');
    });

    expect(result.current.pendingQuestion).toEqual(diseaseQuestion);
    expect(result.current.messages.at(-1)).toEqual({
      role: 'bot',
      text: '가장 가까운 질병을 골라주세요.',
    });
  });

  it('answer: disease 후보 선택 시 question_id/value를 전송하고 다음 질문으로 이어간다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    const surgeryQuestion = {
      question_id: 'surgery',
      question_text: '수술을 받으셨나요?',
      input_type: 'radio_button' as const,
      options: [{ value: true, label: '예' }],
    };
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: surgeryQuestion } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });

    expect(mockedAnswer).toHaveBeenCalledWith('c1', {
      answers: [{ question_id: 'disease_kcd', value: 'G56' }],
    });
    expect(result.current.pendingQuestion).toEqual(surgeryQuestion);
  });

  it('answer: 질병 선택 후 다음 질문이 없으면 자료 제출 방식 선택으로 이어간다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: null } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });

    expect(result.current.pendingQuestion).toMatchObject({
      question_id: 'input_method',
      input_type: 'radio_button',
    });
  });

  it('answer: 자료 제출 방식 선택은 사용자 메시지나 API 요청을 만들지 않고 입력 단계만 바꾼다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: null } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });
    const beforeSelectMessages = result.current.messages;

    await act(async () => {
      await result.current.answer('input_method', 'PAYMENT', '문자·카드내역으로 빠르게 확인');
    });

    expect(mockedAnswer).toHaveBeenCalledTimes(1);
    expect(mockedPayment).not.toHaveBeenCalled();
    expect(mockedMedical).not.toHaveBeenCalled();
    expect(result.current.messages.filter(message => message.role === 'user')).toEqual(
      beforeSelectMessages.filter(message => message.role === 'user')
    );
    expect(result.current.pendingQuestion).toMatchObject({
      question_id: 'payment_text',
      input_type: 'text_input',
    });
  });

  it('answer: 결제 텍스트를 payment API로 전송하고 다음 질문으로 이어간다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: null } as never);
    const surgeryQuestion = {
      question_id: 'surgery',
      question_text: '이번 진료에서 수술도 받으셨나요?',
      input_type: 'radio_button' as const,
      options: [
        { value: true, label: '예' },
        { value: false, label: '아니요' },
      ],
    };
    mockedPayment.mockResolvedValue({ case_id: 'c1', next_question: surgeryQuestion } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });
    await act(async () => {
      await result.current.answer('input_method', 'PAYMENT', '문자·카드내역으로 빠르게 확인');
    });
    await act(async () => {
      await result.current.answer(
        'payment_text',
        'OO정형외과 2026.06.10 결제금액 80,000원',
        'OO정형외과 2026.06.10 결제금액 80,000원'
      );
    });

    expect(mockedPayment).toHaveBeenCalledWith('c1', {
      payment_text: 'OO정형외과 2026.06.10 결제금액 80,000원',
    });
    expect(result.current.pendingQuestion).toEqual(surgeryQuestion);
  });

  it('answer: PDF 파일을 업로드 API로 전송한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: null } as never);
    mockedMedical.mockResolvedValue({ next_question: null } as never);
    const file = new File(['pdf'], 'statement.pdf', { type: 'application/pdf' });

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });
    await act(async () => {
      await result.current.answer(
        'input_method',
        'MEDICAL_DETAIL_STATEMENT',
        '진료비 세부산정내역서로 자세히 확인'
      );
    });
    await act(async () => {
      await result.current.answer('medical_detail_statement', file, file.name);
    });

    expect(mockedMedical).toHaveBeenCalledWith('c1', file);
    expect(result.current.done).toBe(true);
  });

  it('start: 질병 확인이 끝난 상태에서 next_question이 없으면 자료 제출 방식 선택으로 이어간다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: null } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });

    expect(result.current.done).toBe(false);
    expect(result.current.pendingQuestion).toMatchObject({
      question_id: 'input_method',
      input_type: 'radio_button',
    });
  });

  it('후속 질문 응답 후 next_question이 null이면 done=true가 되고 onDone을 호출한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    const surgeryQuestion = {
      question_id: 'surgery',
      question_text: '수술을 받으셨나요?',
      input_type: 'radio_button' as const,
      options: [{ value: true, label: '예' }],
    };
    mockedAnswer
      .mockResolvedValueOnce({ case_id: 'c1', next_question: surgeryQuestion } as never)
      .mockResolvedValueOnce({ case_id: 'c1', next_question: null } as never);
    const onDone = vi.fn();

    const { result } = renderUseChatFlow({ ...defaultParams, onDone });
    await act(async () => {
      await result.current.start('손목');
    });
    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });
    await act(async () => {
      await result.current.answer('surgery', true, '예');
    });

    await waitFor(() => expect(result.current.done).toBe(true));
    expect(result.current.pendingQuestion).toBeNull();
    expect(onDone).toHaveBeenCalledWith('c1');
  });

  it('start 실패(case_id 없음) 시 error를 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: null, message: '실패' } as never);

    const { result } = renderUseChatFlow(defaultParams);
    await act(async () => {
      await result.current.start('손목');
    });

    expect(result.current.error).toBe('실패');
    expect(result.current.caseId).toBeNull();
  });

  it('answer: caseId 없이 호출하면 아무 요청도 보내지 않는다', async () => {
    const { result } = renderUseChatFlow(defaultParams);

    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });

    expect(mockedAnswer).not.toHaveBeenCalled();
  });

  it('start: 공백 입력이면 요청을 보내지 않는다', async () => {
    const { result } = renderUseChatFlow(defaultParams);

    await act(async () => {
      await result.current.start('   ');
    });

    expect(mockedStart).not.toHaveBeenCalled();
  });
});
