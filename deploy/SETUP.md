# EC2 무중단 배포 1회성 셋업 가이드

> 이 절차는 **서버에서 딱 한 번** 실행하면 된다. 이후 `develop` 에 merge되면
> `.github/workflows/backend-deploy.yml` 이 자동으로 무중단 배포(`systemctl reload`)를 수행한다.
>
> 목표 구조: `인터넷 → nginx(:80) → gunicorn(127.0.0.1:5000) ← systemd 관리`

아래 예시는 유저 `ubuntu`, 레포 경로 `/home/ubuntu/bojang` 기준 — **본인 환경에 맞게 치환**할 것.

---

## 0. 변수 정해두기 (이후 명령에 사용)

```bash
APP_DIR=/home/ubuntu/bojang      # 레포 루트 (= AWS_BACKEND_PATH)
DEPLOY_USER=ubuntu               # SSH 접속 유저 (= AWS_USER)
```

## 0-1. 최초 부트스트랩 — 레포 clone + venv 생성 (처음 1회만)

> EC2에 레포가 아직 없을 때만. 이미 clone돼 있으면 건너뛴다.

**(a) 비공개 레포 접근용 Deploy Key 등록** — EC2가 `git pull` 하려면 인증이 필요하다:

```bash
ssh-keygen -t ed25519 -C "ec2-bojang-deploy" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

출력된 공개키를 GitHub 레포 → **Settings → Deploy keys → Add deploy key** 에 등록(읽기 전용이면 충분).

**(b) clone (develop 브랜치 기준)** — 배포 워크플로가 `git pull origin develop` 을 쓰므로 develop 을 받는다:

```bash
cd "$(dirname "$APP_DIR")"
git clone -b develop git@github.com:team7-bojang/bojang.git "$(basename "$APP_DIR")"
```

> `develop` 브랜치가 아직 원격에 없으면 먼저 만들어 push해야 한다(로컬: `git push origin develop`).

**(c) venv 생성** — 시스템 python3 로 만든다. **conda(base) 가 활성화돼 있으면 먼저 `conda deactivate`**
(systemd 서비스는 venv 절대경로를 쓰므로 conda 와 무관하지만, venv 생성은 깨끗한 python 으로):

```bash
conda deactivate 2>/dev/null || true
sudo apt-get update && sudo apt-get install -y python3-venv
cd "$APP_DIR/backend"
python3 -m venv .venv
```

## 1. 의존성 설치 (gunicorn 포함)

```bash
cd "$APP_DIR/backend"
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt   # requirements 에 gunicorn 포함됨
deactivate
```

## 2. systemd 서비스 등록

`deploy/gunicorn.service` 의 placeholder를 실제 값으로 치환해 설치한다:

```bash
sudo sed \
  -e "s#__DEPLOY_USER__#$DEPLOY_USER#g" \
  -e "s#__APP_DIR__#$APP_DIR#g" \
  "$APP_DIR/deploy/gunicorn.service" \
  > /etc/systemd/system/bojang.service

sudo systemctl daemon-reload
sudo systemctl enable --now bojang        # 부팅 시 자동 시작 + 즉시 기동
sudo systemctl status bojang --no-pager   # active (running) 확인
curl -fsS http://127.0.0.1:5000/health    # {"status":"ok"} 확인
```

## 3. nginx 리버스 프록시 설정

```bash
sudo cp "$APP_DIR/deploy/nginx-bojang.conf" /etc/nginx/sites-available/bojang
sudo ln -sf /etc/nginx/sites-available/bojang /etc/nginx/sites-enabled/bojang
sudo rm -f /etc/nginx/sites-enabled/default   # 기본 "Welcome to nginx" 페이지 제거
sudo nginx -t                                  # 문법 검사
sudo systemctl reload nginx
```

이제 `http://<EC2 퍼블릭 IP>/health` 로 접속하면 `{"status":"ok"}` 가 떠야 한다.

## 4. 배포 유저에 reload 권한만 부여 (sudo 전체 X)

GitHub Actions 가 비밀번호 없이 `systemctl reload/restart` 만 실행할 수 있도록 최소 권한을 준다:

```bash
echo "$DEPLOY_USER ALL=(root) NOPASSWD: /bin/systemctl reload bojang, /bin/systemctl restart bojang" \
  | sudo tee /etc/sudoers.d/bojang-deploy
sudo chmod 440 /etc/sudoers.d/bojang-deploy
sudo visudo -c                               # 문법 OK 확인
```

> 참고: 일부 배포판은 systemctl 경로가 `/usr/bin/systemctl` 이다.
> `which systemctl` 로 확인 후 sudoers 의 경로를 맞춰라.

---

## 완료 후 동작

- `develop` 에 backend 변경이 merge되면 → Actions 가 SSH 접속 → `git pull` → `pip install`
  → `sudo systemctl reload bojang` (워커 graceful 교체, **무중단**) → `/health` 헬스체크.
- 헬스체크 실패 시 워크플로가 **실패로 표시**되어 배포 문제를 즉시 인지할 수 있다.

## 필요한 GitHub Secrets

레포 Settings → Secrets and variables → Actions:

| Secret | 값 |
|---|---|
| `AWS_HOST` | EC2 퍼블릭 IP/도메인 |
| `AWS_USER` | SSH 유저 (`$DEPLOY_USER`) |
| `AWS_SSH_KEY` | SSH 개인키 (PEM 전체 내용) |
| `AWS_BACKEND_PATH` | 레포 루트 경로 (`$APP_DIR`) |
