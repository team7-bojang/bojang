import React, { useState, useEffect, useRef } from 'react';
import { api } from './api/client';
import './App.css';

interface Message {
  id: string;
  sender: 'bot' | 'user';
  text: string;
  timestamp: Date;
  actions?: React.ReactNode;
}

interface Preset {
  id: string;
  name: string;
  insurer?: string;
  type?: string;
  [key: string]: unknown;
}

interface ExtractedInfo {
  disease_name: string;
  disease_kcd: string;
  surgery: boolean;
  diag_days: number;
  current_days: number;
  policy_elapsed_days: number;
}

interface Scenario {
  name: string;
}

interface Outcome {
  status: string;
  calc?: string;
  gap_days?: number;
}

interface Comparison {
  policy: string;
  rider: string;
  outcomes: Outcome[];
}

interface CompareData {
  scenarios: Scenario[];
  comparisons: Comparison[];
}

interface ChecklistItem {
  task: string;
}

interface Evidence {
  article: string;
  page: number;
  quote: string;
  [key: string]: unknown;
}

interface AnalysisResult {
  policy: string;
  status: string;
  rider: string;
  calc?: string;
  gap_days?: number;
  explanation: string;
  missed?: boolean;
  evidence: Evidence;
  [key: string]: unknown;
}

interface Report {
  summary: ExtractedInfo;
  checklist: ChecklistItem[];
  statute_of_limitations?: string;
  disclaimer?: string;
  [key: string]: unknown;
}

let msgCounter = 0;
function generateId(): string {
  msgCounter += 1;
  return `${Date.now()}-${msgCounter}`;
}

export default function App() {
  // ── States ──
  const [step, setStep] = useState<number>(0); // 0: 보험선택, 1: 챗봇진행, 2: 분석완료
  const [serviceType, setServiceType] = useState<'CASE1' | 'CASE2'>('CASE1');
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPresets, setSelectedPresets] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Chat States
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [currentCaseId, setCurrentCaseId] = useState<string | null>(null);
  const [inputMethod, setInputMethod] = useState<'PAYMENT' | 'MEDICAL_DETAIL_STATEMENT' | null>(
    null
  );

  // Extracted Info for verification
  const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo>({
    disease_name: '',
    disease_kcd: '',
    surgery: false,
    diag_days: 0,
    current_days: 0,
    policy_elapsed_days: 800,
  });

  // Report States
  const [report, setReport] = useState<Report | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [analysisSummary, setAnalysisSummary] = useState<{
    eligible_count: number;
    missed_count: number;
  }>({
    eligible_count: 0,
    missed_count: 0,
  });
  const [activeTab, setActiveTab] = useState<'eligible' | 'missed' | 'compare' | 'checklist'>(
    'eligible'
  );
  const [selectedCover, setSelectedCover] = useState<AnalysisResult | null>(null);
  const [compareData, setCompareData] = useState<CompareData | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Initial Fetching ──
  useEffect(() => {
    fetchPresets();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  async function fetchPresets() {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/policies/presets');
      if (res.data.success) {
        setPresets(res.data.data.presets);
      }
    } catch (err: unknown) {
      console.error('보험 프리셋 목록을 불러오지 못했습니다.', err);
    } finally {
      setLoading(false);
    }
  }

  // ── Step 0: 가입할 보험 선택 ──
  const handleTogglePreset = (id: string) => {
    if (serviceType === 'CASE2') {
      // CASE2는 단일 보험만 선택 가능하므로 라디오 버튼처럼 동작
      setSelectedPresets([id]);
    } else {
      if (selectedPresets.includes(id)) {
        setSelectedPresets(selectedPresets.filter(x => x !== id));
      } else {
        setSelectedPresets([...selectedPresets, id]);
      }
    }
  };

  const handleSelectServiceType = (type: 'CASE1' | 'CASE2') => {
    setServiceType(type);
    if (type === 'CASE2' && selectedPresets.length > 1) {
      setSelectedPresets([selectedPresets[0]]);
    }
  };

  const handleRegisterPolicies = async () => {
    if (selectedPresets.length === 0) {
      alert('최소 하나 이상의 보험을 선택해주세요.');
      return;
    }
    if (serviceType === 'CASE2' && selectedPresets.length > 1) {
      alert('추가 보장 비교(CASE2)는 단일 보험 상품 1개만 선택해야 합니다.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/api/v1/policies/select', {
        preset_ids: selectedPresets,
      });
      if (res.data.success) {
        setStep(1);
        // 첫 웰컴 메시지 추가
        const welcomeText =
          serviceType === 'CASE1'
            ? '안녕하세요! 가입하신 보험을 바탕으로 청구 가능한 특약을 찾아 드릴게요. 지금 어떤 치료나 질환 상황을 겪으셨나요?\n\n(예: "허리디스크 수술하고 30일 입원했어요", "뇌경색 3일 입원했는데 보장받을 수 있을까요?")'
            : '안녕하세요! 단일 보험의 추가 보장 및 조건 비교를 도와드릴게요. 지금 겪으신 치료 상황이나 분석할 의사 권고 사항을 말씀해 주세요.\n\n(예: "뇌경색으로 3일 입원했는데 의사가 7일 입원을 권고했어요.")';
        setChatMessages([
          {
            id: 'welcome',
            sender: 'bot',
            text: welcomeText,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err: unknown) {
      console.error(err);
      alert('보험 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 1: 상황 텍스트 전송 및 추천 ──
  const handleSendSituation = async (text: string) => {
    if (!text.trim()) {
      return;
    }

    // 유저 메시지 버블 추가
    const userMsg: Message = {
      id: generateId(),
      sender: 'user',
      text: text,
      timestamp: new Date(),
    };
    setChatMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);

    try {
      // POST /cases 호출
      const res = await api.post('/api/v1/cases', {
        service_type: serviceType,
        policy_ids: selectedPresets,
        initial_situation: text,
      });
      if (res.data.success) {
        const data = res.data.data;

        // 지원 범위 밖 질문 감지 처리 (FR-10b)
        if (data.out_of_scope) {
          setCurrentCaseId(null);
          const botMsg: Message = {
            id: generateId(),
            sender: 'bot',
            text: data.message,
            timestamp: new Date(),
            actions: (
              <div className="flex gap-2 mt-3 flex-wrap">
                <button
                  onClick={() =>
                    alert(
                      '저희 서비스는 실손의료비, 암 진단/수술/입원, 뇌혈관/심장질환 진단/입원/수술, 일반 질병 입원/수술 등 질병·암·실손·상해 약관을 지원 범위로 합니다.'
                    )
                  }
                  className="bg-gray-800 text-gray-200 border border-gray-700 px-4 py-2 rounded-xl text-xs font-semibold hover:bg-gray-700 shadow-md cursor-pointer"
                >
                  ℹ️ 지원 범위 다시 보기
                </button>
                <button
                  onClick={() => {
                    addBotMessage(
                      '질병·암·실손·상해와 관련된 치료 상황을 새로 설명해 주세요.\n\n(예: "허리디스크 14일 입원했어요", "뇌경색 3일 입원했어요")'
                    );
                  }}
                  className="bg-accent text-white px-4 py-2 rounded-xl text-xs font-semibold hover:opacity-90 shadow-md cursor-pointer"
                >
                  ✏️ 상황 다시 입력하기
                </button>
              </div>
            ),
          };
          setChatMessages(prev => [...prev, botMsg]);
          return;
        }

        setCurrentCaseId(data.case_id);

        // 질환 정보 임시 업데이트
        let parsedCurrent = 3;
        let parsedDiag = 7;
        if (text.includes('14일')) {
          parsedCurrent = 14;
          parsedDiag = 14;
        } else if (text.includes('30일')) {
          parsedCurrent = 30;
          parsedDiag = 30;
        } else if (text.includes('5일')) {
          parsedCurrent = 5;
          parsedDiag = 5;
        } else if (text.includes('3일')) {
          parsedCurrent = 3;
          parsedDiag = text.includes('7일') ? 7 : 3;
        }

        setExtractedInfo(prev => ({
          ...prev,
          disease_name: data.disease_name || (text.includes('뇌경색') ? '뇌경색증' : '기타 추간판 장애 (허리디스크)'),
          disease_kcd: data.disease_kcd || (text.includes('뇌경색') ? 'I63' : 'M51'),
          surgery: data.surgery !== undefined ? data.surgery : text.includes('수술'),
          current_days: parsedCurrent,
          diag_days: parsedDiag,
        }));

        // 챗봇 분석 결과 추천 버블 추가
        const statusText =
          data.claim_status === 'BEFORE_CLAIM'
            ? '아직 청구하지 않으신 상태'
            : '이미 청구해 보신 상태';

        if (serviceType === 'CASE2') {
          // CASE2: 영수증 입력 단계 없이 바로 의료 정보 검수 폼으로 연결
          const botMsg: Message = {
            id: generateId(),
            sender: 'bot',
            text: `상황을 확인했어요. 추가 보장 및 조건 비교를 진행하기 위해 아래의 진단 및 치료 정보를 검수해 주세요. 특히 '의사 권고 입원일수'가 맞는지 확인해 주세요.`,
            timestamp: new Date(),
            actions: renderVerificationForm(),
          };
          setChatMessages(prev => [...prev, botMsg]);
        } else {
          // CASE1: 기존의 영수증/내역서 입력 방식 분기 노출
          const botMsg: Message = {
            id: generateId(),
            sender: 'bot',
            text: `상황을 확인했어요. 의도 분석 결과, 고객님은 [${statusText}]로 판별됩니다.\n\n${data.message}\n\n분석을 진행할 자료의 입력 방식을 아래에서 골라주세요.`,
            timestamp: new Date(),
            actions: (
              <div className="flex gap-2 mt-3 flex-wrap">
                <button
                  onClick={() => handleSelectInputMethod(data.case_id, 'PAYMENT')}
                  className="btn-action bg-accent text-white px-4 py-2 rounded-xl text-sm font-semibold hover:opacity-90 shadow-md cursor-pointer"
                >
                  💳 결제 문자/카드내역 기반 (빠른 분석)
                </button>
                <button
                  onClick={() => handleSelectInputMethod(data.case_id, 'MEDICAL_DETAIL_STATEMENT')}
                  className="btn-action bg-gray-800 text-gray-200 border border-gray-700 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-gray-700 shadow-md cursor-pointer"
                >
                  📄 세부산정내역서 파일 기반 (정확한 분석)
                </button>
              </div>
            ),
          };
          setChatMessages(prev => [...prev, botMsg]);
        }
      }
    } catch (err: unknown) {
      console.error(err);
      addBotMessage('상황 분석 중 오류가 발생했습니다. 다시 입력해 주세요.');
    } finally {
      setLoading(false);
    }
  };

  const addBotMessage = (text: string, actions?: React.ReactNode) => {
    setChatMessages(prev => [
      ...prev,
      {
        id: generateId(),
        sender: 'bot',
        text,
        timestamp: new Date(),
        actions,
      },
    ]);
  };

  // 입력 방식 선택 시 흐름
  const handleSelectInputMethod = (
    caseId: string,
    method: 'PAYMENT' | 'MEDICAL_DETAIL_STATEMENT'
  ) => {
    setInputMethod(method);
    if (method === 'PAYMENT') {
      addBotMessage(
        '병원 결제 내역(문자 내용이나 복사한 결제 텍스트)을 아래에 입력해 주세요.\n\n(예: "OO정형외과 2026.06.10 결제금액 80,000원")',
        <div className="mt-2 text-xs text-gray-500 italic">
          결제 텍스트를 입력창에 적고 전송을 눌러주세요.
        </div>
      );
    } else {
      addBotMessage(
        '진료비 세부산정내역서 PDF 또는 이미지 파일을 업로드해 주세요.',
        <div className="mt-2 flex items-center gap-2">
          <input
            type="file"
            id="statement-file"
            className="hidden"
            onChange={e => handleUploadStatement(caseId, e.target.files?.[0])}
          />
          <label
            htmlFor="statement-file"
            className="bg-accent text-white px-4 py-2 rounded-lg text-xs font-semibold cursor-pointer hover:opacity-90"
          >
            파일 선택 및 업로드
          </label>
        </div>
      );
    }
  };

  // 결제내역 전송 처리
  const handleSendPaymentText = async (text: string) => {
    if (!currentCaseId) {
      return;
    }
    setLoading(true);
    try {
      const res = await api.post(`/api/v1/cases/${currentCaseId}/payment`, { payment_text: text });
      if (res.data.success) {
        addBotMessage(
          '결제 내역 데이터를 성공적으로 확인했습니다. 추출된 치료 정보에 오류가 없는지 검수해 주세요.',
          renderVerificationForm()
        );
      }
    } catch (err: unknown) {
      console.error(err);
      alert('결제 내역 처리 실패');
    } finally {
      setLoading(false);
    }
  };

  // 세부산정내역서 업로드 처리
  const handleUploadStatement = async (caseId: string, file?: File) => {
    if (!file) {
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post(`/api/v1/cases/${caseId}/medical-detail-statement`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.success) {
        // Mock 데이터로 세부산정내역서 추출 결과 폼 띄우기
        setExtractedInfo(prev => ({
          ...prev,
          diag_days: 14,
          current_days: 14,
          surgery: false,
        }));
        addBotMessage(
          `세부산정내역서(${file.name}) 분석이 끝났습니다. 추출된 세부 의료 처치 기록을 검수해 주세요.`,
          renderVerificationForm()
        );
      }
    } catch (err: unknown) {
      console.error(err);
      alert('파일 업로드 분석 실패');
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: 정보 검수 폼 랜더링 ──
  const renderVerificationForm = () => {
    return (
      <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl mt-3 text-sm text-left max-w-md w-full shadow-lg">
        <h4 className="font-bold text-accent mb-3 text-base">📋 추출 의료 정보 검수</h4>
        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">질병 진단명 (KCD)</label>
            <input
              type="text"
              value={`${extractedInfo.disease_name} (${extractedInfo.disease_kcd})`}
              disabled
              className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-xs text-gray-300"
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs text-gray-400 mb-1">입원 일수 (일)</label>
              <input
                type="number"
                value={extractedInfo.current_days}
                onChange={e =>
                  setExtractedInfo({
                    ...extractedInfo,
                    current_days: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-xs text-gray-300 focus:border-accent outline-none"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-gray-400 mb-1">가입일수 경과 (일)</label>
              <input
                type="number"
                value={extractedInfo.policy_elapsed_days}
                onChange={e =>
                  setExtractedInfo({
                    ...extractedInfo,
                    policy_elapsed_days: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-xs text-gray-300 focus:border-accent outline-none"
              />
            </div>
          </div>
          {serviceType === 'CASE2' && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">의사 권고 입원일수 (일)</label>
              <input
                type="number"
                value={extractedInfo.diag_days}
                onChange={e =>
                  setExtractedInfo({
                    ...extractedInfo,
                    diag_days: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-xs text-gray-300 focus:border-accent outline-none"
              />
            </div>
          )}
          <div className="flex items-center gap-2 mt-1">
            <input
              type="checkbox"
              id="surgery-check"
              checked={extractedInfo.surgery}
              onChange={e => setExtractedInfo({ ...extractedInfo, surgery: e.target.checked })}
              className="accent-accent cursor-pointer"
            />
            <label htmlFor="surgery-check" className="text-xs text-gray-300 cursor-pointer">
              수술적 처치를 받으셨나요?
            </label>
          </div>
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleConfirmVerification}
              className="flex-1 bg-accent text-white font-bold py-2 rounded text-xs hover:opacity-90 cursor-pointer"
            >
              네, 분석할게요
            </button>
            <button
              onClick={() => {
                alert('정보를 수정하여 다시 제출해주세요.');
              }}
              className="flex-1 bg-gray-700 text-gray-300 py-2 rounded text-xs hover:bg-gray-600 cursor-pointer"
            >
              수정할게요
            </button>
          </div>
        </div>
      </div>
    );
  };

  const handleConfirmVerification = async () => {
    if (!currentCaseId) {
      return;
    }
    setLoading(true);
    try {
      // 1. PATCH /cases/{case_id}/extracted-info 에 검수 수정된 데이터 전송
      await api.patch(`/api/v1/cases/${currentCaseId}/extracted-info`, {
        disease_kcd: extractedInfo.disease_kcd,
        disease_name: extractedInfo.disease_name,
        surgery: extractedInfo.surgery,
        diag_days: extractedInfo.current_days,
        current_days: extractedInfo.current_days,
        policy_elapsed_days: extractedInfo.policy_elapsed_days,
      });

      // 2. POST /analysis/search 로 RAG 분석 시작
      const resAnalysis = await api.post('/api/v1/analysis/search', { case_id: currentCaseId });
      if (resAnalysis.data.success) {
        setAnalysisResults(resAnalysis.data.data.results);
        setAnalysisSummary(resAnalysis.data.data.summary);
      }

      // 3. POST /reports 로 최종 보고서 생성
      const resReportCreate = await api.post('/api/v1/reports', { case_id: currentCaseId });
      if (resReportCreate.data.success) {
        const reportId = resReportCreate.data.data.report_id;
        // 4. GET /reports/{id} 로 보고서 디테일 조회
        const resReport = await api.get(`/api/v1/reports/${reportId}`);
        if (resReport.data.success) {
          setReport(resReport.data.data.body);

          // 5. 조건별 비교 데이터 로드 (POST /analysis/compare)
          const compareScenarios =
            serviceType === 'CASE2'
              ? [
                  { days: extractedInfo.current_days, name: `현재 입원 (${extractedInfo.current_days}일)` },
                  { days: extractedInfo.diag_days, name: `의사 권고 (${extractedInfo.diag_days}일)` },
                ]
              : [
                  { days: 3, name: '통상입원 (3일)' },
                  { days: 14, name: '장기입원 (14일)' },
                  { days: 30, name: '집중입원 (30일)' },
                ];

          const compareRes = await api.post('/api/v1/analysis/compare', {
            case_id: currentCaseId,
            scenarios: compareScenarios,
          });
          if (compareRes.data.success) {
            setCompareData(compareRes.data.data);
          }

          setStep(2); // 분석 완료 레이아웃으로 변경!
        }
      }
    } catch (err: unknown) {
      console.error(err);
      alert('분석을 시작하는 데 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitInput = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) {
      return;
    }

    if (inputMethod === 'PAYMENT' && currentCaseId) {
      const userText = inputValue;
      setChatMessages(prev => [
        ...prev,
        { id: Math.random().toString(), sender: 'user', text: userText, timestamp: new Date() },
      ]);
      setInputValue('');
      handleSendPaymentText(userText);
    } else {
      handleSendSituation(inputValue);
    }
  };

  // ── Helper: 챗봇 대화 리셋 ──
  const handleReset = () => {
    setStep(0);
    setServiceType('CASE1');
    setPresets([]);
    setSelectedPresets([]);
    setChatMessages([]);
    setCurrentCaseId(null);
    setInputMethod(null);
    setReport(null);
    setAnalysisResults([]);
    setSelectedCover(null);
    setCompareData(null);
    fetchPresets();
  };

  // ── Render ──
  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-logo">
          <span className="logo-spark">✨</span>
          <h1 className="logo-title">
            보험금 놓치지 마세요! <span className="logo-sub">AI 약관 보장분석</span>
          </h1>
        </div>
        <button onClick={handleReset} className="btn-reset">
          🔄 처음부터 다시 분석
        </button>
      </header>

      {/* Main Panel */}
      <div className="main-content">
        {step === 0 && (
          /* Step 0: 가입 보험 설정 */
          <div className="panel-preset">
            <div className="preset-card glass">
              <h2 className="preset-title">보장 분석을 위한 내 가입 보험 설정</h2>
              <p className="preset-desc">
                분석할 서비스 종류를 선택하고, 가입하신 보험 상품을 등록해주세요. 해당 약관의 원문 데이터를 기반으로 특약을 분석합니다.
              </p>

              {/* 서비스 유형 선택 */}
              <div className="section-label">1. 분석 서비스 유형 선택</div>
              <div className="service-select-container">
                <div
                  className={`service-card glass ${serviceType === 'CASE1' ? 'selected' : ''}`}
                  onClick={() => handleSelectServiceType('CASE1')}
                >
                  <div className="service-card-radio"></div>
                  <div className="service-card-header">
                    <span className="service-card-icon">🔍</span>
                    <h3 className="service-card-title">청구가능보험 찾기 (CASE1)</h3>
                  </div>
                  <p className="service-card-desc">
                    다중 보험 교차 검색 및 결제내역/세부산정내역서 기반 지급 가능 특약 탐색
                  </p>
                </div>
                <div
                  className={`service-card glass ${serviceType === 'CASE2' ? 'selected' : ''}`}
                  onClick={() => handleSelectServiceType('CASE2')}
                >
                  <div className="service-card-radio"></div>
                  <div className="service-card-header">
                    <span className="service-card-icon">📊</span>
                    <h3 className="service-card-title">추가보장 비교 (CASE2)</h3>
                  </div>
                  <p className="service-card-desc">
                    단일 보험 입원기간·가입기간 비교 및 시뮬레이션 기반 추가 보장 탐색 (보험 1개 제한)
                  </p>
                </div>
              </div>

              <div className="section-label">2. 내 가입 보험 상품 선택</div>
              {loading ? (
                <div className="loader-container">
                  <div className="spinner"></div>
                  <p>약관 정보를 준비하고 있습니다...</p>
                </div>
              ) : (
                <div className="presets-grid">
                  {presets.map(p => {
                    const isSelected = selectedPresets.includes(p.id);
                    return (
                      <div
                        key={p.id}
                        onClick={() => handleTogglePreset(p.id)}
                        className={`preset-item glass ${isSelected ? 'selected' : ''}`}
                      >
                        <div className="preset-checkbox">{isSelected ? '✓' : ''}</div>
                        <div className="preset-info">
                          <span className="preset-insurer">{p.insurer}</span>
                          <h3 className="preset-name">{p.name}</h3>
                          <span className="preset-type">{p.type}형</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <button
                onClick={handleRegisterPolicies}
                className="btn-primary mt-6 cursor-pointer"
                disabled={selectedPresets.length === 0}
              >
                가입 등록 완료 및 분석 챗봇 시작
              </button>
            </div>
          </div>
        )}

        {step === 1 && (
          /* Step 1: 챗봇 진행 */
          <div className="panel-chat w-full max-w-2xl mx-auto">
            <div className="chat-container glass">
              <div className="chat-body">
                {chatMessages.map(msg => (
                  <div key={msg.id} className={`chat-bubble-row ${msg.sender}`}>
                    <div className="bubble glass">
                      <div className="bubble-text">{msg.text}</div>
                      {msg.actions && <div className="bubble-actions">{msg.actions}</div>}
                    </div>
                    <span className="bubble-time">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
                {loading && (
                  <div className="chat-bubble-row bot">
                    <div className="bubble glass loading-bubble">
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <span className="dot"></span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSubmitInput} className="chat-footer">
                <input
                  type="text"
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  placeholder={
                    inputMethod === 'PAYMENT'
                      ? '결제내역 문자 텍스트를 적어주세요...'
                      : '치료 상황이나 아픈 곳을 적어주세요...'
                  }
                  className="chat-input"
                />
                <button type="submit" className="chat-send-btn cursor-pointer">
                  전송
                </button>
              </form>
            </div>
          </div>
        )}

        {step === 2 && report && (
          /* Step 2: 분석완료 결과 보드 */
          <div className="panel-report">
            {/* Left Chatbot Pane (For context continuity) */}
            <div className="report-chat-pane glass">
              <div className="chat-mini-header">
                <h3>💬 분석 상담 챗봇</h3>
              </div>
              <div className="chat-mini-body">
                <div className="chat-bubble-row bot">
                  <div className="bubble glass">
                    <div className="bubble-text">
                      분석이 완료되었습니다! 우측 결과 보드에서 청구 가능한 보장과 상세 약관 원문
                      근거를 확인해 보세요.
                    </div>
                  </div>
                </div>
                <div className="chat-bubble-row user">
                  <div className="bubble glass">
                    <div className="bubble-text">
                      질환: {report.summary.disease_name} ({report.summary.disease_kcd})<br />
                      입원일수: {report.summary.current_days || 0}일<br />
                      수술여부: {report.summary.surgery ? '예' : '아니오'}
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-gray-700/50">
                <button
                  onClick={handleReset}
                  className="w-full bg-accent text-white font-bold py-2 rounded-xl text-sm cursor-pointer"
                >
                  🔄 새로운 질환 분석하기
                </button>
              </div>
            </div>

            {/* Right Report Visualization Board */}
            <div className="report-board-pane glass">
              {/* Summary Metrics */}
              <div className="board-metrics">
                <div className="metric-box orange-glow">
                  <span className="metric-title">💡 놓치고 있는 보험금</span>
                  <span className="metric-value">{analysisSummary.missed_count}건</span>
                </div>
                <div className="metric-box purple-glow">
                  <span className="metric-title">📋 지급 가능성이 높은 보장</span>
                  <span className="metric-value">{analysisSummary.eligible_count}건</span>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="board-tabs border-b border-gray-700">
                <button
                  onClick={() => {
                    setActiveTab('eligible');
                    setSelectedCover(null);
                  }}
                  className={`tab-btn ${activeTab === 'eligible' ? 'active' : ''}`}
                >
                  지급 가능 보장 ({analysisResults.filter(x => x.status === 'eligible').length})
                </button>
                <button
                  onClick={() => {
                    setActiveTab('missed');
                    setSelectedCover(null);
                  }}
                  className={`tab-btn ${activeTab === 'missed' ? 'active' : ''}`}
                >
                  놓친 보장 탐색 ({analysisResults.filter(x => x.missed).length})
                </button>
                {compareData && (
                  <button
                    onClick={() => {
                      setActiveTab('compare');
                      setSelectedCover(null);
                    }}
                    className={`tab-btn ${activeTab === 'compare' ? 'active' : ''}`}
                  >
                    📈 조건별 시나리오 비교
                  </button>
                )}
                <button
                  onClick={() => {
                    setActiveTab('checklist');
                    setSelectedCover(null);
                  }}
                  className={`tab-btn ${activeTab === 'checklist' ? 'active' : ''}`}
                >
                  📎 준비 서류 체크리스트
                </button>
              </div>

              {/* Tab Contents */}
              <div className="board-body">
                {activeTab === 'eligible' && (
                  <div className="covers-list">
                    {analysisResults.length === 0 ? (
                      <p className="text-gray-500 py-10">
                        지급 조건에 부합하는 보장이 발견되지 않았습니다.
                      </p>
                    ) : (
                      analysisResults.map((r, idx) => (
                        <div
                          key={idx}
                          onClick={() => setSelectedCover(r)}
                          className={`cover-card glass ${selectedCover?.rider === r.rider ? 'selected' : ''}`}
                        >
                          <div className="cover-header">
                            <span className="cover-policy">{r.policy}</span>
                            <span className={`cover-badge status-${r.status}`}>{r.status}</span>
                          </div>
                          <h3 className="cover-name">{r.rider}</h3>
                          {r.calc && (
                            <div className="cover-calc">
                              계산구조: <code>{r.calc}</code>
                            </div>
                          )}
                          {r.gap_days && (
                            <div className="text-xs text-orange-400 font-semibold mt-1">
                              경계 도달 1일 미달! (+{r.gap_days}일 부족)
                            </div>
                          )}
                          <p className="cover-explanation">{r.explanation}</p>
                          <div className="cover-meta">
                            <span>{r.evidence.article}</span>
                            <span>•</span>
                            <span>{r.evidence.page}페이지</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {activeTab === 'missed' && (
                  <div className="covers-list">
                    {analysisResults.filter(x => x.missed).length === 0 ? (
                      <p className="text-gray-500 py-10">놓치고 있는 보험금이 없습니다.</p>
                    ) : (
                      analysisResults
                        .filter(x => x.missed)
                        .map((r, idx) => (
                          <div
                            key={idx}
                            onClick={() => setSelectedCover(r)}
                            className={`cover-card glass orange-border ${selectedCover?.rider === r.rider ? 'selected' : ''}`}
                          >
                            <div className="cover-header">
                              <span className="cover-policy text-orange-400">{r.policy}</span>
                              <span className="cover-badge status-missed">놓치고 있는 보험금</span>
                            </div>
                            <h3 className="cover-name">{r.rider}</h3>
                            <p className="cover-explanation">{r.explanation}</p>
                            <div className="cover-meta">
                              <span>{r.evidence.article}</span>
                              <span>•</span>
                              <span>{r.evidence.page}페이지</span>
                            </div>
                          </div>
                        ))
                    )}
                  </div>
                )}

                {activeTab === 'compare' && compareData && (
                  <div className="compare-pane">
                    <h3 className="pane-title">📊 입원 일수에 따른 보장 가능성 변동 비교</h3>
                    <p className="pane-desc">
                      치료 조건(입원 일수 등) 변동 시 각 약관 보장의 지급 금액 및 판정 결과가 어떻게
                      바뀌는지 추적합니다.
                    </p>
                    <div className="compare-table-wrapper">
                      <table className="compare-table">
                        <thead>
                          <tr>
                            <th>보험사/특약</th>
                            {compareData.scenarios.map((sc: Scenario, i: number) => (
                              <th key={i}>{sc.name}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {compareData.comparisons.map((c: Comparison, i: number) => (
                            <tr key={i}>
                              <td className="font-semibold text-left">
                                <div className="text-xs text-gray-500">{c.policy}</div>
                                <div className="text-sm text-gray-200">{c.rider}</div>
                              </td>
                              {c.outcomes.map((out: Outcome, j: number) => (
                                <td key={j}>
                                  <span className={`outcome-badge status-${out.status}`}>
                                    {out.status}
                                  </span>
                                  {out.calc && (
                                    <div className="text-xs text-gray-400 mt-1 font-mono">
                                      {out.calc}
                                    </div>
                                  )}
                                  {out.gap_days && (
                                    <div className="text-xs text-orange-400 mt-1 font-bold">
                                      1일 부족 (경계미달)
                                    </div>
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {activeTab === 'checklist' && report && (
                  <div className="checklist-pane">
                    <h3 className="pane-title">📎 필요 서류 및 체크리스트</h3>
                    <p className="pane-desc">
                      보험금 청구 시 원활한 지급 청구를 위한 구비서류 목록입니다.
                    </p>
                    <div className="checklist-list">
                      {report.checklist.map((item: ChecklistItem, idx: number) => (
                        <div key={idx} className="checklist-item glass">
                          <input
                            type="checkbox"
                            id={`chk-${idx}`}
                            className="accent-accent w-4 h-4 cursor-pointer"
                          />
                          <label
                            htmlFor={`chk-${idx}`}
                            className="text-sm text-gray-300 select-none cursor-pointer"
                          >
                            {item.task}
                          </label>
                        </div>
                      ))}
                    </div>
                    <div className="statute-box glass mt-6">
                      <h4 className="font-bold text-accent text-sm mb-1">⏳ 소멸시효 유의</h4>
                      <p className="text-xs text-gray-400 leading-relaxed">
                        {report.statute_of_limitations}
                      </p>
                    </div>
                  </div>
                )}

                {/* Evidence Panel (Shows when a cover is clicked) */}
                {selectedCover && (
                  <div className="evidence-panel glass">
                    <div className="evidence-header">
                      <h4 className="evidence-title">🔍 약관 원문 근거 판독</h4>
                      <button onClick={() => setSelectedCover(null)} className="evidence-close">
                        ✕
                      </button>
                    </div>
                    <div className="evidence-meta">
                      <span className="meta-article">{selectedCover.evidence.article}</span>
                      <span className="meta-page">{selectedCover.evidence.page} 페이지</span>
                    </div>
                    <div className="evidence-quote-box">
                      <div className="quote-label">📜 약관 원문 인용</div>
                      <blockquote className="quote-content">
                        "{selectedCover.evidence.quote}"
                      </blockquote>
                    </div>
                    <p className="evidence-desc">
                      <span className="font-semibold text-accent">AI 판독:</span>{' '}
                      {selectedCover.explanation}
                    </p>
                  </div>
                )}
              </div>

              {/* Disclaimer */}
              <div className="board-disclaimer">
                <p>⚠️ {report.disclaimer}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
