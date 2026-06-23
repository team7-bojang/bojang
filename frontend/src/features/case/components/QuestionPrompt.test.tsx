import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { QuestionPrompt } from './QuestionPrompt';

describe('QuestionPrompt', () => {
  it('radio_button: 옵션 칩 클릭 시 question_id/value/label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'surgery',
          question_text: '수술을 받으셨나요?',
          input_type: 'radio_button',
          options: [
            { value: true, label: '예' },
            { value: false, label: '아니요' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '예' }));

    expect(onAnswer).toHaveBeenCalledWith('surgery', true, '예');
  });

  it('select_button: disease_kcd가 아니면 일반 단일 선택 칩으로 처리한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'input_method',
          question_text: '자료 입력 방식을 선택해주세요.',
          input_type: 'select_button',
          options: [
            { value: 'PAYMENT', label: '문자·카드내역으로 빠르게 확인' },
            { value: 'MEDICAL_DETAIL_STATEMENT', label: '진료비 세부산정내역서로 자세히 확인' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    expect(screen.queryByRole('button', { name: '해당 병명이 없어요' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: '문자·카드내역으로 빠르게 확인' }));

    expect(onAnswer).toHaveBeenCalledWith(
      'input_method',
      'PAYMENT',
      '문자·카드내역으로 빠르게 확인'
    );
  });

  it('checkbox_button: 다중 선택 후 확인 시 배열 value와 합친 label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'treatment_items',
          question_text: '받으신 치료를 골라주세요.',
          input_type: 'checkbox_button',
          options: [
            { value: 'MRI_MRA', label: '영상검사' },
            { value: 'INJECTION', label: '주사치료' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '영상검사' }));
    await userEvent.click(screen.getByRole('button', { name: '주사치료' }));
    await userEvent.click(screen.getByRole('button', { name: '확인' }));

    expect(onAnswer).toHaveBeenCalledWith(
      'treatment_items',
      ['MRI_MRA', 'INJECTION'],
      '영상검사, 주사치료'
    );
  });

  it('text_input: 입력값을 trim해서 question_id/value/label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'annual_visit_count',
          question_text: '연간 통원 횟수를 입력해주세요.',
          input_type: 'text_input',
          placeholder: '예: 3회',
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.type(screen.getByPlaceholderText('예: 3회'), ' 3회 ');
    await userEvent.click(screen.getByRole('button', { name: '전송' }));

    expect(onAnswer).toHaveBeenCalledWith('annual_visit_count', '3회', '3회');
  });
});
