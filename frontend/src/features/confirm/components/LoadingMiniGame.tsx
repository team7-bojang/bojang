import { useEffect, useRef, useState } from 'react';

interface Obstacle {
  x: number;
  width: number;
  height: number;
  scored: boolean;
}

const GAME_WIDTH = 720;
const GAME_HEIGHT = 200;
const GROUND_Y = 150;
const PLAYER_X = 80;
const PLAYER_SIZE = 36;
const GRAVITY = 0.0022;
const JUMP_VELOCITY = -0.82;

// 단색 크롬 공룡게임 느낌의 미니멀 팔레트
const INK = '#525252';
const LINE = '#bdbdbd';

function rectsOverlap(a: DOMRect, b: DOMRect) {
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

  // 바닥선
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, GROUND_Y);
  ctx.lineTo(GAME_WIDTH, GROUND_Y);
  ctx.stroke();

  // 장애물 (단순 막대)
  ctx.fillStyle = INK;
  obstacles.forEach(obstacle => {
    ctx.fillRect(obstacle.x, GROUND_Y - obstacle.height, obstacle.width, obstacle.height);
  });

  // 플레이어 (단순 사각형 + 눈)
  const playerTop = GROUND_Y - PLAYER_SIZE - playerY;
  ctx.fillStyle = crashed ? '#dc2626' : INK;
  ctx.fillRect(PLAYER_X, playerTop, PLAYER_SIZE, PLAYER_SIZE);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(PLAYER_X + PLAYER_SIZE - 12, playerTop + 8, 5, 5);

  // 점수
  ctx.fillStyle = INK;
  ctx.font = '700 15px ui-monospace, SFMono-Regular, Menlo, monospace';
  ctx.textAlign = 'right';
  ctx.fillText(String(score).padStart(5, '0'), GAME_WIDTH - 8, 24);
}

/** 분석 대기 중 가볍게 조작하는 미니멀 러너 게임. */
export function LoadingMiniGame() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const playerYRef = useRef(0);
  const velocityRef = useRef(0);
  const obstaclesRef = useRef<Obstacle[]>([{ x: 560, width: 18, height: 38, scored: false }]);
  const lastTimeRef = useRef<number | null>(null);
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

      const speed = 0.26 + Math.min(score, 20) * 0.006;
      obstaclesRef.current = obstaclesRef.current
        .map(obstacle => ({ ...obstacle, x: obstacle.x - speed * delta }))
        .filter(obstacle => obstacle.x + obstacle.width > -20);

      const lastObstacle = obstaclesRef.current.at(-1);
      if (!lastObstacle || lastObstacle.x < 420) {
        obstaclesRef.current.push({
          x: GAME_WIDTH + 30 + Math.random() * 120,
          width: 14 + Math.round(Math.random()) * 8,
          height: 30 + Math.round(Math.random() * 3) * 8,
          scored: false,
        });
      }

      const playerRect = new DOMRect(
        PLAYER_X + 4,
        GROUND_Y - PLAYER_SIZE - playerYRef.current + 4,
        PLAYER_SIZE - 8,
        PLAYER_SIZE - 8
      );

      obstaclesRef.current.forEach(obstacle => {
        const obstacleRect = new DOMRect(
          obstacle.x + 2,
          GROUND_Y - obstacle.height + 2,
          obstacle.width - 4,
          obstacle.height - 4
        );
        if (rectsOverlap(playerRect, obstacleRect)) {
          crashedUntilRef.current = now + 400;
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
      className="block h-40 w-full rounded-card bg-white sm:h-48"
      role="img"
      aria-label="분석을 기다리는 동안 즐기는 미니 러너 게임"
      onPointerDown={() => {
        if (playerYRef.current <= 1) {
          velocityRef.current = JUMP_VELOCITY;
        }
      }}
    />
  );
}
