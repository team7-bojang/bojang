import { useEffect, useRef, useState } from 'react';

interface Obstacle {
  x: number;
  width: number;
  height: number;
  label: string;
  scored: boolean;
}

const GAME_WIDTH = 720;
const GAME_HEIGHT = 320;
const GROUND_Y = 246;
const PLAYER_X = 92;
const PLAYER_SIZE = 42;
const GRAVITY = 0.0018;
const JUMP_VELOCITY = -0.78;
const OBSTACLE_LABELS = ['면책', '감액', '대기기간', '기청구'];

function rectsOverlap(a: DOMRectReadOnly, b: DOMRectReadOnly) {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

function drawGame(
  canvas: HTMLCanvasElement,
  playerY: number,
  obstacles: Obstacle[],
  score: number,
  crashed: boolean
) {
  const dpr = window.devicePixelRatio || 1;
  const width = Math.floor(canvas.clientWidth * dpr);
  const height = Math.floor(canvas.clientHeight * dpr);

  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return;
  }

  const scaleX = canvas.clientWidth / GAME_WIDTH;
  const scaleY = canvas.clientHeight / GAME_HEIGHT;
  ctx.setTransform(dpr * scaleX, 0, 0, dpr * scaleY, 0, 0);
  ctx.clearRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

  const bg = ctx.createLinearGradient(0, 0, 0, GAME_HEIGHT);
  bg.addColorStop(0, '#0a3f3a');
  bg.addColorStop(0.6, '#0d6e66');
  bg.addColorStop(1, '#d8ece8');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, GAME_WIDTH, GAME_HEIGHT);

  ctx.fillStyle = 'rgba(255,255,255,0.16)';
  for (let i = 0; i < 12; i += 1) {
    ctx.beginPath();
    ctx.arc(60 + i * 58, 44 + ((i * 37) % 110), 2 + (i % 3), 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = 'rgba(255,255,255,0.88)';
  ctx.beginPath();
  ctx.roundRect(34, 30, 184, 44, 14);
  ctx.fill();
  ctx.fillStyle = '#0a3f3a';
  ctx.font = '800 16px Pretendard, system-ui, sans-serif';
  ctx.fillText(`검토한 약관 ${score}건`, 54, 58);

  ctx.strokeStyle = 'rgba(255,255,255,0.72)';
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(34, GROUND_Y);
  ctx.lineTo(GAME_WIDTH - 34, GROUND_Y);
  ctx.stroke();

  obstacles.forEach(obstacle => {
    const x = obstacle.x;
    const y = GROUND_Y - obstacle.height;

    ctx.fillStyle = '#fef3c7';
    ctx.beginPath();
    ctx.roundRect(x, y, obstacle.width, obstacle.height, 8);
    ctx.fill();
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = '#92400e';
    ctx.font = '800 15px Pretendard, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(obstacle.label, x + obstacle.width / 2, y + obstacle.height / 2 + 5);
  });

  const playerTop = GROUND_Y - PLAYER_SIZE - playerY;
  ctx.fillStyle = crashed ? '#fecaca' : '#ffffff';
  ctx.beginPath();
  ctx.roundRect(PLAYER_X, playerTop, PLAYER_SIZE, PLAYER_SIZE, 10);
  ctx.fill();
  ctx.strokeStyle = crashed ? '#dc2626' : '#14b8a6';
  ctx.lineWidth = 4;
  ctx.stroke();

  ctx.fillStyle = '#0a3f3a';
  ctx.font = '800 12px Pretendard, system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('보장', PLAYER_X + PLAYER_SIZE / 2, playerTop + 18);
  ctx.fillText('zip', PLAYER_X + PLAYER_SIZE / 2, playerTop + 33);

  ctx.fillStyle = '#14b8a6';
  ctx.beginPath();
  ctx.arc(PLAYER_X + 34, playerTop + 8, 5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = 'rgba(255,255,255,0.86)';
  ctx.font = '700 14px Pretendard, system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('스페이스 · 클릭 · 터치로 약관 조건을 넘겨보세요', GAME_WIDTH / 2, 292);
}

/** 분석 대기 중 사용자가 가볍게 조작할 수 있는 로딩 미니게임. */
export function LoadingMiniGame() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const playerYRef = useRef(0);
  const velocityRef = useRef(0);
  const obstaclesRef = useRef<Obstacle[]>([
    { x: 560, width: 68, height: 46, label: '면책', scored: false },
  ]);
  const lastTimeRef = useRef<number | null>(null);
  const nextLabelRef = useRef(1);
  const crashedUntilRef = useRef(0);
  const [score, setScore] = useState(0);

  useEffect(() => {
    const jump = () => {
      if (playerYRef.current <= 1) {
        velocityRef.current = JUMP_VELOCITY;
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'Space' || event.code === 'ArrowUp') {
        event.preventDefault();
        jump();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    let frameId = 0;

    const tick = (now: number) => {
      const previous = lastTimeRef.current ?? now;
      const delta = Math.min(32, now - previous);
      lastTimeRef.current = now;

      velocityRef.current += GRAVITY * delta;
      playerYRef.current = Math.max(0, playerYRef.current - velocityRef.current * delta);
      if (playerYRef.current === 0 && velocityRef.current > 0) {
        velocityRef.current = 0;
      }

      const speed = 0.24 + Math.min(score, 18) * 0.006;
      obstaclesRef.current = obstaclesRef.current
        .map(obstacle => ({ ...obstacle, x: obstacle.x - speed * delta }))
        .filter(obstacle => obstacle.x + obstacle.width > -20);

      const lastObstacle = obstaclesRef.current.at(-1);
      if (!lastObstacle || lastObstacle.x < 430) {
        const label = OBSTACLE_LABELS[nextLabelRef.current % OBSTACLE_LABELS.length];
        nextLabelRef.current += 1;
        obstaclesRef.current.push({
          x: GAME_WIDTH + 30,
          width: 76,
          height: 42 + (nextLabelRef.current % 2) * 10,
          label,
          scored: false,
        });
      }

      const playerRect = new DOMRect(
        PLAYER_X + 5,
        GROUND_Y - PLAYER_SIZE - playerYRef.current + 5,
        PLAYER_SIZE - 10,
        PLAYER_SIZE - 10
      );

      obstaclesRef.current.forEach(obstacle => {
        const obstacleRect = new DOMRect(
          obstacle.x + 5,
          GROUND_Y - obstacle.height + 5,
          obstacle.width - 10,
          obstacle.height - 10
        );
        if (rectsOverlap(playerRect, obstacleRect)) {
          crashedUntilRef.current = now + 450;
        }
        if (!obstacle.scored && obstacle.x + obstacle.width < PLAYER_X) {
          obstacle.scored = true;
          setScore(value => value + 1);
        }
      });

      if (canvasRef.current) {
        drawGame(
          canvasRef.current,
          playerYRef.current,
          obstaclesRef.current,
          score,
          crashedUntilRef.current > now
        );
      }

      frameId = window.requestAnimationFrame(tick);
    };

    frameId = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [score]);

  return (
    <canvas
      ref={canvasRef}
      className="block h-64 w-full rounded-card bg-primary-tint sm:h-80"
      role="img"
      aria-label="분석을 기다리는 동안 플레이하는 보장zip 미니게임"
      onPointerDown={() => {
        if (playerYRef.current <= 1) {
          velocityRef.current = JUMP_VELOCITY;
        }
      }}
    />
  );
}
