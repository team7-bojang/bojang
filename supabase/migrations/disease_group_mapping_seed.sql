-- 질병군 매핑 레이어 v1
-- 목적: 사용자 자연어 질병명 -> KCD 후보 -> 질병군 -> 약관 특약 매칭
-- 주의: 아래 KCD 범위는 MVP 시드이며, 실제 지급 판단에는 각 약관 별표 기준 검수가 필요하다.
--
-- ============================================================================
-- [매칭 로직 규칙] rider_disease_rules 적용 시 judge 전처리 단계에서 반드시 처리
-- (seed 데이터 자체가 아니라 매칭 코드에서 구현. 데모 6개 약관 391건 검증 기준)
--
-- 규칙 1) priority 단일 선택
--   한 특약이 여러 질병군 패턴에 매칭되면, disease_groups.match_priority 가
--   가장 높은 1개만 'required'(확정)로 적용하고 나머지는 후보(candidate)로 둔다.
--   예) "중증 갑상선암 진단자금" -> %갑상선암%(100) + %암진단%(90)
--       => required=thyroid_cancer, 후보=[cancer_all]
--
-- 규칙 2) "유사암 제외" 보정
--   특약명에 "유사암제외" 또는 "유사암및"이 있으면 cancer_all/similar_cancer 를 빼고
--   general_cancer_excl_similar(일반암-유사암제외)로 확정한다.
--   예) "암진단비(유사암제외)" -> required=general_cancer_excl_similar
--
-- 규칙 3) "특정소액암/소액암 제외" 보정
--   특약명에 "특정소액암및" / "특정소액암제외" / "소액암제외"가 있으면
--   specific_small_cancer 를 빼고 일반암(general_cancer_excl_similar/cancer_all)으로 본다.
--   예) "암진단비(특정소액암 및 유사암제외)" -> required=general_cancer_excl_similar
--   (주의: 단순 %소액암% 매칭은 specific_small_cancer 이지만, "제외" 표현이면 반대로 빼야 함)
--
-- 위 3개는 보장명 패턴의 한계를 보정하는 것이며, 데모 약관은 적재 후 rider_id 로
-- 직접 고정 매핑하는 것을 최종 권장한다(rider_name_pattern 은 초안용).
-- ============================================================================

create table if not exists disease_groups (
  id text primary key,
  name text not null,
  group_type text not null check (group_type in ('disease', 'injury', 'cancer', 'treatment_context', 'non_kcd')),
  match_priority int not null default 50,
  requires_policy_appendix boolean not null default false,
  description text,
  user_label text not null
);

create table if not exists disease_group_aliases (
  id bigserial primary key,
  group_id text not null references disease_groups(id) on delete cascade,
  alias text not null,
  source text not null default 'service',
  unique (group_id, alias)
);

create table if not exists disease_group_code_rules (
  id bigserial primary key,
  group_id text not null references disease_groups(id) on delete cascade,
  rule_type text not null check (rule_type in ('include', 'exclude')),
  code_start text not null,
  code_end text,
  code_system text not null default 'KCD',
  confidence text not null default 'policy_review_required' check (confidence in ('high', 'medium', 'policy_review_required')),
  note text
);

create table if not exists rider_disease_rules (
  id bigserial primary key,
  policy_id uuid references policies(id) on delete cascade,
  rider_id uuid references riders(id) on delete cascade,
  rider_name_pattern text,
  rule_type text not null check (rule_type in ('required', 'excluded', 'optional')),
  group_id text not null references disease_groups(id),
  require_trigger_type text,
  note text,
  unique (policy_id, rider_id, rider_name_pattern, rule_type, group_id)
);

alter table cases
  add column if not exists disease_kcd_candidates jsonb not null default '[]',
  add column if not exists disease_group_candidates jsonb not null default '[]',
  add column if not exists disease_match_confidence text;

insert into disease_groups (id, name, group_type, match_priority, requires_policy_appendix, description, user_label) values
  ('general_disease', '일반 질병', 'disease', 10, false, '상해가 아닌 질병 전체. 실손/입원/수술의 원인 분류에 사용', '질병'),
  ('injury', '상해', 'injury', 10, false, '급격하고 우연한 외래 사고로 인한 상해', '상해'),
  ('disc_disease', '디스크질환', 'disease', 40, false, '목디스크/허리디스크 등 추간판장애 후보', '디스크 관련 질환'),
  ('cancer_all', '암', 'cancer', 90, true, '약관상 악성신생물 암. 보험사/상품별 별표 확인 필요', '암'),
  ('general_cancer_excl_similar', '일반암(유사암 제외)', 'cancer', 95, true, '기타피부암, 갑상선암, 제자리암, 경계성종양 등을 제외하는 암 보장', '일반암'),
  ('similar_cancer', '유사암', 'cancer', 95, true, '기타피부암, 갑상선암, 제자리암, 경계성종양 등', '유사암'),
  ('specific_small_cancer', '특정 소액암', 'cancer', 100, true, '약관에서 별도로 정의하는 특정 소액암. 일반암과 지급액·조건이 다르며 보험사/상품별 별표 정의 확인 필요', '특정 소액암'),
  ('thyroid_cancer', '갑상선암', 'cancer', 100, true, '갑상선의 악성신생물. 중증/초기제외 여부는 별도 규칙 필요', '갑상선암'),
  ('other_skin_cancer', '기타피부암', 'cancer', 100, true, '기타 피부의 악성신생물', '기타피부암'),
  ('carcinoma_in_situ', '제자리암', 'cancer', 100, true, '제자리신생물', '제자리암'),
  ('borderline_tumor', '경계성종양', 'cancer', 100, true, '행동양식 불명 또는 미상의 신생물 등 약관상 경계성종양', '경계성종양'),
  ('metastatic_cancer', '전이암', 'cancer', 95, true, '이차성/상세불명 악성신생물. 원발암 기준 예외 주의', '전이암'),
  ('male_genital_cancer', '남성생식기관련암', 'cancer', 90, true, '전립선, 음경, 고환 등 남성생식기관련암', '남성생식기관련암'),
  ('female_genital_cancer', '여성생식기관련암', 'cancer', 90, true, '자궁, 난소, 외음, 질, 태반 등 여성생식기관련암', '여성생식기관련암'),
  ('breast_cancer', '유방암', 'cancer', 90, true, '유방의 악성신생물', '유방암'),
  ('cerebrovascular', '뇌혈관질환', 'disease', 90, true, '뇌혈관질환 분류표 기준', '뇌혈관질환'),
  ('stroke', '뇌졸중', 'disease', 95, true, '뇌졸중 분류표 기준', '뇌졸중'),
  ('cerebral_hemorrhage', '뇌출혈', 'disease', 95, true, '거미막밑출혈, 뇌내출혈 등', '뇌출혈'),
  ('ischemic_heart', '허혈심장질환', 'disease', 90, true, '허혈성/허혈심장질환 분류표 기준', '허혈심장질환'),
  ('acute_mi', '급성심근경색증', 'disease', 95, true, '급성심근경색증 분류표 기준', '급성심근경색증'),
  ('diabetes', '당뇨병', 'disease', 80, true, '당뇨병 및 당뇨 관련 주요질환의 기준 그룹', '당뇨병'),
  ('herpes_zoster', '대상포진', 'disease', 80, false, '대상포진', '대상포진'),
  ('gout', '통풍', 'disease', 80, false, '통풍', '통풍'),
  ('cataract', '백내장', 'disease', 80, false, '백내장', '백내장'),
  ('fracture', '골절', 'injury', 80, true, '골절분류표 기준. 치아파절 포함 여부는 특약별 rule로 제어', '골절'),
  ('fracture_excl_tooth', '골절(치아파절 제외)', 'injury', 85, true, '치아파절을 제외하는 골절분류표 기준', '골절'),
  ('burn_corrosion_frostbite', '화상/부식/동상', 'injury', 80, true, '화상, 부식, 동상 관련 상해 분류', '화상/동상'),
  ('specific_injury', '특정상해', 'injury', 75, true, '특정다빈도상해, 특정상해손상, 특정고심도상해 등 별표 기준', '특정상해')
on conflict (id) do update set
  name = excluded.name,
  group_type = excluded.group_type,
  match_priority = excluded.match_priority,
  requires_policy_appendix = excluded.requires_policy_appendix,
  description = excluded.description,
  user_label = excluded.user_label;

insert into disease_group_aliases (group_id, alias) values
  ('disc_disease', '허리디스크'),
  ('disc_disease', '목디스크'),
  ('disc_disease', '디스크'),
  ('disc_disease', '추간판탈출'),
  ('disc_disease', '추간판장애'),
  ('cancer_all', '암'),
  ('general_cancer_excl_similar', '일반암'),
  ('similar_cancer', '유사암'),
  ('specific_small_cancer', '특정소액암'),
  ('specific_small_cancer', '소액암'),
  ('thyroid_cancer', '갑상선암'),
  ('other_skin_cancer', '기타피부암'),
  ('carcinoma_in_situ', '제자리암'),
  ('borderline_tumor', '경계성종양'),
  ('metastatic_cancer', '전이암'),
  ('cerebrovascular', '뇌혈관질환'),
  ('stroke', '뇌졸중'),
  ('cerebral_hemorrhage', '뇌출혈'),
  ('ischemic_heart', '허혈심장질환'),
  ('ischemic_heart', '허혈성심장질환'),
  ('acute_mi', '급성심근경색증'),
  ('diabetes', '당뇨'),
  ('diabetes', '당뇨병'),
  ('herpes_zoster', '대상포진'),
  ('gout', '통풍'),
  ('cataract', '백내장'),
  ('fracture', '골절'),
  ('burn_corrosion_frostbite', '화상'),
  ('burn_corrosion_frostbite', '부식'),
  ('burn_corrosion_frostbite', '동상')
on conflict (group_id, alias) do nothing;

insert into disease_group_code_rules (group_id, rule_type, code_start, code_end, confidence, note) values
  ('disc_disease', 'include', 'M50', 'M51', 'medium', '목/허리 디스크 후보. 사용자 표현만으로 세부 코드는 확정하지 않음'),
  ('cancer_all', 'include', 'C00', 'C97', 'policy_review_required', '악성신생물 전체의 일반 범위. 보험 약관 별표 기준 검수 필요'),
  ('thyroid_cancer', 'include', 'C73', null, 'high', '갑상선의 악성신생물'),
  ('other_skin_cancer', 'include', 'C44', null, 'high', '기타 피부의 악성신생물'),
  ('carcinoma_in_situ', 'include', 'D00', 'D09', 'policy_review_required', '제자리신생물. 약관별 제자리암 정의 확인 필요'),
  ('borderline_tumor', 'include', 'D37', 'D48', 'policy_review_required', '경계성종양 후보 범위. 약관별 별표 확인 필요'),
  ('similar_cancer', 'include', 'C44', null, 'high', '기타피부암'),
  ('similar_cancer', 'include', 'C73', null, 'high', '갑상선암'),
  ('similar_cancer', 'include', 'D00', 'D09', 'policy_review_required', '제자리암 후보'),
  ('similar_cancer', 'include', 'D37', 'D48', 'policy_review_required', '경계성종양 후보'),
  ('specific_small_cancer', 'include', 'C00', 'C97', 'policy_review_required', '특정 소액암은 약관 별표가 대상 암종을 직접 열거함. KCD 범위로 확정하지 말고 rider별 별표 정의로 검수'),
  ('general_cancer_excl_similar', 'include', 'C00', 'C97', 'policy_review_required', '일반암 후보. 아래 제외 규칙 적용'),
  ('general_cancer_excl_similar', 'exclude', 'C44', null, 'high', '기타피부암 제외'),
  ('general_cancer_excl_similar', 'exclude', 'C73', null, 'high', '갑상선암 제외'),
  ('general_cancer_excl_similar', 'exclude', 'D00', 'D09', 'policy_review_required', '제자리암 제외'),
  ('general_cancer_excl_similar', 'exclude', 'D37', 'D48', 'policy_review_required', '경계성종양 제외'),
  ('metastatic_cancer', 'include', 'C77', 'C80', 'policy_review_required', '전이암/이차성 악성신생물. 원발암 기준 조항 주의'),
  ('breast_cancer', 'include', 'C50', null, 'high', '유방의 악성신생물'),
  ('male_genital_cancer', 'include', 'C60', 'C63', 'policy_review_required', '남성생식기관련암 후보'),
  ('female_genital_cancer', 'include', 'C51', 'C58', 'policy_review_required', '여성생식기관련암 후보'),
  ('cerebrovascular', 'include', 'I60', 'I69', 'policy_review_required', '뇌혈관질환 일반 범위. 보험사 별표 확인 필요'),
  ('stroke', 'include', 'I60', 'I63', 'policy_review_required', '뇌졸중 후보. 약관별 I65/I66 포함 여부 확인 필요'),
  ('cerebral_hemorrhage', 'include', 'I60', 'I62', 'policy_review_required', '뇌출혈 후보'),
  ('ischemic_heart', 'include', 'I20', 'I25', 'policy_review_required', '허혈심장질환 후보'),
  ('acute_mi', 'include', 'I21', 'I23', 'policy_review_required', '급성심근경색증 후보'),
  ('diabetes', 'include', 'E10', 'E14', 'policy_review_required', '당뇨병 후보'),
  ('herpes_zoster', 'include', 'B02', null, 'high', '대상포진'),
  ('gout', 'include', 'M10', null, 'high', '통풍'),
  ('cataract', 'include', 'H25', 'H26', 'medium', '백내장 후보'),
  ('fracture', 'include', 'S02', 'S92', 'policy_review_required', '골절은 부위별 S코드와 T코드가 섞일 수 있어 별표 검수 필요'),
  ('fracture_excl_tooth', 'include', 'S02', 'S92', 'policy_review_required', '치아파절 제외 조건은 rider_disease_rules 또는 별도 code exclude로 보강'),
  ('burn_corrosion_frostbite', 'include', 'T20', 'T35', 'policy_review_required', '화상/부식/동상 후보')
on conflict do nothing;

-- 특약명 패턴 기반 초안. 실제 적재 후에는 rider_id 기준으로 고정하는 것을 권장한다.
insert into rider_disease_rules (rider_name_pattern, rule_type, group_id, require_trigger_type, note) values
  ('%암진단%', 'required', 'cancer_all', '진단', '암 진단 계열. 세부 제외는 특약명으로 추가 rule 적용'),
  ('%암진단비%유사암제외%', 'required', 'general_cancer_excl_similar', '진단', '일반암 보장'),
  ('%유사암진단%', 'required', 'similar_cancer', '진단', '유사암 보장'),
  ('%특정소액암%', 'required', 'specific_small_cancer', null, '특정 소액암 전용/포함 보장. priority 100으로 %암진단%(일반암)보다 우선'),
  ('%소액암%', 'required', 'specific_small_cancer', null, '소액암 계열 보장. 매칭 시 priority로 일반암(cancer_all)보다 우선 적용'),
  ('%갑상선암%', 'required', 'thyroid_cancer', null, '갑상선암 전용/포함 보장'),
  ('%기타피부암%', 'required', 'other_skin_cancer', null, '기타피부암 전용/포함 보장'),
  ('%제자리암%', 'required', 'carcinoma_in_situ', null, '제자리암 전용/포함 보장'),
  ('%경계성종양%', 'required', 'borderline_tumor', null, '경계성종양 전용/포함 보장'),
  ('%전이암%', 'required', 'metastatic_cancer', null, '전이암 보장'),
  ('%남성생식기관련%', 'required', 'male_genital_cancer', null, '남성생식기관련암 보장'),
  ('%여성생식기관련%', 'required', 'female_genital_cancer', null, '여성생식기관련암 보장'),
  ('%유방암%', 'required', 'breast_cancer', null, '유방암 보장'),
  ('%뇌혈관질환%', 'required', 'cerebrovascular', null, '뇌혈관질환 보장'),
  ('%뇌졸중%', 'required', 'stroke', null, '뇌졸중 보장'),
  ('%뇌출혈%', 'required', 'cerebral_hemorrhage', null, '뇌출혈 보장'),
  ('%허혈%심장질환%', 'required', 'ischemic_heart', null, '허혈심장질환 보장'),
  ('%급성심근경색%', 'required', 'acute_mi', null, '급성심근경색증 보장'),
  ('%당뇨%', 'required', 'diabetes', null, '당뇨/당뇨 관련 주요질환 보장'),
  ('%대상포진%', 'required', 'herpes_zoster', null, '대상포진 보장'),
  ('%통풍%', 'required', 'gout', null, '통풍 보장'),
  ('%백내장%', 'required', 'cataract', null, '백내장 보장'),
  ('%골절%치아파절제외%', 'required', 'fracture_excl_tooth', null, '치아파절 제외 골절 보장'),
  ('%골절%', 'required', 'fracture', null, '골절 보장'),
  ('%화상%', 'required', 'burn_corrosion_frostbite', null, '화상/부식/동상 보장'),
  ('%부식%', 'required', 'burn_corrosion_frostbite', null, '화상/부식/동상 보장'),
  ('%동상%', 'required', 'burn_corrosion_frostbite', null, '화상/부식/동상 보장'),
  ('%특정상해%', 'required', 'specific_injury', null, '약관 별표 기반 특정상해 보장'),
  ('%질병급여실손%', 'optional', 'general_disease', null, '실손은 질병군보다 급여/비급여, 입원/통원, 금액이 우선'),
  ('%질병비급여실손%', 'optional', 'general_disease', null, '실손은 질병군보다 급여/비급여, 입원/통원, 금액이 우선'),
  ('%질병입원일당%', 'optional', 'general_disease', '입원', '일반 질병 입원 여부 중심'),
  ('%질병수술비%', 'optional', 'general_disease', '수술', '일반 질병 수술 여부 중심')
on conflict do nothing;

