import { normalizeOptions } from './options';

describe('normalizeOptions', () => {
  it('질병 {kcd,name} 옵션을 {value,label}로 변환한다', () => {
    const result = normalizeOptions([
      { kcd: 'G56', name: '손목터널증후군' },
      { kcd: 'S60', name: '손목 타박상' },
    ]);

    expect(result).toEqual([
      { value: 'G56', label: '손목터널증후군' },
      { value: 'S60', label: '손목 타박상' },
    ]);
  });

  it('{value,label} 옵션은 그대로 두고 boolean value를 보존한다', () => {
    const result = normalizeOptions([
      { value: true, label: '예' },
      { value: false, label: '아니오' },
    ]);

    expect(result).toEqual([
      { value: true, label: '예' },
      { value: false, label: '아니오' },
    ]);
  });

  it('options가 없으면 빈 배열을 반환한다', () => {
    expect(normalizeOptions()).toEqual([]);
    expect(normalizeOptions(undefined)).toEqual([]);
  });
});
