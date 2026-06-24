import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import type { NextQuestion } from '../model';
import { DiseasePicker } from './DiseasePicker';

function makeQuestion(count: number): NextQuestion {
  return {
    question_id: 'disease_kcd',
    question_text: '가장 가까운 질병을 골라주세요.',
    input_type: 'select_button',
    options: Array.from({ length: count }, (_, i) => ({
      kcd: `K${i}`,
      name: `질병${i}`,
    })),
  };
}

describe('DiseasePicker', () => {
  it('첫 페이지에는 후보 5개와 "해당 병명이 없어요" 칩을 노출한다', () => {
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={vi.fn()} />);

    expect(screen.getByRole('button', { name: '질병0' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '질병4' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '질병5' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '해당 병명이 없어요' })).toBeInTheDocument();
  });

  it('후보 칩 클릭 시 disease_kcd + kcd/name으로 콜백한다', async () => {
    const onAnswer = vi.fn();
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={onAnswer} />);

    await userEvent.click(screen.getByRole('button', { name: '질병2' }));

    expect(onAnswer).toHaveBeenCalledWith('disease_kcd', 'K2', '질병2');
  });

  it('"해당 병명이 없어요"가 눌린 페이지에 다음 후보가 있으면 다음 5개로 이동한다', async () => {
    render(<DiseasePicker question={makeQuestion(12)} onAnswer={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));

    expect(screen.getByRole('button', { name: '질병5' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '질병9' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '질병0' })).not.toBeInTheDocument();
  });

  it('마지막 페이지에서 "해당 병명이 없어요"를 누르면 직접 입력으로 전환하고 disease_name으로 전송한다', async () => {
    const onAnswer = vi.fn();
    render(<DiseasePicker question={makeQuestion(7)} onAnswer={onAnswer} />);

    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));
    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));

    const input = screen.getByPlaceholderText('질병명을 직접 입력해주세요');
    await userEvent.type(input, '손목 터널 증상');
    await userEvent.click(screen.getByRole('button', { name: '전송' }));

    expect(onAnswer).toHaveBeenCalledWith('disease_name', '손목 터널 증상', '손목 터널 증상');
  });

  it('후보가 5개 이하면 "해당 병명이 없어요"가 바로 직접 입력으로 전환한다', async () => {
    render(<DiseasePicker question={makeQuestion(3)} onAnswer={vi.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: '해당 병명이 없어요' }));

    expect(screen.getByPlaceholderText('질병명을 직접 입력해주세요')).toBeInTheDocument();
  });
});
