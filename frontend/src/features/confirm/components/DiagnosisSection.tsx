import { Search } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { DiseaseSearchResult } from '@/features/case/model';
import { searchDiseases } from '@/features/case/queries';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import type { CaseDashboard } from '@/types/case';
import { Field, NumberField } from './controls';

interface DiagnosisSectionProps {
  form: CaseDashboard;
  patch: (partial: Partial<CaseDashboard>) => void;
}

const HANGUL_JAMO_PATTERN = /[\u3131-\u318e\u1100-\u11ff]/;

/** 질병명 · 입/통원 · (입원 시) 입원 상세. */
export function DiagnosisSection({ form, patch }: DiagnosisSectionProps) {
  const inOut = form.is_inpatient ? 'inpatient' : form.is_outpatient ? 'outpatient' : '';
  const [diseaseResults, setDiseaseResults] = useState<DiseaseSearchResult[]>([]);
  const [diseaseSearchLoading, setDiseaseSearchLoading] = useState(false);
  const [diseaseSearchError, setDiseaseSearchError] = useState<string | null>(null);
  const [searchedDiseaseQuery, setSearchedDiseaseQuery] = useState('');
  const [diseaseSearchFocused, setDiseaseSearchFocused] = useState(false);
  const [searchText, setSearchText] = useState(form.disease_name);
  const [hasMoreDiseases, setHasMoreDiseases] = useState(false);
  const [nextDiseaseOffset, setNextDiseaseOffset] = useState(0);
  const [loadingMoreDiseases, setLoadingMoreDiseases] = useState(false);
  const diseaseQuery = searchText.trim();
  const hasIncompleteHangul = HANGUL_JAMO_PATTERN.test(diseaseQuery);
  const searchableDiseaseQuery =
    diseaseQuery.length >= 1 && !hasIncompleteHangul ? diseaseQuery : '';
  const debouncedDiseaseQuery = useDebouncedValue(searchableDiseaseQuery, 250);

  useEffect(() => {
    if (!debouncedDiseaseQuery) {
      return;
    }

    const controller = new AbortController();
    const timerId = window.setTimeout(() => {
      setDiseaseSearchLoading(true);
      setDiseaseSearchError(null);

      void searchDiseases(debouncedDiseaseQuery, 0, controller.signal)
        .then(response => {
          setDiseaseResults(response.results);
          setSearchedDiseaseQuery(debouncedDiseaseQuery);
          setHasMoreDiseases(response.has_more);
          setNextDiseaseOffset(response.offset + response.results.length);
        })
        .catch(error => {
          if (controller.signal.aborted) {
            return;
          }

          setDiseaseResults([]);
          setSearchedDiseaseQuery(debouncedDiseaseQuery);
          setHasMoreDiseases(false);
          setNextDiseaseOffset(0);
          setDiseaseSearchError(
            error instanceof Error ? error.message : '질병 검색에 실패했습니다.'
          );
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setDiseaseSearchLoading(false);
          }
        });
    }, 0);

    return () => {
      window.clearTimeout(timerId);
      controller.abort();
    };
  }, [debouncedDiseaseQuery]);

  const hasSearchedCurrentDisease = searchedDiseaseQuery === diseaseQuery;
  const showDiseaseResults =
    diseaseSearchFocused &&
    diseaseQuery.length >= 1 &&
    !hasIncompleteHangul &&
    (diseaseSearchLoading || hasSearchedCurrentDisease);

  const selectDisease = (disease: DiseaseSearchResult) => {
    setSearchText(disease.name);
    patch({ disease_name: disease.name, disease_kcd: disease.kcd });
    setDiseaseSearchFocused(false);
    setDiseaseResults([]);
  };

  const loadMoreDiseases = () => {
    if (!hasMoreDiseases || loadingMoreDiseases || !searchedDiseaseQuery) {
      return;
    }

    setLoadingMoreDiseases(true);
    setDiseaseSearchError(null);

    void searchDiseases(searchedDiseaseQuery, nextDiseaseOffset)
      .then(response => {
        setDiseaseResults(prev => [...prev, ...response.results]);
        setHasMoreDiseases(response.has_more);
        setNextDiseaseOffset(response.offset + response.results.length);
      })
      .catch(error => {
        setDiseaseSearchError(error instanceof Error ? error.message : '질병 검색에 실패했습니다.');
      })
      .finally(() => setLoadingMoreDiseases(false));
  };

  const handleDiseaseResultsScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
    if (scrollHeight - scrollTop - clientHeight < 24) {
      loadMoreDiseases();
    }
  };

  return (
    <>
      <div className="grid gap-6 sm:grid-cols-2">
        <Field label="질병명 (KCD)" required>
          <Popover open={showDiseaseResults}>
            <PopoverTrigger asChild>
              <div className="relative">
                <Input
                  value={searchText}
                  placeholder="질병명 또는 KCD 코드를 입력하세요"
                  onFocus={() => setDiseaseSearchFocused(true)}
                  onBlur={() => window.setTimeout(() => setDiseaseSearchFocused(false), 100)}
                  onChange={event => {
                    setSearchText(event.target.value);
                    setDiseaseSearchError(null);
                  }}
                  className="pr-10"
                  role="combobox"
                  aria-expanded={showDiseaseResults}
                  aria-controls="disease-search-results"
                />
                <Search className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
              </div>
            </PopoverTrigger>
            <PopoverContent
              id="disease-search-results"
              role="listbox"
              align="start"
              side="bottom"
              sideOffset={8}
              onOpenAutoFocus={event => event.preventDefault()}
              className="z-50 max-h-64 w-(--radix-popover-trigger-width) overflow-y-auto p-0"
              onScroll={handleDiseaseResultsScroll}
            >
              {diseaseSearchLoading && (
                <p className="px-4 py-3 text-sm text-muted">질병을 검색하는 중입니다.</p>
              )}

              {!diseaseSearchLoading && diseaseSearchError && (
                <p className="px-4 py-3 text-sm text-red-600">{diseaseSearchError}</p>
              )}

              {!diseaseSearchLoading &&
                !diseaseSearchError &&
                diseaseResults.map(disease => (
                  <button
                    key={`${disease.kcd}-${disease.name}`}
                    type="button"
                    role="option"
                    onMouseDown={event => event.preventDefault()}
                    onClick={() => selectDisease(disease)}
                    className="flex w-full items-start gap-3 px-4 py-3 text-left text-sm transition-colors hover:bg-primary-tint/40 focus-visible:bg-primary-tint/40 focus-visible:outline-none"
                  >
                    <span className="mt-0.5 rounded-md bg-primary-tint px-2 py-0.5 font-mono text-xs font-bold text-primary">
                      {disease.kcd}
                    </span>
                    <span className="font-medium leading-6 text-ink">{disease.name}</span>
                  </button>
                ))}

              {!diseaseSearchLoading &&
                !diseaseSearchError &&
                diseaseResults.length === 0 &&
                searchedDiseaseQuery === diseaseQuery && (
                  <p className="px-4 py-3 text-sm text-muted">관련 검색어가 없습니다.</p>
                )}

              {loadingMoreDiseases && (
                <p className="border-t border-line px-4 py-3 text-sm text-muted">
                  더 불러오는 중입니다.
                </p>
              )}

              {!diseaseSearchLoading &&
                !loadingMoreDiseases &&
                !diseaseSearchError &&
                diseaseResults.length > 0 &&
                !hasMoreDiseases &&
                searchedDiseaseQuery === diseaseQuery && (
                  <p className="border-t border-line px-4 py-3 text-center text-xs text-muted">
                    마지막 관련 검색어입니다.
                  </p>
                )}
            </PopoverContent>
          </Popover>
          {form.disease_kcd && (
            <span className="text-xs text-muted">KCD 코드: {form.disease_kcd}</span>
          )}
        </Field>

        <Field label="입/통원 여부" required>
          <RadioGroup
            className="flex gap-6 pt-2"
            value={inOut}
            onValueChange={value =>
              patch({
                is_inpatient: value === 'inpatient',
                is_outpatient: value === 'outpatient',
              })
            }
          >
            <label className="flex items-center gap-2 text-sm text-ink">
              <RadioGroupItem value="inpatient" /> 입원
            </label>
            <label className="flex items-center gap-2 text-sm text-ink">
              <RadioGroupItem value="outpatient" /> 통원
            </label>
          </RadioGroup>
        </Field>
      </div>

      {/* 입원 상세 — 입원일 때만 노출 */}
      {form.is_inpatient && (
        <div className="mt-5 grid gap-5 rounded-card border-2 border-dashed border-line p-5 sm:grid-cols-3">
          <Field label="수술 여부" required>
            <RadioGroup
              className="flex gap-6 pt-2"
              value={form.surgery ? 'yes' : 'no'}
              onValueChange={value => patch({ surgery: value === 'yes' })}
            >
              <label className="flex items-center gap-2 text-sm text-ink">
                <RadioGroupItem value="yes" /> 수술함
              </label>
              <label className="flex items-center gap-2 text-sm text-ink">
                <RadioGroupItem value="no" /> 수술하지 않음
              </label>
            </RadioGroup>
          </Field>

          <Field label="현재 입원일수">
            <NumberField
              value={form.admission_days_current}
              onChange={v => patch({ admission_days_current: v })}
              placeholder="예) 5"
              suffix="일"
            />
          </Field>

          <Field label="진단 입원일수">
            <NumberField
              value={form.admission_days_diagnosed}
              onChange={v => patch({ admission_days_diagnosed: v })}
              placeholder="예) 7"
              suffix="일"
            />
          </Field>
        </div>
      )}
    </>
  );
}
