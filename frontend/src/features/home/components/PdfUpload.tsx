import { useRef, useState } from 'react';
import { CheckCircle2, FileText, Upload } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const MAX_SIZE_MB = 15;

type UploadStatus = 'idle' | 'uploading' | 'done' | 'error';

interface PdfUploadProps {
  /** 전송 중에는 onProgress로 실제 진행률을 보고하고, 서버 처리까지 끝나야 resolve 한다. */
  onSelect?: (file: File, onProgress: (percent: number) => void) => Promise<void>;
  className?: string;
}

/** 목록에 없는 보험 추가 — 약관 PDF 업로드 + 진행률 표시. */
export function PdfUpload({ onSelect, className }: PdfUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = async (file: File | undefined) => {
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

    try {
      // 전송(0~100%) 이후 서버의 텍스트 추출이 끝나야 resolve 되므로, 그 사이는 진행률 100%로 고정한 채 "처리 중" 문구로 안내한다.
      await onSelect?.(file, percent => setProgress(percent));
      setProgress(100);
      setStatus('done');
    } catch (err) {
      setStatus('error');
      setError(
        err instanceof Error
          ? err.message
          : '약관 PDF 업로드에 실패했습니다. 잠시 후 다시 시도해주세요.'
      );
    }
  };

  const subText =
    status === 'uploading'
      ? progress >= 100
        ? '처리 중...'
        : `업로드 중... ${progress}%`
      : status === 'done'
        ? '업로드 완료'
        : status === 'error'
          ? error
          : `PDF만 가능 · 최대 ${MAX_SIZE_MB}MB`;

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    handleFile(event.dataTransfer.files[0]);
  };

  return (
    <section
      className={cn(
        'flex flex-col rounded-card bg-surface p-5 shadow-sm ring-1 ring-line sm:p-6 lg:p-4',
        className
      )}
    >
      <div className="shrink-0">
        <h2 className="text-lg font-bold text-ink lg:text-base">목록에 없는 보험 추가하기</h2>
      </div>

      <div
        className={cn(
          'mt-3 flex flex-col justify-center gap-2 rounded-card border-2 border-dashed bg-canvas px-4 py-2.5 transition-colors lg:mt-2 lg:py-2',
          dragActive ? 'border-primary bg-primary-tint/35' : 'border-line'
        )}
        onDragEnter={event => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragOver={event => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={event => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setDragActive(false);
          }
        }}
        onDrop={handleDrop}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={cn(
                'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors',
                status === 'done' ? 'bg-success-tint text-success' : 'bg-primary-tint text-primary'
              )}
            >
              {status === 'done' ? (
                <motion.span initial={{ scale: 0.5 }} animate={{ scale: 1 }} className="flex">
                  <CheckCircle2 className="size-4" />
                </motion.span>
              ) : (
                <FileText className="size-4" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink lg:text-xs">
                {fileName ?? '목록에 내 보험이 없다면 약관 PDF를 직접 올려주세요.'}
              </p>
              <p
                className={cn(
                  'truncate text-xs lg:text-[11px]',
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
          onChange={event => {
            handleFile(event.target.files?.[0]);
            event.target.value = '';
          }}
        />
      </div>
    </section>
  );
}
