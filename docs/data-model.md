# 데이터 모델 / 도메인 경계 (`supabase/migrations/`)

> `CLAUDE.md` 에서 `@docs/data-model.md` 로 로드됨.

- `001_policy_domain.sql` — `policies · riders · rider_chunks` (약관 도메인). `riders` 가 시스템의 심장. 임베딩은 `vector(1536)` + ivfflat.
- `002_service_domain.sql` — `cases · analysis_results · reports` (서비스 도메인). 사용자는 Supabase Auth(`auth.users`) 사용 — 자체 users 테이블 없음, `user_id`(uuid)로만 참조.

## 불변 규칙

- **마이그레이션**: 각 도메인 스키마 변경 권한은 단독 소유자에게 있고, 변경은 **기존 파일 수정이 아니라 새 마이그레이션 파일**로만 한다.
- **스냅샷**: `analysis_results` 는 생성 시점의 `policy_name·rider_name·evidence` 값을 복사해 저장하며, 이후 `riders` 변경과 무관하게 불변이다.
- **검수 게이팅**: 검수 전 데이터는 `verified=false` 유지. `verified=false` 는 `potential` 등급으로만 노출하고, 정밀 판정은 `verified=true` 이후에만.
