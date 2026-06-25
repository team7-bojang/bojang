-- 012 롤백: 012_fix_disease_group_overmatch.sql 을 적용 전 상태로 되돌린다.
--
-- 012 는 테이블/컬럼 변경 없이 '행(데이터)'만 추가/삭제하는 마이그레이션이므로,
-- 아래 역순 DML 로 원복된다. (Supabase SQL Editor 에서 수동 실행)
--
-- ▷ 정밀 매칭: 012 가 넣은 '정확한 행'만 지운다.
--   - rider_disease_rules: (특약명 패턴 + group_id) 쌍이 정확히 일치하는 것만 삭제
--     → 그 사이 팀원이 같은 그룹에 다른 패턴(예: '%녹내장수술%')을 추가했어도 보존된다.
--   - disease_groups: '아직 아무 rider 룰도 참조하지 않을 때만' 삭제
--     → 팀원이 그 그룹을 계속 쓰면 그룹은 남겨둔다(팀원 보호 + FK 위반 방지).
--   - code_rules·aliases 는 그룹 삭제 시 ON DELETE CASCADE 로 함께 제거된다.
-- 두 번 실행해도 안전하도록 작성(idempotent).


-- ── (2)·(3) 역: 012 가 추가한 rider_disease_rules 만 (패턴+그룹) 쌍으로 정확히 제거 ──
delete from rider_disease_rules
 where (rider_name_pattern, group_id) in (
   ('%간경변%',       'liver_cirrhosis'),
   ('%녹내장%',       'glaucoma'),
   ('%뇌전증%',       'epilepsy'),
   ('%루게릭%',       'als'),
   ('%일과성뇌허혈%', 'tia'),
   ('%특정망막질환%', 'retinal_disease'),
   ('%3대질병%',      'general_cancer_excl_similar'),
   ('%3대질병%',      'cerebrovascular'),
   ('%3대질병%',      'ischemic_heart'),
   ('%3대질병%',      'acute_mi'),
   ('%3대질병%',      'stroke')
 );


-- ── (2) 역: 012 가 추가한 신규 질병군 제거 — 단, 남은 참조가 없을 때만 ──────────────
-- 팀원이 같은 그룹을 계속 참조하면(rider_disease_rules 에 남아 있으면) 그룹을 보존한다.
delete from disease_groups dg
 where dg.id in ('liver_cirrhosis', 'glaucoma', 'epilepsy', 'als', 'tia', 'retinal_disease')
   and not exists (select 1 from rider_disease_rules r where r.group_id = dg.id);


-- ── (1) 역: 삭제했던 specific_small_cancer 의 C00~C97 매핑 복원 (중복 방지 가드) ──────
insert into disease_group_code_rules (group_id, rule_type, code_start, code_end, confidence, note)
select 'specific_small_cancer', 'include', 'C00', 'C97', 'policy_review_required',
       '특정 소액암은 약관 별표가 대상 암종을 직접 열거함. KCD 범위로 확정하지 말고 rider별 별표 정의로 검수'
 where not exists (
   select 1 from disease_group_code_rules
    where group_id = 'specific_small_cancer' and rule_type = 'include'
      and code_start = 'C00' and code_end = 'C97'
 );

-- ⚠️ 코드(서비스 필터·conditional 분리)는 이 SQL 로 되돌아가지 않는다.
--    탐색 결과를 012 적용 전과 '완전히' 동일하게 하려면 해당 커밋(7720eef)도 git 으로 되돌려야 한다.
