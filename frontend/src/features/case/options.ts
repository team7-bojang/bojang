import type { NormalizedOption, RawQuestionOption } from './model';

export function normalizeOptions(options: RawQuestionOption[] = []): NormalizedOption[] {
  return options.map(opt =>
    'kcd' in opt ? { value: opt.kcd, label: opt.name } : { value: opt.value, label: opt.label }
  );
}
