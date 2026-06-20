import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, FileText, Upload } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const MAX_SIZE_MB = 15;

type UploadStatus = 'idle' | 'uploading' | 'done' | 'error';

interface PdfUploadProps {
  onSelect?: (file: File) => void;
  className?: string;
}

/** "PDF 업로드" — 약관 PDF 업로드 + 진행률 표시. */
export function PdfUpload({ onSelect, className }: PdfUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 컴포넌트 언마운트 시 진행률 타이머 정리.
  useEffect(() => () => window.clearInterval(timerRef.current), []);

  const handleFile = (file: File | undefined) => {
    if (!file) {
      return;
    }
    if (file.type !== 'application/pdf') {
      setStatus('error');
      setError('PDF 파일만 업로드할 수 있습니다.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setStatus('error');
      setError(`최대 ${MAX_SIZE_MB}MB까지 업로드할 수 있습니다.`);
      return;
    }

    setError(null);
    setFileName(file.name);
    setStatus('uploading');
    setProgress(0);

    // TODO: 실제 업로드 연동 시 axios onUploadProgress 값으로 setProgress 교체.
    window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          window.clearInterval(timerRef.current);
          setStatus('done');
          // 업로드 성공 후에만 스토어에 반영 (실패 시 잔류 방지).
          onSelect?.(file);
          return 100;
        }
        return prev + 8;
      });
    }, 90);
  };

  const subText =
    status === 'uploading'
      ? `업로드 중... ${Math.min(progress, 100)}%`
      : status === 'done'
        ? '업로드 완료'
        : status === 'error'
          ? error
          : `PDF만 가능 · 최대 ${MAX_SIZE_MB}MB`;

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6',
        className
      )}
    >
      <h2 className="shrink-0 text-lg font-bold text-ink">PDF 업로드</h2>

      <div className="mt-3 flex flex-1 flex-col justify-center gap-2.5 rounded-card border-2 border-dashed border-line bg-canvas px-4 py-3 lg:min-h-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={cn(
                'flex size-9 shrink-0 items-center justify-center rounded-lg transition-colors',
                status === 'done' ? 'bg-success-tint text-success' : 'bg-primary-tint text-primary'
              )}
            >
              {status === 'done' ? (
                <motion.span initial={{ scale: 0.5 }} animate={{ scale: 1 }} className="flex">
                  <CheckCircle2 className="size-5" />
                </motion.span>
              ) : (
                <FileText className="size-5" />
              )}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">
                {fileName ?? '보험 약관 PDF를 업로드 해주세요'}
              </p>
              <p
                className={cn(
                  'truncate text-xs',
                  status === 'error' ? 'text-red-500' : 'text-muted'
                )}
              >
                {subText}
              </p>
            </div>
          </div>

          <Button
            type="button"
            size="sm"
            variant={status === 'done' ? 'outline' : 'default'}
            className="shrink-0"
            disabled={status === 'uploading'}
            onClick={() => inputRef.current?.click()}
          >
            <Upload />
            {status === 'done' ? '다시 선택' : status === 'uploading' ? '업로드 중' : '파일 선택'}
          </Button>
        </div>

        <AnimatePresence>
          {(status === 'uploading' || status === 'done') && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="h-2 w-full overflow-hidden rounded-full bg-line/70">
                <motion.div
                  className="h-full rounded-full bg-linear-to-r from-primary-soft to-primary"
                  animate={{ width: `${Math.min(progress, 100)}%` }}
                  transition={{ ease: 'easeOut', duration: 0.2 }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={event => handleFile(event.target.files?.[0])}
        />
      </div>
    </section>
  );
}
