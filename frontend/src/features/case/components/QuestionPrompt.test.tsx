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

  it('checkbox_button: 일반 다중 선택은 확인 시 배열 value와 합친 label로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'claimed_policy_ids',
          question_text: '이미 청구한 보험을 골라주세요.',
          input_type: 'checkbox_button',
          options: [
            { value: 'policy-a', label: 'A 보험' },
            { value: 'policy-b', label: 'B 보험' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'A 보험' }));
    await userEvent.click(screen.getByRole('button', { name: 'B 보험' }));
    await userEvent.click(screen.getByRole('button', { name: '확인' }));

    expect(onAnswer).toHaveBeenCalledWith(
      'claimed_policy_ids',
      ['policy-a', 'policy-b'],
      'A 보험, B 보험'
    );
  });

  it('treatment_items: ui_group 선택 후 display_name 칩을 즉시 답변으로 보낸다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'treatment_items',
          question_text: '받으신 치료를 골라주세요.',
          input_type: 'checkbox_button',
          options: [
            { value: 'MRI_MRA', label: '영상검사 (MRI/CT)' },
            { value: 'OTHER', label: '기타 치료' },
          ],
          treatment_types: [
            {
              code: 'MRI_MRA',
              display_name: 'MRI/MRA',
              ui_group: '영상검사',
              active: true,
            },
            {
              code: 'CT',
              display_name: 'CT 검사',
              ui_group: '영상검사',
              active: true,
            },
            {
              code: 'CAST',
              display_name: '깁스',
              ui_group: '기타',
              active: true,
            },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '영상검사 (MRI/CT)' }));

    expect(screen.getByRole('button', { name: '영상검사 (MRI/CT)' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '확인' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'MRI/MRA' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'CT 검사' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'CT 검사' }));
    await userEvent.click(screen.getByRole('button', { name: '기타 치료' }));
    await userEvent.click(screen.getByRole('button', { name: '깁스' }));
    await userEvent.click(screen.getByRole('button', { name: '확인' }));

    expect(onAnswer).toHaveBeenCalledWith('treatment_items', ['CT 검사', '깁스'], 'CT 검사, 깁스');
  });

  it('treatment_items: 해당없음 선택 시 빈 배열을 즉시 답변으로 보낸다', async () => {
    const onAnswer = vi.fn();
    render(
      <QuestionPrompt
        question={{
          question_id: 'treatment_items',
          question_text: '이번 입원 중 함께 받은 치료가 있다면 골라주세요.',
          input_type: 'checkbox_button',
          options: [
            { value: 'MRI_MRA', label: '영상검사 (MRI/CT)' },
            { value: 'NONE', label: '해당없음' },
          ],
        }}
        onAnswer={onAnswer}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: '해당없음' }));

    expect(onAnswer).toHaveBeenCalledWith('treatment_items', [], '해당없음');
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

  it('file_upload: PDF와 이미지 파일을 선택하고 선택한 파일명을 표시한다', async () => {
    const onAnswer = vi.fn();
    const { container } = render(
      <QuestionPrompt
        question={{
          question_id: 'medical_detail_statement',
          question_text: '진료비 세부산정내역서 파일(PDF 또는 이미지)을 업로드해 주세요.',
          input_type: 'file_upload',
        }}
        onAnswer={onAnswer}
      />
    );

    const input = container.querySelector('input[type="file"]');

    expect(input).toHaveAttribute(
      'accept',
      'application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png'
    );
    expect(screen.getByText('선택된 이미지 없음')).toBeInTheDocument();
    expect(screen.getByText('이미지 선택')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '이미지 업로드' })).toBeInTheDocument();

    const file = new File(['image'], 'statement.png', { type: 'image/png' });
    await userEvent.upload(input as HTMLInputElement, file);

    expect(screen.getByText('statement.png')).toBeInTheDocument();
  });
});
