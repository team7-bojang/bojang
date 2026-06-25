-- 012: 질병군 매핑 과다매칭 보정 (pass 1)
--
-- 배경: 갑상선암(C73) 통원 등에서 무관 특약이 eligible 로 새는 문제(탐색 과다매칭).
--   judge 키워드 폴백이 룰테이블 미비 구간을 너무 느슨하게 통과시키는데, 그 중
--   '데이터가 틀려서' 또는 '룰이 아예 없어서' 생기는 명백한 오탐을 룰테이블에서 바로잡는다.
-- 이 파일이 고치는 것:
--   (1) specific_small_cancer 의 C00~C97 과잉 매핑 제거
--   (2) 무관 질병군(간경변/녹내장/뇌전증/루게릭/일과성뇌허혈/특정망막) 추가 + 해당 특약 게이팅
--   (3) 3대질병 진단비를 일반암(유사암 제외)·뇌·심장으로 한정
-- 효과(실측 시뮬): C73 통원 케이스 eligible 36 → 25 (골든 정답 3개 유지).
--   중증/재진단/직접치료 등 '입력에 없는 조건' 기반 오탐은 후속 pass 에서 처리.
--
-- ⚠️ 적용: Supabase SQL Editor 에서 수동 실행 (이 저장소의 마이그레이션은 자동 적용 안 됨).
-- ⚠️ 1회만 실행 권장 (rider_disease_rules 는 null 키라 on conflict 가 중복을 못 막을 수 있음).


-- ── (1) specific_small_cancer 의 C00~C97 과잉 매핑 제거 ──────────────────────
-- 특정소액암은 약관 별표가 대상 암종을 직접 열거하므로 KCD 범위로 확정하면 안 된다
-- (seed 주석에도 "KCD 범위로 확정하지 말 것"). 이 매핑 때문에 C73(갑상선암)이
-- specific_small_cancer 로 잡혀 아래 두 특약이 오매칭됐다:
--   · '특정 소액암 진단자금'                 (specific_small_cancer 요구 → 매칭)
--   · '암진단비(특정소액암 및 유사암제외)'    (제외해야 하는데 오히려 매칭)
-- 제거하면 C73 은 specific_small_cancer 에 속하지 않게 되어 둘 다 not_applicable 이 된다.
delete from disease_group_code_rules
 where group_id = 'specific_small_cancer'
   and rule_type = 'include'
   and code_start = 'C00'
   and code_end = 'C97';


-- ── (2) 무관 질병군 추가 + 해당 진단비 특약 게이팅 ──────────────────────────
-- 간경변/녹내장/뇌전증/루게릭/일과성뇌허혈/특정망막 진단비는 룰이 없어 폴백으로 통과해
-- 암 케이스에도 eligible 로 샜다. 각 질병군을 정의하고 특약명 패턴으로 require 를 건다.
insert into disease_groups (id, name, group_type, match_priority, requires_policy_appendix, description, user_label) values
  ('liver_cirrhosis', '간경변증', 'disease', 80, false, '간섬유증 및 간경변증', '간경변'),
  ('glaucoma', '녹내장', 'disease', 80, false, '녹내장', '녹내장'),
  ('epilepsy', '뇌전증', 'disease', 80, false, '뇌전증/간질', '뇌전증'),
  ('als', '루게릭병', 'disease', 85, true, '근위축성 측삭경화증(루게릭병) 등 척수성 근위축', '루게릭병'),
  ('tia', '일과성뇌허혈발작', 'disease', 85, true, '일과성 대뇌 허혈 발작 및 관련 증후군', '일과성뇌허혈'),
  ('retinal_disease', '특정망막질환', 'disease', 80, true, '망막박리·망막병증 등 특정 망막질환', '망막질환')
on conflict (id) do nothing;

insert into disease_group_code_rules (group_id, rule_type, code_start, code_end, confidence, note) values
  ('liver_cirrhosis', 'include', 'K74', null, 'medium', '간섬유증/간경변(K74)'),
  ('glaucoma', 'include', 'H40', 'H42', 'high', '녹내장'),
  ('epilepsy', 'include', 'G40', 'G41', 'high', '뇌전증/간질지속상태'),
  ('als', 'include', 'G12', null, 'medium', '척수성 근위축(G12.2 루게릭) 후보'),
  ('tia', 'include', 'G45', null, 'high', '일과성 대뇌 허혈 발작'),
  ('retinal_disease', 'include', 'H30', 'H36', 'medium', '망막질환 후보 범위')
on conflict do nothing;

insert into rider_disease_rules (rider_name_pattern, rule_type, group_id, require_trigger_type, note) values
  ('%간경변%', 'required', 'liver_cirrhosis', null, '간경변증 진단 보장'),
  ('%녹내장%', 'required', 'glaucoma', null, '녹내장 진단 보장'),
  ('%뇌전증%', 'required', 'epilepsy', null, '뇌전증 진단 보장'),
  ('%루게릭%', 'required', 'als', null, '루게릭병 진단 보장'),
  ('%일과성뇌허혈%', 'required', 'tia', null, '일과성뇌허혈발작 진단 보장'),
  ('%특정망막질환%', 'required', 'retinal_disease', null, '특정망막질환 진단 보장')
on conflict do nothing;


-- ── (3) 3대질병 진단비: 일반암(유사암 제외)·뇌·심장으로 한정 ─────────────────
-- '3대질병진단비/계속받는3대질병진단비/3대질병 장애진단비'가 룰 없이 폴백으로 통과해
-- 갑상선암(유사암)에도 잡혔다. 3대질병 = 일반암(유사암 제외) + 뇌혈관/뇌졸중 + 허혈심장/급성심근경색.
-- require 여러 개는 judge 에서 'OR'(하나라도 일치) 로 동작하므로, 위 중 하나에 속할 때만 매칭된다.
-- C73(갑상선암)은 어디에도 속하지 않아 not_applicable 이 된다(유사암 제외 취지와 일치).
insert into rider_disease_rules (rider_name_pattern, rule_type, group_id, require_trigger_type, note) values
  ('%3대질병%', 'required', 'general_cancer_excl_similar', null, '3대질병=일반암(유사암 제외) 한정'),
  ('%3대질병%', 'required', 'cerebrovascular', null, '3대질병=뇌혈관질환 포함'),
  ('%3대질병%', 'required', 'ischemic_heart', null, '3대질병=허혈심장질환 포함'),
  ('%3대질병%', 'required', 'acute_mi', null, '3대질병=급성심근경색 포함'),
  ('%3대질병%', 'required', 'stroke', null, '3대질병=뇌졸중 포함')
on conflict do nothing;
