import { act, renderHook, waitFor } from '@testing-library/react';

import * as queries from './queries';
import { useChatFlow } from './useChatFlow';

vi.mock('./queries');

const mockedStart = vi.mocked(queries.startCaseAnalysis);
const mockedAnswer = vi.mocked(queries.answerCase);

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
  it('start: /cases 응답의 next_question을 pendingQuestion으로 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));

    await act(async () => {
      await result.current.start('계단에서 넘어져 손목을 다쳤어요');
    });

    expect(mockedStart).toHaveBeenCalledWith({
      service_type: 'CASE1',
      policy_ids: ['p1'],
      initial_situation: '계단에서 넘어져 손목을 다쳤어요',
    });
    expect(result.current.caseId).toBe('c1');
    expect(result.current.pendingQuestion).toEqual(diseaseQuestion);
    expect(result.current.messages.at(-1)).toEqual({
      role: 'bot',
      text: '가장 가까운 질병을 골라주세요.',
    });
  });

  it('answer: question_id/value를 전송하고 다음 next_question으로 전이한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: diseaseQuestion } as never);
    const surgeryQuestion = {
      question_id: 'surgery',
      question_text: '수술도 받으셨나요?',
      input_type: 'radio_button' as const,
      options: [{ value: true, label: '예' }],
    };
    mockedAnswer.mockResolvedValue({ case_id: 'c1', next_question: surgeryQuestion } as never);

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));
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

  it('next_question이 null이면 done=true가 되고 onDone을 호출한다', async () => {
    mockedStart.mockResolvedValue({ case_id: 'c1', next_question: null } as never);
    const onDone = vi.fn();

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'], onDone }));
    await act(async () => {
      await result.current.start('손목');
    });

    await waitFor(() => expect(result.current.done).toBe(true));
    expect(result.current.pendingQuestion).toBeNull();
    expect(onDone).toHaveBeenCalledWith('c1');
  });

  it('start 실패(case_id 없음) 시 error를 세팅한다', async () => {
    mockedStart.mockResolvedValue({ case_id: null, message: '실패' } as never);

    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));
    await act(async () => {
      await result.current.start('손목');
    });

    expect(result.current.error).toBe('실패');
    expect(result.current.caseId).toBeNull();
  });

  it('answer: caseId 없이 호출하면 아무 요청도 보내지 않는다', async () => {
    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));

    await act(async () => {
      await result.current.answer('disease_kcd', 'G56', '손목터널증후군');
    });

    expect(mockedAnswer).not.toHaveBeenCalled();
  });

  it('start: 공백 입력이면 요청을 보내지 않는다', async () => {
    const { result } = renderHook(() => useChatFlow({ selectedPolicyIds: ['p1'] }));

    await act(async () => {
      await result.current.start('   ');
    });

    expect(mockedStart).not.toHaveBeenCalled();
  });
});
