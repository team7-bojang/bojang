-- 치료항목 ↔ 특약 매핑 시드
-- 실행 시점: seed_policies.py로 policies/riders를 적재한 다음
-- 재실행 정책: 기존 행을 전체 삭제하지 않고 동일 매핑만 UPSERT한다.
--
-- 일반 실손 항목인 XRAY, PHYSICAL_THERAPY, MEDICATION은
-- 특정 전용 특약과 직접 연결하지 않으므로 이 시드에서 제외한다.

BEGIN;

WITH treatment_rule_seed (
    policy_name,
    rider_name,
    treatment_code,
    rule_type,
    note
) AS (
    VALUES
        (
            '현대해상 Hi실손의료비보험',
            '3대비급여실손의료비(갱신형) - 자기공명영상진단(MRI/MRA)',
            'MRI_MRA',
            'required',
            'MRI/MRA 전용 특약'
        ),
        (
            'KB 9회주는 암보험Plus',
            '2대질환 CT, MRI, 심장초음파, 뇌파, 뇌척수액 검사지원비(급여, 연간1회한)',
            'CT',
            'required',
            'MRI/CT 검사비 특약이 실제 존재하는 경우만 매핑'
        ),
        (
            'KB 9회주는 암보험Plus',
            '암 MRI,PET,CT,초음파검사지원비(진단후, 각 연간1회한)',
            'CT',
            'required',
            'MRI/CT 검사비 특약이 실제 존재하는 경우만 매핑'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 상해MRI/CT검사비(급여,연간1회한)보장 특별약관',
            'CT',
            'required',
            'MRI/CT 검사비 특약이 실제 존재하는 경우만 매핑'
        ),
        (
            '현대해상 Hi실손의료비보험',
            '3대비급여실손의료비(갱신형) - 도수치료·체외충격파치료·증식치료',
            'MANUAL_THERAPY',
            'required',
            '도수치료·체외충격파 전용 특약'
        ),
        (
            '현대해상 Hi실손의료비보험',
            '3대비급여실손의료비(갱신형) - 도수치료·체외충격파치료·증식치료',
            'ECSWT',
            'required',
            '도수치료·체외충격파 전용 특약'
        ),
        (
            '현대해상 Hi실손의료비보험',
            '3대비급여실손의료비(갱신형) - 주사료',
            'INJECTION',
            'required',
            '3대 비급여 주사료 특약'
        ),
        (
            '교보생명 New내생애맞춤건강보험',
            '무배당 교보깁스치료(부목제외)특약',
            'CAST',
            'required',
            '깁스 치료 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 깁스치료비보장 특별약관',
            'CAST',
            'required',
            '깁스 치료 특약'
        ),
        (
            'DB 계속받는 3대질병보험',
            '응급실내원보험금(비갱신형/갱신형)',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 상해 응급실내원비(응급)',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 응급실내원비(응급)보장',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 응급실내원비(1등급)보장',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 응급실내원비(2등급)보장',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        ),
        (
            '메리츠 상해안심보험',
            '갱신형 응급실내원비(3등급)보장',
            'EMERGENCY',
            'required',
            '응급실 내원 특약'
        )
)
INSERT INTO public.rider_treatment_rules (
    rider_id,
    treatment_code,
    rule_type,
    note
)
SELECT
    r.id,
    s.treatment_code,
    s.rule_type,
    s.note
FROM treatment_rule_seed s
JOIN public.policies p
  ON p.name = s.policy_name
 AND p.is_preset = true
JOIN public.riders r
  ON r.policy_id = p.id
 AND r.name = s.rider_name
ON CONFLICT (rider_id, treatment_code, rule_type) DO UPDATE
SET note = EXCLUDED.note;

COMMIT;

-- 검증 쿼리: 현재 기준 총 15건이어야 한다.
SELECT
    treatment_code,
    count(*) AS mapping_count
FROM public.rider_treatment_rules
GROUP BY treatment_code
ORDER BY treatment_code;
