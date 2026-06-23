"""테스트용 단일 페이지 웹 서비스 클라이언트 (지수).

프론트엔드 담당자와 독립적으로 백엔드 RAG 파이프라인 및 청구 판정 플로우를 직접 검증해볼 수 있는
미려한 다크 모드 웹 데모 인터페이스를 /test-ui 로 제공합니다. 언제든 이 파일과 블루프린트 등록만 지우면 완전 삭제가 가능합니다.
"""

from flask import Response
from flask_openapi3.blueprint import APIBlueprint
from flask_openapi3.models.tag import Tag

bp = APIBlueprint("test_ui", __name__, abp_tags=[Tag(name="test_ui")])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 보험 보장 분석 서비스 - 테스트 클라이언트</title>
    <link rel="icon" href="data:,">
    <!-- Modern Outfits & Inter Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: hsl(224, 71%, 4%);
            --bg-sidebar: hsl(222, 47%, 11%);
            --bg-card: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-color: #3b82f6;
            --accent-gradient: linear-gradient(135deg, #6366f1, #3b82f6);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-success: #10b981;
            --text-warning: #f59e0b;
            --text-danger: #ef4444;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            overflow-x: hidden;
            height: 100vh;
        }

        h1, h2, h3, h4, .font-outfit {
            font-family: 'Outfit', sans-serif;
        }

        /* Layout styles */
        #app-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 2rem;
            background-color: var(--bg-sidebar);
            border-bottom: 1px solid var(--border-color);
            z-index: 10;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .logo-spark {
            font-size: 1.5rem;
        }

        .logo-title {
            font-size: 1.25rem;
            font-weight: 600;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-sub {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-left: 0.5rem;
            border: 1px solid var(--border-color);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
        }

        .btn-restart {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        .btn-restart:hover {
            color: var(--text-main);
            border-color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
        }

        .main-layout {
            display: flex;
            flex: 1;
            height: calc(100vh - 65px);
            overflow: hidden;
        }

        /* Screen Step 0: Preset Select */
        #step-preset {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            overflow-y: auto;
        }

        .preset-card-container {
            max-width: 800px;
            width: 100%;
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            text-align: center;
        }

        .preset-title {
            font-size: 1.75rem;
            margin-bottom: 0.75rem;
            font-weight: 700;
        }

        .preset-desc {
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-bottom: 2rem;
        }

        .presets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }

        .preset-item {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: left;
            cursor: pointer;
            transition: all 0.25s ease;
            position: relative;
            user-select: none;
        }

        .preset-item:hover {
            transform: translateY(-2px);
            border-color: rgba(59, 130, 246, 0.4);
        }

        .preset-item.selected {
            border-color: var(--accent-color);
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
            background: rgba(59, 130, 246, 0.05);
        }

        .preset-insurer {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 600;
            display: block;
            margin-bottom: 0.25rem;
        }

        .preset-name {
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }

        .preset-tag {
            font-size: 0.7rem;
            background: rgba(255, 255, 255, 0.08);
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            color: var(--text-muted);
        }

        .preset-checkbox {
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 18px;
            height: 18px;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .preset-item.selected .preset-checkbox {
            background: var(--accent-color);
            border-color: var(--accent-color);
        }

        .preset-item.selected .preset-checkbox::after {
            content: "✓";
            color: white;
            font-size: 0.7rem;
            font-weight: bold;
        }

        .btn-preset-submit {
            background: var(--accent-gradient);
            color: white;
            border: none;
            padding: 0.85rem 2.5rem;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            transition: opacity 0.2s;
        }

        .btn-preset-submit:hover {
            opacity: 0.9;
        }

        /* Screen Step 1-2 Layout */
        #step-main {
            display: flex;
            flex: 1;
            height: 100%;
            width: 100%;
        }

        /* Left Side: Chatbot */
        .chat-panel {
            width: 450px;
            border-right: 1px solid var(--border-color);
            background-color: var(--bg-sidebar);
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .chat-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chat-header h3 {
            font-size: 1.05rem;
            font-weight: 600;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .msg-bubble {
            max-width: 85%;
            padding: 0.85rem 1.15rem;
            border-radius: 16px;
            line-height: 1.5;
            font-size: 0.9rem;
            word-break: break-all;
            white-space: pre-line;
            animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(10px);
        }

        @keyframes slideUp {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .msg-bot {
            align-self: flex-start;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            border-top-left-radius: 2px;
        }

        .msg-user {
            align-self: flex-end;
            background: var(--accent-gradient);
            color: white;
            border-top-right-radius: 2px;
        }

        .msg-actions {
            margin-top: 0.75rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .msg-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: var(--text-main);
            padding: 0.4rem 0.85rem;
            border-radius: 20px;
            font-size: 0.78rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .msg-btn:hover {
            background: rgba(255, 255, 255, 0.18);
        }

        .msg-btn-primary {
            background: var(--accent-color);
            border-color: var(--accent-color);
            color: white;
        }

        .msg-btn-primary:hover {
            opacity: 0.9;
        }

        .chat-input-area {
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border-color);
            background: rgba(15, 23, 42, 0.4);
        }

        .chat-input-form {
            display: flex;
            gap: 0.75rem;
        }

        .chat-input {
            flex: 1;
            background: var(--bg-base);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.75rem 1rem;
            border-radius: 10px;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: var(--accent-color);
        }

        .chat-send-btn {
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 0 1.25rem;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: opacity 0.2s;
        }

        .chat-send-btn:hover {
            opacity: 0.9;
        }

        /* Right Side: Dashboard & Report */
        .dashboard-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            background-color: var(--bg-base);
        }

        .empty-dashboard {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            text-align: center;
            padding: 2rem;
        }

        .empty-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.6;
        }

        .report-tabs {
            display: flex;
            background: var(--bg-sidebar);
            border-bottom: 1px solid var(--border-color);
            padding: 0 1.5rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 1rem 1.25rem;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            color: var(--accent-color);
            border-bottom-color: var(--accent-color);
            font-weight: 600;
        }

        .report-content {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
        }

        .report-header-summary {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .summary-card {
            flex: 1;
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .summary-val {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent-color);
        }

        .summary-val.missed {
            color: var(--text-warning);
        }

        .summary-lbl {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        /* Coverage Cards Grid */
        .coverages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
        }

        .coverage-card {
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .coverage-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .coverage-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .coverage-insurer {
            font-size: 0.72rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .coverage-status {
            font-size: 0.72rem;
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            font-weight: 600;
        }

        .status-eligible { background: rgba(16, 185, 129, 0.12); color: var(--text-success); }
        .status-claimed { background: rgba(148, 163, 184, 0.12); color: var(--text-muted); }
        .status-boundary_not_met { background: rgba(245, 158, 11, 0.12); color: var(--text-warning); }
        .status-waiting_period_not_met { background: rgba(239, 68, 68, 0.12); color: var(--text-danger); }
        .status-potential { background: rgba(99, 102, 241, 0.12); color: #818cf8; }

        .coverage-name {
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
        }

        .coverage-calc {
            background: rgba(0, 0, 0, 0.2);
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .coverage-calc-val {
            color: var(--text-main);
            font-weight: 600;
            margin-top: 0.15rem;
        }

        .coverage-click-tip {
            font-size: 0.72rem;
            color: var(--accent-color);
            text-align: right;
            margin-top: auto;
        }

        /* Compare View Styles */
        .compare-header {
            background: rgba(59, 130, 246, 0.06);
            border: 1px solid rgba(59, 130, 246, 0.15);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 2rem;
            font-size: 0.85rem;
            line-height: 1.5;
        }

        .compare-table-wrapper {
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
        }

        .compare-table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }

        .compare-table th, .compare-table td {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border-color);
        }

        .compare-table th {
            background: rgba(255, 255, 255, 0.02);
            color: var(--text-muted);
            font-weight: 600;
        }

        .compare-table tr:last-child td {
            border-bottom: none;
        }

        .compare-status-badge {
            display: inline-block;
            font-size: 0.7rem;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            font-weight: 600;
        }

        .compare-boundary-highlight {
            color: var(--text-warning);
            font-size: 0.75rem;
            display: block;
            margin-top: 0.25rem;
        }

        /* Checklist View Styles */
        .checklist-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .checklist-section {
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
        }

        .checklist-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        .checklist-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0;
            font-size: 0.9rem;
            color: var(--text-main);
        }

        .checklist-cb {
            width: 16px;
            height: 16px;
            accent-color: var(--accent-color);
            cursor: pointer;
        }

        /* Lower Disclaimer & Limit Note */
        .disclaimer-area {
            margin-top: 3rem;
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
            color: var(--text-muted);
            font-size: 0.78rem;
            line-height: 1.6;
        }

        .disclaimer-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--text-main);
        }

        /* Modal Details */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }

        .modal.show {
            opacity: 1;
            pointer-events: auto;
        }

        .modal-card {
            background: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            width: 90%;
            max-width: 600px;
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            max-height: 80vh;
        }

        .modal-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            font-size: 1.15rem;
            font-weight: 600;
        }

        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
        }

        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .modal-sec-title {
            font-weight: 600;
            color: var(--text-muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }

        .modal-quote-box {
            background: var(--bg-base);
            border-left: 3px solid var(--accent-color);
            padding: 1rem;
            border-radius: 4px;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            color: #cbd5e1;
        }

        /* Verification Form Styling */
        .verify-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            padding: 1rem;
            border-radius: 12px;
            margin-top: 0.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .verify-form-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .verify-form-group label {
            font-size: 0.72rem;
            color: var(--text-muted);
        }

        .verify-input {
            background: var(--bg-base);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
            font-size: 0.8rem;
            outline: none;
        }

        .verify-checkbox-area {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
        }

        /* Loading Spinner */
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border-left-color: var(--accent-color);
            animation: spin 1s linear infinite;
            display: inline-block;
            vertical-align: middle;
            margin-right: 0.5rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .service-card {
            background-color: var(--bg-sidebar);
            border: 1px solid var(--border-color);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .service-card:hover {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.25);
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <div id="app-container">
        <!-- Header -->
        <header>
            <div class="logo-area">
                <span class="logo-spark">✨</span>
                <h1 class="logo-title">보험금 놓치지 마세요! <span class="logo-sub">AI 약관 보장분석</span></h1>
            </div>
            <button onclick="handleRestart()" class="btn-restart">🔄 처음부터 다시 분석</button>
        </header>

        <!-- Main Body -->
        <div class="main-layout">
            <!-- Step -1: Service Type Selection (Home) -->
            <div id="step-service">
                <div class="preset-card-container glass" style="max-width: 800px; text-align: center; margin: 4rem auto;">
                    <h2 class="preset-title" style="margin-bottom: 0.5rem; font-size: 1.75rem;">원하시는 보장 분석 서비스를 선택해주세요</h2>
                    <p class="preset-desc" style="margin-bottom: 2.5rem; font-size: 0.95rem;">약관 원문 데이터를 기반으로 AI RAG 분석을 진행합니다.</p>
                    
                    <div style="display: flex; gap: 1.5rem; justify-content: center; margin-bottom: 1.5rem;">
                        <!-- CASE 1 Card -->
                        <div onclick="selectService('CASE1')" class="service-card glass" style="flex: 1; padding: 2.5rem 2rem; border-radius: 12px; cursor: pointer; transition: all 0.3s ease;">
                            <span style="font-size: 3rem; display: block; margin-bottom: 1rem;">🔍</span>
                            <h3 style="font-size: 1.35rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-main);">CASE 1</h3>
                            <p style="font-size: 0.9rem; color: var(--text-muted);">청구가능보험 찾기</p>
                        </div>
                        <!-- CASE 2 Card -->
                        <div onclick="selectService('CASE2')" class="service-card glass" style="flex: 1; padding: 2.5rem 2rem; border-radius: 12px; cursor: pointer; transition: all 0.3s ease;">
                            <span style="font-size: 3rem; display: block; margin-bottom: 1rem;">⚖️</span>
                            <h3 style="font-size: 1.35rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-main);">CASE 2</h3>
                            <p style="font-size: 0.9rem; color: var(--text-muted);">추가보장 비교</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step 0: Presets selection -->
            <div id="step-preset" style="display: none;">
                <div class="preset-card-container glass">
                    <h2 class="preset-title">보장 분석을 위한 내 가입 보험 설정</h2>
                    <p class="preset-desc">가지고 계신 보험 상품을 선택해주세요. 해당 약관의 원문 데이터를 기반으로 숨겨진 청구 보장 및 특약을 RAG 탐색합니다.</p>
                    
                    <div class="presets-grid" id="presets-container">
                        <!-- Presets dynamically loaded here -->
                        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">
                            <span class="spinner"></span> 프리셋 로드 중...
                        </div>
                    </div>

                    <button id="btn-preset-submit" onclick="submitPresets()" class="btn-preset-submit">보험 등록 및 챗봇 실행</button>
                </div>
            </div>

            <!-- Step 1 & 2: Chat & Result Dashboard (Initially Hidden) -->
            <div id="step-main" style="display: none;">
                <!-- Left Chat Sidebar -->
                <div class="chat-panel">
                    <div class="chat-header">
                        <span style="font-size:1.2rem;">💬</span>
                        <h3>분석 챗봇 인터페이스</h3>
                    </div>
                    
                    <div class="chat-messages" id="chat-messages">
                        <!-- Message Bubbles -->
                    </div>

                    <div class="chat-input-area">
                        <form class="chat-input-form" id="chat-form" onsubmit="handleSendText(event)">
                            <input 
                                type="text" 
                                class="chat-input" 
                                id="chat-input-field" 
                                placeholder="치료 상황을 말해보세요 (예: '뇌경색 3일 입원')" 
                                autocomplete="off"
                            >
                            <button type="submit" class="chat-send-btn">전송</button>
                        </form>
                    </div>
                </div>

                <!-- Right Dashboard Report View -->
                <div class="dashboard-panel">
                    <!-- Dashboard Empty State -->
                    <div class="empty-dashboard" id="empty-dashboard">
                        <span class="empty-icon">📊</span>
                        <h3>분석 완료 후 분석 리포트가 표시됩니다.</h3>
                        <p style="font-size:0.85rem; margin-top:0.25rem;">챗봇 대화를 진행하고 [분석 실행]을 완료해 주세요.</p>
                    </div>

                    <!-- Dashboard Loaded Content -->
                    <div id="dashboard-content" style="display: none; flex: 1; flex-direction: column; overflow: hidden;">
                        <div class="report-tabs">
                            <button class="tab-btn active" onclick="switchTab('eligible')">👍 청구 가능 보장</button>
                            <button class="tab-btn" onclick="switchTab('missed')">🚨 놓쳤을 보장</button>
                            <button class="tab-btn" onclick="switchTab('compare')">📅 퇴원 시점 비교</button>
                            <button class="tab-btn" onclick="switchTab('checklist')">📋 필요 서류 Checklist</button>
                        </div>

                        <div class="report-content">
                            <!-- Summary Counters -->
                            <div class="report-header-summary">
                                <div class="summary-card">
                                    <span class="summary-val" id="summary-eligible-count">0</span>
                                    <span class="summary-lbl">청구 가능 특약 수 (기청구 포함)</span>
                                </div>
                                <div class="summary-card">
                                    <span class="summary-val missed" id="summary-missed-count">0</span>
                                    <span class="summary-lbl">미청구(놓쳤을 가능성) 특약 수</span>
                                </div>
                            </div>

                            <!-- Tab 1: Eligible -->
                            <div id="tab-pane-eligible" class="tab-pane">
                                <h3 style="margin-bottom: 1rem; font-size:1.1rem;">약관 기준 청구 대상에 해당합니다</h3>
                                <div class="coverages-grid" id="eligible-cards"></div>
                            </div>

                            <!-- Tab 2: Missed -->
                            <div id="tab-pane-missed" class="tab-pane" style="display: none;">
                                <h3 style="margin-bottom: 1rem; font-size:1.1rem; color: var(--text-warning);">놓치고 계실 가능성이 높은 보장입니다</h3>
                                <div class="coverages-grid" id="missed-cards"></div>
                            </div>

                            <!-- Tab 3: Compare -->
                            <div id="tab-pane-compare" class="tab-pane" style="display: none;">
                                <div class="compare-header">
                                    <strong>💡 의학적 진단 기간 기준 안내</strong><br>
                                    과잉 입원을 방지하기 위해, 모든 보장 비교의 기준 전제는 "의사가 진단한 치료 입원 기간"입니다.<br>
                                    퇴원 시점에 따른 보장 차이를 파악하여 올바른 치료 의사결정에 참고해 주세요.
                                </div>
                                <div class="compare-table-wrapper">
                                    <table class="compare-table">
                                        <thead>
                                            <tr>
                                                <th>보험상품 / 특약명</th>
                                                <th>단기 퇴원 (3일)</th>
                                                <th>일반 퇴원 (14일)</th>
                                                <th>장기 퇴원 (30일)</th>
                                            </tr>
                                        </thead>
                                        <tbody id="compare-table-rows">
                                            <!-- Compare rows loaded dynamically -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Tab 4: Checklist -->
                            <div id="tab-pane-checklist" class="tab-pane" style="display: none;">
                                <div class="checklist-container" id="checklist-items">
                                    <!-- Checklist loaded dynamically -->
                                </div>
                            </div>

                            <!-- Disclaimer Common Area -->
                            <div class="disclaimer-area">
                                <p class="disclaimer-title">⚠️ 면책고지 및 유의사항</p>
                                <p>본 분석 결과는 가입자가 제출한 정보와 약관 텍스트를 기준으로 RAG 및 룰 엔진이 자동 매칭하여 산출한 약관 기준의 예시값입니다. 실제 보험금 지급 여부와 정확한 지급 금액은 각 보험사의 정밀 심사 결과에 따라 달라질 수 있습니다. 보험금 청구의 소멸시효 기한은 사고일(또는 진단 확정일)로부터 3년입니다.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Coverage Quote Modal -->
    <div class="modal" id="quote-modal">
        <div class="modal-card">
            <div class="modal-header">
                <h3 id="modal-rider-name">특약 상세 정보</h3>
                <button onclick="closeModal()" class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div>
                    <div class="modal-sec-title">가입 보험 상품</div>
                    <div id="modal-policy-name" style="font-weight:600;">-</div>
                </div>
                <div>
                    <div class="modal-sec-title font-outfit">판정 결과 및 설명</div>
                    <div id="modal-explanation" style="font-size:0.92rem; color: #f1f5f9; background: rgba(255,255,255,0.03); padding:0.85rem; border-radius:6px;">-</div>
                </div>
                <div>
                    <div class="modal-sec-title">약관 근거 조항 정보</div>
                    <div id="modal-evidence-article" style="font-weight:600;">-</div>
                </div>
                <div>
                    <div class="modal-sec-title">약관 원문 인용 (100% 검증)</div>
                    <div class="modal-quote-box" id="modal-evidence-quote">-</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Frontend JS logic -->
    <script>
        // Global variables
        const API_BASE = "/api/v1";
        const dummyToken = "Bearer test-token";
        let activeCaseId = null;
        let selectedPresetIds = [];
        let serviceType = 'CASE1';

        // Chatbot state control variables for sequential flow
        let inputMethodSelected = false;
        let tempPaymentAmount = null;
        let tempPaymentDate = null;
        let tempHospitalName = null;
        let tempInferredVisitType = null;
        let tempVisitTypeInferred = false;

        function changeServiceType(type) {
            serviceType = type;
            selectedPresetIds = [];
            document.querySelectorAll('.preset-item').forEach(el => el.classList.remove('selected'));
        }
        let curStep = 0;
        let analysisData = null;

        // Chatbot multi-turn interactive variables
        let chatbotQuestions = [];
        let currentQuestionIndex = 0;
        let globalTreatmentTypes = [];

        // On document load
        window.addEventListener('DOMContentLoaded', () => {
            // 로드 시에는 홈(step-service)만 보여주고 대기
        });

        function selectService(type) {
            serviceType = type;
            document.getElementById('step-service').style.display = 'none';
            document.getElementById('step-preset').style.display = 'flex';
            
            const desc = document.querySelector('#step-preset .preset-desc');
            if (desc) {
                if (serviceType === 'CASE1') {
                    desc.innerText = '가지고 계신 보험 상품을 여러 개 선택해주세요. 해당 약관의 원문 데이터를 기반으로 숨겨진 청구 보장 및 특약을 RAG 탐색합니다.';
                } else {
                    desc.innerText = '비교 분석할 보험 상품 1개를 선택해주세요. 해당 약관의 보장 한도와 타 플랜 추가 보장을 상세 분석합니다.';
                }
            }
            loadPresets();
        }

        // Request helper
        async function fetchAPI(endpoint, options = {}) {
            const url = API_BASE + endpoint;
            const headers = {
                'Authorization': dummyToken,
                'Content-Type': 'application/json',
                ...(options.headers || {})
            };
            if (options.body && !(options.body instanceof FormData)) {
                options.body = JSON.stringify(options.body);
            }
            
            const response = await fetch(url, { ...options, headers });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'API request failed');
            }
            return data;
        }

        // Load presets
        async function loadPresets() {
            try {
                console.log("[loadPresets] Fetching presets...");
                const res = await fetchAPI('/policies/presets');
                console.log("[loadPresets] Response:", res);
                if (res.success && res.data && res.data.presets) {
                    const container = document.getElementById('presets-container');
                    container.innerHTML = '';
                    console.log("[loadPresets] Presets array length:", res.data.presets.length);
                    res.data.presets.forEach(p => {
                        const div = document.createElement('div');
                        div.className = 'preset-item';
                        div.onclick = () => togglePreset(p.id, div);
                        div.innerHTML = `
                            <span class="preset-insurer">${p.insurer}</span>
                            <h3 class="preset-name">${p.name}</h3>
                            <span class="preset-tag">${p.type}</span>
                            <div class="preset-checkbox"></div>
                        `;
                        container.appendChild(div);
                    });
                }
            } catch (err) {
                console.error(err);
                document.getElementById('presets-container').innerHTML = `
                    <div style="color:var(--text-danger)">
                        보험 프리셋을 불러오지 못했습니다. 백엔드 서버 상태를 확인해 주세요.
                    </div>
                `;
            }
        }

        function togglePreset(id, element) {
            if (serviceType === 'CASE2') {
                selectedPresetIds = [id];
                document.querySelectorAll('.preset-item').forEach(el => el.classList.remove('selected'));
                element.classList.add('selected');
            } else {
                if (selectedPresetIds.includes(id)) {
                    selectedPresetIds = selectedPresetIds.filter(x => x !== id);
                    element.classList.remove('selected');
                } else {
                    selectedPresetIds.push(id);
                    element.classList.add('selected');
                }
            }
        }

        // Submit presets
        let isSubmittingPresets = false;
        async function submitPresets() {
            if (isSubmittingPresets) return;
            if (selectedPresetIds.length === 0) {
                alert('가입 보험을 최소 1개 이상 선택해 주세요.');
                return;
            }
            if (serviceType === 'CASE2' && selectedPresetIds.length > 1) {
                alert('CASE2 (추가보장 비교) 서비스는 1개의 보험 상품만 선택할 수 있습니다.');
                return;
            }

            const btn = document.getElementById('btn-preset-submit');
            if (btn) {
                btn.disabled = true;
                btn.innerText = '보험 등록 및 분석 세션 초기화 중...';
            }
            isSubmittingPresets = true;

            try {
                const res = await fetchAPI('/policies/select', {
                    method: 'POST',
                    body: { preset_ids: selectedPresetIds }
                });
                if (res.success) {
                    registeredPolicyIds = res.data.policy_ids;
                    document.getElementById('step-preset').style.display = 'none';
                    document.getElementById('step-main').style.display = 'flex';
                    curStep = 1;
                    
                    // Welcome bot message
                    if (serviceType === 'CASE1') {
                        addBotMessage(
                            '안녕하세요! 가입하신 보험을 바탕으로 청구 가능한 특약을 찾아 드릴게요. ' +
                            '지금 어떤 치료나 질환 상황을 겪으셨나요?\\n\\n' +
                            '(예: "뇌경색 입원했어요", "위암 진단받았습니다")'
                        );
                    } else {
                        addBotMessage(
                            '안녕하세요! 선택하신 보험의 상세 보장을 분석하고 다른 플랜과 추가 보장을 비교해 드릴게요. ' +
                            '지금 진단 경과나 입원 상황이 어떻게 되시나요?\\n\\n' +
                            '(예: "허리디스크 4주 진단에 2주차 입원치료 중입니다")'
                        );
                    }
                }
            } catch (err) {
                alert('보험 프리셋 설정에 실패했습니다: ' + err.message);
            } finally {
                isSubmittingPresets = false;
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = '보험 등록 및 챗봇 실행';
                }
            }
        }

        // Chat utilities
        function addBotMessage(text, actions = null) {
            const container = document.getElementById('chat-messages');
            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble msg-bot';
            bubble.innerHTML = text.replace(/\\n/g, '<br>');
            
            if (actions) {
                const actionDiv = document.createElement('div');
                actionDiv.className = 'msg-actions';
                actionDiv.innerHTML = actions;
                bubble.appendChild(actionDiv);
            }
            
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;
        }

        function addUserMessage(text) {
            const container = document.getElementById('chat-messages');
            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble msg-user';
            bubble.innerText = text;
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;
        }

        // Handle text submission in chat
        async function handleSendText(e) {
            e.preventDefault();
            const inputField = document.getElementById('chat-input-field');
            const text = inputField.value.trim();
            if (!text) return;

            addUserMessage(text);
            inputField.value = '';

            const isPaymentInput = inputField.dataset.mode === 'payment';
            const isPaymentEdit = inputField.dataset.mode === 'payment_edit';
            const isAnnualCountInput = inputField.dataset.mode === 'annual_visit_count';

            try {
                if (isPaymentInput) {
                    inputField.dataset.mode = ''; // Reset
                    inputField.placeholder = "치료 상황을 말해보세요 (예: '뇌경색 3일 입원')";
                    
                    // Post payment text
                    const res = await fetchAPI(`/cases/${activeCaseId}/payment`, {
                        method: 'POST',
                        body: { payment_text: text }
                    });
                    if (res.success) {
                        const payData = res.data;
                        globalTreatmentTypes = payData.treatment_types || [];
                        
                        // Store parsed data temporarily
                        tempPaymentAmount = payData.extracted_payment.payment_amount || 80000;
                        tempPaymentDate = payData.extracted_payment.payment_date || "2026-06-10";
                        tempHospitalName = payData.extracted_payment.hospital_name || "OO정형외과";

                        const inf = payData.visit_type_inference;
                        if (inf && inf.inferred) {
                            tempVisitTypeInferred = true;
                            tempInferredVisitType = inf.inferred_is_outpatient ? 'outpatient' : 'inpatient';
                        } else {
                            tempVisitTypeInferred = false;
                            tempInferredVisitType = null;
                        }

                        const dateFormatted = tempPaymentDate.replace(/-/g, '.');
                        const confirmHtml = `
                            <button onclick="confirmPaymentInfo(true)" class="msg-btn msg-btn-primary">맞아요</button>
                            <button onclick="confirmPaymentInfo(false)" class="msg-btn">수정할게요</button>
                        `;
                        addBotMessage(
                            `결제금액 ${tempPaymentAmount.toLocaleString()}원 / 접수일 ${dateFormatted}으로 확인됐어요. 맞나요?`,
                            confirmHtml
                        );
                    }
                } else if (isPaymentEdit) {
                    inputField.dataset.mode = ''; // Reset
                    inputField.placeholder = "치료 상황을 말해보세요 (예: '뇌경색 3일 입원')";
                    const amt = parseInt(text.replace(/[^0-9]/g, '')) || 80000;
                    tempPaymentAmount = amt;
                    confirmPaymentInfo(true); // Re-run with updated amount
                } else if (isAnnualCountInput) {
                    inputField.dataset.mode = ''; // Reset
                    inputField.placeholder = "치료 상황을 말해보세요 (예: '뇌경색 3일 입원')";
                    
                    const numMatch = text.match(/[0-9]+/);
                    const countVal = numMatch ? parseInt(numMatch[0]) : 1;
                    
                    const res = await fetchAPI(`/cases/${activeCaseId}/answers`, {
                        method: 'POST',
                        body: {
                            answers: [
                                { question_id: "annual_visit_count", value: countVal }
                            ]
                        }
                    });
                    if (res.success) {
                        globalTreatmentTypes = res.data.treatment_types || [];
                        if (res.data.case) {
                            rebuildQuestions(res.data.case);
                        }
                    }
                    currentQuestionIndex = 0;
                    askNextQuestion();
                } else {
                    // Normal Case Initial Situation Input
                    const res = await fetchAPI('/cases', {
                        method: 'POST',
                        body: {
                            service_type: serviceType,
                            policy_ids: selectedPresetIds,
                            initial_situation: text
                        }
                    });
                    
                    if (res.success) {
                        const c = res.data;
                        globalTreatmentTypes = c.treatment_types || [];
                        if (c.out_of_scope) {
                            addBotMessage(c.message, `
                                <button onclick="alert('지원 범위: 질병·암·실손·상해 관련 입원/수술/진단 특약. 자동차/화재/배상책임은 제외')" class="msg-btn">지원 범위 다시 보기</button>
                                <button onclick="handleRestart()" class="msg-btn msg-btn-primary">상황 다시 입력하기</button>
                            `);
                            return;
                        }

                        activeCaseId = c.case_id;
                        inputMethodSelected = false;
                        currentQuestionIndex = 0;
                        rebuildQuestions(c);
                        
                        setTimeout(() => {
                            askNextQuestion();
                        }, 500);
                    }
                }
            } catch (err) {
                addBotMessage('데이터 처리 중 오류가 발생했습니다: ' + err.message);
            }
        }

        // Rebuild dynamic questions list based on current case state
        function toggleSubGroup(id) {
            const panels = document.querySelectorAll('.sub-group-panel');
            panels.forEach(p => {
                if (p.id === id) {
                    p.style.display = p.style.display === 'none' ? 'block' : 'none';
                } else {
                    p.style.display = 'none';
                }
            });
        }

        function rebuildQuestions(c) {
            chatbotQuestions = [];

            // 1. Disease name & KCD code check
            if (!c.disease_name || !c.disease_kcd || c.disease_kcd === 'R69' || c.disease_match_confidence === 'need_user_confirmation') {
                let btnHtml = '';
                if (c.disease_kcd_candidates && c.disease_kcd_candidates.length > 0) {
                    c.disease_kcd_candidates.forEach((cand, idx) => {
                        btnHtml += `<button onclick="answerQuestion('disease', '${cand.name}', '${cand.kcd}')" class="msg-btn">${idx + 1}. ${cand.name} (${cand.kcd})</button> `;
                    });
                    btnHtml += `<button onclick="answerQuestion('disease', '상세불명 질환', 'R69')" class="msg-btn">해당 병명이 없어요</button>`;
                } else {
                    btnHtml = `
                        <button onclick="answerQuestion('disease', '뇌경색증', 'I63')" class="msg-btn">뇌경색증 (I63)</button>
                        <button onclick="answerQuestion('disease', '기타 추간판장애 (허리디스크)', 'M51')" class="msg-btn">허리디스크 (M51)</button>
                        <button onclick="answerQuestion('disease', '위암', 'C16')" class="msg-btn">위암 (C16)</button>
                    `;
                }

                chatbotQuestions.push({
                    type: 'disease',
                    text: '정확한 진단명을 알 수 있을까요? 아래 후보 중 선택하시거나, 없으시면 입력창에 직접 써주세요.',
                    actions: btnHtml
                });
                return;
            }

            // 2. 입력 방식 선택 및 영수증 정보 수집 (CASE1에만 해당)
            if (serviceType === 'CASE1' && !inputMethodSelected) {
                chatbotQuestions.push({
                    type: 'input_method',
                    text: `${c.disease_name}으로 확인했어요. 가지고 계신 자료로 확인할까요?`,
                    actions: `
                        <button onclick="selectInputMethodDirect('PAYMENT')" class="msg-btn msg-btn-primary">문자·카드내역으로 확인</button>
                        <button onclick="selectInputMethodDirect('STATEMENT')" class="msg-btn">진료비 세부산정내역서로 확인</button>
                    `
                });
                return;
            }

            // 3. Treatment type (Inpatient / Outpatient) check (CASE2인 경우이거나, 영수증 건너뛰기/입력 미완료된 수동 백업 질문)
            const hasType = (c.is_inpatient || c.is_outpatient);
            if (!hasType) {
                chatbotQuestions.push({
                    type: 'treatment_type',
                    text: '입원 치료와 통원 치료 중 어떤 형태로 치료받으셨나요?',
                    actions: `
                        <button onclick="answerQuestion('treatment_type', 'inpatient')" class="msg-btn msg-btn-primary">입원 치료</button>
                        <button onclick="answerQuestion('treatment_type', 'outpatient')" class="msg-btn">통원 치료 (외래)</button>
                    `
                });
                return;
            }

            // 4. Inpatient branch questions
            if (c.is_inpatient) {
                const needDays = (c.current_days === null || c.current_days === undefined || c.current_days === 0);
                if (needDays) {
                    chatbotQuestions.push({
                        type: 'days',
                        text: '며칠간 입원 치료를 받으셨나요?',
                        actions: `
                            <button onclick="answerQuestion('days', 3)" class="msg-btn">3일 입원</button>
                            <button onclick="answerQuestion('days', 14)" class="msg-btn">14일 입원</button>
                            <button onclick="answerQuestion('days', 30)" class="msg-btn">30일 입원</button>
                        `
                    });
                    return;
                }

                const surgeryInputted = (c.surgery !== null && c.surgery !== undefined);
                if (!surgeryInputted) {
                    chatbotQuestions.push({
                        type: 'surgery',
                        text: '치료 중 수술적 처치를 받으셨나요?',
                        actions: `
                            <button onclick="answerQuestion('surgery', true)" class="msg-btn">예, 수술 받았습니다</button>
                            <button onclick="answerQuestion('surgery', false)" class="msg-btn">아니오, 수술받지 않았습니다</button>
                        `
                    });
                    return;
                }
            }

            // 5. 치료 항목 (treatment_items) 질문 - 공통화 (입원/통원 불문하고 항상!)
            const treatmentsInputted = (c.treatment_items !== null && c.treatment_items !== undefined && (c.treatment_items.length > 0 || c.annual_visit_count !== null));
            if (!treatmentsInputted) {
                chatbotQuestions.push({
                    type: 'treatments',
                    text: '이번에 받은 치료 항목을 선택해주세요.',
                    actions: `
                        <div style="display:flex; flex-direction:column; gap:0.75rem; width:100%; margin-top:0.5rem; text-align:left;">
                            <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.25rem;">
                                <button type="button" class="msg-btn" onclick="toggleSubGroup('group-video')">영상검사</button>
                                <button type="button" class="msg-btn" onclick="toggleSubGroup('group-injection')">주사치료</button>
                                <button type="button" class="msg-btn" onclick="toggleSubGroup('group-manual')">도수·충격파</button>
                                <button type="button" class="msg-btn" onclick="toggleSubGroup('group-physical')">물리치료</button>
                                <button type="button" class="msg-btn" onclick="toggleSubGroup('group-etc')">기타</button>
                            </div>
                            
                            <div id="group-video" class="sub-group-panel" style="display:none; background:rgba(255,255,255,0.03); padding:0.5rem; border-radius:6px; border:1px solid var(--border-color);">
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main); margin-bottom:0.25rem;">
                                    <input type="checkbox" name="chk-treatment" value="XRAY"> 엑스레이 (XRAY)
                                </label>
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main);">
                                    <input type="checkbox" name="chk-treatment" value="MRI_MRA"> MRI / MRA 검사 (MRI_MRA)
                                </label>
                            </div>
                            
                            <div id="group-injection" class="sub-group-panel" style="display:none; background:rgba(255,255,255,0.03); padding:0.5rem; border-radius:6px; border:1px solid var(--border-color);">
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main);">
                                    <input type="checkbox" name="chk-treatment" value="INJECTION"> 주사치료 (INJECTION)
                                </label>
                            </div>
                            
                            <div id="group-manual" class="sub-group-panel" style="display:none; background:rgba(255,255,255,0.03); padding:0.5rem; border-radius:6px; border:1px solid var(--border-color);">
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main); margin-bottom:0.25rem;">
                                    <input type="checkbox" name="chk-treatment" value="MANUAL_THERAPY"> 도수치료 (MANUAL_THERAPY)
                                </label>
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main);">
                                    <input type="checkbox" name="chk-treatment" value="ECSWT"> 체외충격파 (ECSWT)
                                </label>
                            </div>
                            
                            <div id="group-physical" class="sub-group-panel" style="display:none; background:rgba(255,255,255,0.03); padding:0.5rem; border-radius:6px; border:1px solid var(--border-color);">
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main);">
                                    <input type="checkbox" name="chk-treatment" value="PHYSICAL_THERAPY"> 물리치료 (PHYSICAL_THERAPY)
                                </label>
                            </div>
                            
                            <div id="group-etc" class="sub-group-panel" style="display:none; background:rgba(255,255,255,0.03); padding:0.5rem; border-radius:6px; border:1px solid var(--border-color);">
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main); margin-bottom:0.25rem;">
                                    <input type="checkbox" name="chk-treatment" value="EMERGENCY"> 응급실 진료 (EMERGENCY)
                                </label>
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main); margin-bottom:0.25rem;">
                                    <input type="checkbox" name="chk-treatment" value="CAST"> 깁스 (CAST)
                                </label>
                                <label style="font-size:0.85rem; display:flex; align-items:center; gap:0.5rem; color:var(--text-main); margin-bottom:0.25rem;">
                                    <input type="checkbox" name="chk-treatment" value="ETC" onchange="toggleEtcInput(this)"> 기타 (ETC)
                                </label>
                                <input type="text" id="chk-treatment-etc-detail" placeholder="상세 치료 내용을 입력하세요" 
                                    style="display:none; width:100%; padding:0.35rem; font-size:0.8rem; border:1px solid var(--border-color); border-radius:4px; background:var(--bg-card); color:var(--text-main); margin-top:0.25rem;">
                            </div>
                            
                            <div style="margin-top:0.25rem; display:flex; gap:0.5rem;">
                                <button onclick="submitCheckedTreatments()" class="msg-btn msg-btn-primary">선택 완료</button>
                                <button onclick="answerQuestion('treatments', [])" class="msg-btn">선택 없음</button>
                            </div>
                        </div>
                    `
                });
                return;
            }

            // 6. 연간 치료 횟수 (annual_visit_count) 질문 - 공통화 (치료 항목 입력 완료 후 항상!)
            const annualCountInputted = (c.annual_visit_count !== null && c.annual_visit_count !== undefined);
            if (treatmentsInputted && !annualCountInputted) {
                chatbotQuestions.push({
                    type: 'annual_visit_count',
                    text: '해당 진료와 같은 내용으로 올해 몇 번 받으셨나요?',
                    actions: `
                        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.5rem;">
                            <button onclick="answerQuestion('annual_visit_count', 1)" class="msg-btn">1번</button>
                            <button onclick="answerQuestion('annual_visit_count', 2)" class="msg-btn">2번</button>
                            <button onclick="answerQuestion('annual_visit_count', 3)" class="msg-btn">3번</button>
                            <button onclick="answerQuestion('annual_visit_count', 5)" class="msg-btn">5번 이상</button>
                        </div>
                    `
                });
                return;
            }

            // 7. 보험 가입 기간 (policy_elapsed_days) 질문 - 공통화 (치료 횟수 입력 완료 후 항상!)
            const elapsedDaysInputted = (c.policy_elapsed_days !== null && c.policy_elapsed_days !== undefined);
            if (treatmentsInputted && annualCountInputted && !elapsedDaysInputted) {
                chatbotQuestions.push({
                    type: 'policy_elapsed_days',
                    text: '마지막으로 가입 시기에 따라 감액 조건이 달라질 수 있어요. 이 보험에 가입한 지 얼마나 됐나요?',
                    actions: `
                        <div style="display:flex; flex-direction:column; gap:0.4rem; margin-top:0.5rem; text-align:left; width:100%;">
                            <button onclick="answerQuestion('policy_elapsed_days', 0)" class="msg-btn">90일 미만</button>
                            <button onclick="answerQuestion('policy_elapsed_days', 90)" class="msg-btn">90일 이상 ~ 1년 미만</button>
                            <button onclick="answerQuestion('policy_elapsed_days', 365)" class="msg-btn">1년 이상 ~ 2년 미만</button>
                            <button onclick="answerQuestion('policy_elapsed_days', 730)" class="msg-btn">2년 이상</button>
                            <button onclick="answerQuestion('policy_elapsed_days', 800)" class="msg-btn">잘 모르겠어요</button>
                        </div>
                    `
                });
                return;
            }
        }

        // Toggle etc detail input display status
        function toggleEtcInput(checkbox) {
            const etcInput = document.getElementById('chk-treatment-etc-detail');
            if (etcInput) {
                etcInput.style.display = checkbox.checked ? 'block' : 'none';
                if (checkbox.checked) {
                    etcInput.focus();
                }
            }
        }

        // Submit checked outpatient treatments
        function submitCheckedTreatments() {
            const checkboxes = document.querySelectorAll('input[name="chk-treatment"]:checked');
            const values = Array.from(checkboxes).map(cb => {
                if (cb.value === 'ETC') {
                    const etcDetail = document.getElementById('chk-treatment-etc-detail')?.value.trim();
                    return etcDetail ? `ETC:${etcDetail}` : 'ETC';
                }
                return cb.value;
            });
            answerQuestion('treatments', values);
        }

        // Ask next interactive question
        async function askNextQuestion() {
            if (currentQuestionIndex < chatbotQuestions.length) {
                const q = chatbotQuestions[currentQuestionIndex];
                
                const inputField = document.getElementById('chat-input-field');
                if (q.type === 'annual_visit_count') {
                    inputField.dataset.mode = 'annual_visit_count';
                    inputField.placeholder = "올해 진료 횟수를 입력하세요 (예: 1)";
                } else {
                    inputField.dataset.mode = '';
                    inputField.placeholder = "치료 상황을 말해보세요 (예: '뇌경색 3일 입원')";
                }
                
                addBotMessage(q.text, q.actions);
            } else {
                try {
                    const res = await fetchAPI(`/cases/${activeCaseId}/dashboard`);
                    if (res.success) {
                        const dbVal = res.data.dashboard;
                        const msgText = (serviceType === 'CASE2') 
                            ? '좋아요. 제가 이해한 내용을 한 번 정리해볼게요.\n맞는지 확인한 뒤 분석을 시작할 수 있어요.'
                            : '내용 확인을 위해 대시보드로 넘어갈게요.';
                        addBotMessage(
                            msgText,
                            renderVerifyForm(dbVal)
                        );
                        // 대시보드 탭 활성화 및 렌더링
                        renderDashboard(dbVal);
                        return;
                    }
                } catch (err) {
                    console.error("Failed to check case state for dashboard auto-transition", err);
                }

                const actionsHtml = `
                    <button onclick="selectInputMethod('PAYMENT')" class="msg-btn msg-btn-primary">💳 결제 내역 복사입력</button>
                    <button onclick="selectInputMethod('STATEMENT')" class="msg-btn">📄 세부산정내역서 파일 업로드</button>
                    <button onclick="skipReceiptInput()" class="msg-btn">⏭️ 영수증 없이 바로 분석</button>
                `;
                addBotMessage(
                    "추가 정보 수집을 완료했습니다! 분석할 영수증 내역을 입력하시겠습니까? " +
                    "영수증이 없다면 바로 보장 분석을 진행할 수 있습니다.",
                    actionsHtml
                );
            }
        }

        // Answer interactive question
        async function answerQuestion(type, value, extraVal = null) {
            let textRep = "";
            let answers = [];
            if (type === 'disease') {
                textRep = `${value} (${extraVal})`;
                answers.push({ question_id: "disease_name", value: value });
                answers.push({ question_id: "disease_kcd", value: extraVal });
            } else if (type === 'treatment_type') {
                const isInpatient = (value === 'inpatient');
                textRep = isInpatient ? "입원 치료" : "통원 치료";
                answers.push({ question_id: "is_inpatient", value: isInpatient });
                answers.push({ question_id: "is_outpatient", value: !isInpatient });
                if (!isInpatient) {
                    answers.push({ question_id: "admission_days_current", value: 0 });
                    answers.push({ question_id: "admission_days_diagnosed", value: 0 });
                    answers.push({ question_id: "surgery", value: false });
                }
            } else if (type === 'days') {
                textRep = `${value}일 입원`;
                answers.push({ question_id: "admission_days_current", value: value });
                answers.push({ question_id: "admission_days_diagnosed", value: value });
            } else if (type === 'surgery') {
                textRep = value ? "수술 받음" : "수술 안 받음";
                answers.push({ question_id: "surgery", value: value });
            } else if (type === 'treatments') {
                const names = {
                    "MANUAL_THERAPY": "도수치료",
                    "ECSWT": "체외충격파",
                    "MRI_MRA": "MRI/MRA",
                    "INJECTION": "주사치료",
                    "XRAY": "엑스레이",
                    "PHYSICAL_THERAPY": "물리치료",
                    "EMERGENCY": "응급실 진료",
                    "CAST": "깁스",
                    "ETC": "기타"
                };
                textRep = value.length > 0 ? `치료 선택: ${value.map(v => {
                    if (typeof v === 'string' && v.startsWith('ETC:')) {
                        return `기타(${v.substring(4)})`;
                    }
                    return names[v] || v;
                }).join(', ')}` : "치료 없음";
                answers.push({ question_id: "treatment_items", value: value });
            } else if (type === 'annual_visit_count') {
                textRep = `${value}번`;
                answers.push({ question_id: "annual_visit_count", value: value });
            } else if (type === 'policy_elapsed_days') {
                const elapsedLabels = {
                    0: "90일 미만",
                    90: "90일 이상~1년 미만",
                    365: "1년 이상~2년 미만",
                    730: "2년 이상",
                    800: "잘 모르겠어요"
                };
                textRep = `보험 가입 기간: ${elapsedLabels[value] || value}`;
                answers.push({ question_id: "policy_elapsed_days", value: value });
            }
            
            addUserMessage(textRep);
            
            try {
                const res = await fetchAPI(`/cases/${activeCaseId}/answers`, {
                    method: 'POST',
                    body: { answers: answers }
                });
                
                if (res.success && res.data) {
                    globalTreatmentTypes = res.data.treatment_types || [];
                    if (res.data.case) {
                        rebuildQuestions(res.data.case);
                    }
                }
                
                currentQuestionIndex = 0;
                askNextQuestion();
            } catch (err) {
                addBotMessage("오류가 발생했습니다: " + err.message);
            }
        }

        // Select input method directly from bot actions
        function selectInputMethodDirect(method) {
            const userMsgText = method === 'PAYMENT' ? '문자·카드내역으로 확인' : '진료비 세부산정내역서로 확인';
            addUserMessage(userMsgText);

            if (method === 'PAYMENT') {
                const inputField = document.getElementById('chat-input-field');
                inputField.dataset.mode = 'payment';
                inputField.placeholder = "결제일, 병원명, 금액을 입력하세요 (예: '정형외과 06/10 80,000원 승인')";
                addBotMessage('결제 문자나 카드내역을 붙여넣거나 올려주세요.');
            } else {
                const fileInputHtml = `
                    <input type="file" id="statement-file-input" onchange="uploadStatementFile(this)" style="display:none;">
                    <button onclick="document.getElementById('statement-file-input').click()" class="msg-btn msg-btn-primary">📂 파일 선택 및 업로드</button>
                `;
                addBotMessage('진료비 세부 산정 내역서 PDF 또는 이미지 파일을 업로드해 주세요.', fileInputHtml);
            }
        }

        // Confirm parsed payment information
        async function confirmPaymentInfo(isCorrect) {
            if (isCorrect) {
                addUserMessage("맞아요");
                
                if (tempVisitTypeInferred) {
                    // 통원/입원 추정 판정 컨펌 진행
                    const inferredIsOutpatient = (tempInferredVisitType === 'outpatient');

                    const visitTypeMessage = inferredIsOutpatient ? 
                        "결제금액을 보니 통원치료인 것 같은데 맞나요?" : 
                        "결제금액을 보니 입원치료인 것 같은데 맞나요?";

                    const actionsHtml = `
                        <button onclick="confirmEstimatedVisitType(true)" class="msg-btn msg-btn-primary">맞아요</button>
                        <button onclick="confirmEstimatedVisitType(false)" class="msg-btn">아니요(${inferredIsOutpatient ? '→입원' : '→통원'})</button>
                    `;
                    
                    setTimeout(() => {
                        addBotMessage(visitTypeMessage, actionsHtml);
                    }, 500);
                } else {
                    // 이미 입/통원이 확정된 상태이므로 추정 컨펌 질문 생략
                    try {
                        inputMethodSelected = true;
                        
                        // answers API 호출하여 최신 case 상태를 받아와서 rebuildQuestions에 공급
                        const caseRes = await fetchAPI(`/cases/${activeCaseId}/answers`, {
                            method: 'POST',
                            body: { answers: [] } // 빈 리스트 전송하여 case 데이터 조회
                        });
                        
                        if (caseRes.success) {
                            rebuildQuestions(caseRes.data.case);
                            currentQuestionIndex = 0;
                            setTimeout(() => {
                                askNextQuestion();
                            }, 500);
                        }
                    } catch (err) {
                        addBotMessage("오류가 발생했습니다: " + err.message);
                    }
                }
            } else {
                addUserMessage("수정할게요");
                addBotMessage("수정할 결제 금액을 입력해주세요. (예: 80000)");
                const inputField = document.getElementById('chat-input-field');
                inputField.dataset.mode = 'payment_edit';
                inputField.placeholder = "결제 금액을 숫자로 입력하세요";
            }
        }

        // Confirm inpatient/outpatient estimation
        async function confirmEstimatedVisitType(isCorrect) {
            let finalVisitType = tempInferredVisitType;
            if (!isCorrect) {
                finalVisitType = (tempInferredVisitType === 'outpatient') ? 'inpatient' : 'outpatient';
            }

            const userText = isCorrect ? "맞아요" : (finalVisitType === 'inpatient' ? "아니요(→입원)" : "아니요(→통원)");
            addUserMessage(userText);

            const isInpatient = (finalVisitType === 'inpatient');

            try {
                // Save answers for visit type, payment amount and basic inpatient days
                const answers = [
                    { question_id: "is_inpatient", value: isInpatient },
                    { question_id: "is_outpatient", value: !isInpatient },
                    { question_id: "admission_days_current", value: isInpatient ? 3 : 0 },
                    { question_id: "admission_days_diagnosed", value: isInpatient ? 3 : 0 },
                    { question_id: "surgery", value: false }
                ];

                const res = await fetchAPI(`/cases/${activeCaseId}/answers`, {
                    method: 'POST',
                    body: { answers: answers }
                });

                if (res.success) {
                    inputMethodSelected = true;
                    
                    const latestCase = res.data.case;
                    globalTreatmentTypes = res.data.treatment_types || [];

                    rebuildQuestions(latestCase);
                    currentQuestionIndex = 0;

                    setTimeout(() => {
                        askNextQuestion();
                    }, 500);
                }
            } catch (err) {
                addBotMessage("오류가 발생했습니다: " + err.message);
            }
        }

        // Renders dashboard analysis dynamically when transition happens
        async function renderDashboard(dbVal) {
            try {
                document.getElementById('empty-dashboard').style.display = 'none';
                document.getElementById('dashboard-content').style.display = 'flex';

                const current_days = dbVal.admission_days_current || 0;
                const policy_elapsed_days = dbVal.policy_elapsed_days || 800;
                const surgery = !!dbVal.surgery;
                const disease_kcd = dbVal.disease_kcd;
                const disease_name = dbVal.disease_name;
                const is_inpatient = !!dbVal.is_inpatient;
                const is_outpatient = !!dbVal.is_outpatient;
                const payment_amount = dbVal.payment_amount || 0;
                const annual_visit_count = dbVal.annual_visit_count || 1;
                const treatment_items = dbVal.treatment_items || [];

                // 1. PATCH /cases/{id}/dashboard
                await fetchAPI(`/cases/${activeCaseId}/dashboard`, {
                    method: 'PATCH',
                    body: {
                        disease_kcd,
                        disease_name,
                        surgery,
                        admission_days_current: current_days,
                        admission_days_diagnosed: current_days,
                        policy_elapsed_days,
                        is_inpatient,
                        is_outpatient,
                        payment_amount,
                        annual_visit_count,
                        treatment_items
                    }
                });

                // 2. POST /analysis/search
                const searchRes = await fetchAPI('/analysis/search', {
                    method: 'POST',
                    body: { case_id: activeCaseId }
                });

                // 3. POST /analysis/compare
                const targetDays = current_days > 3 ? 30 : 14;
                const compareRes = await fetchAPI('/analysis/compare', {
                    method: 'POST',
                    body: {
                        case_id: activeCaseId,
                        current_days: current_days,
                        target_days: targetDays
                    }
                });

                // 4. POST /reports
                const reportInitRes = await fetchAPI('/reports', {
                    method: 'POST',
                    body: { case_id: activeCaseId }
                });

                // 5. GET /reports/{id}
                const reportRes = await fetchAPI(`/reports/${reportInitRes.data.report_id}`);

                analysisData = {
                    search: searchRes.data,
                    compare: compareRes.data,
                    report: reportRes.data ? reportRes.data.body : { claim_documents: [] }
                };

                showDashboard();

                if (searchRes.data.notice) {
                    addBotMessage(`⚠️ [알림]\\n${searchRes.data.notice}`);
                }
                if (compareRes.data.notice && compareRes.data.notice !== searchRes.data.notice) {
                    addBotMessage(`⚠️ [알림]\\n${compareRes.data.notice}`);
                }
            } catch (err) {
                console.error("Auto dashboard load failed:", err);
                addBotMessage("대시보드 분석 데이터를 가져오는 도중 실패: " + err.message);
            }
        }

        // Skip receipt flow
        async function skipReceiptInput() {
            addUserMessage("영수증 입력 건너뛰기");
            try {
                const res = await fetchAPI(`/cases/${activeCaseId}/dashboard`);
                if (res.success) {
                    addBotMessage(
                        '최종 분석 정보입니다. 내용을 확인하고 보장 분석을 시작해 주세요.',
                        renderVerifyForm(res.data.dashboard)
                    );
                }
            } catch (err) {
                addBotMessage("대시보드 조회 실패: " + err.message);
            }
        }

        // Select file/text input method
        function selectInputMethod(method) {
            if (method === 'PAYMENT') {
                const inputField = document.getElementById('chat-input-field');
                inputField.dataset.mode = 'payment';
                inputField.placeholder = "결제일, 병원명, 금액을 입력하세요 (예: '정형외과 2026.06.10 결제 80,000원')";
                addBotMessage('카드 결제 승인 문자나 결제 텍스트 내역을 복사해서 입력창에 넣어 전송해 주세요.');
            } else {
                const fileInputHtml = `
                    <input type="file" id="statement-file-input" onchange="uploadStatementFile(this)" style="display:none;">
                    <button onclick="document.getElementById('statement-file-input').click()" class="msg-btn msg-btn-primary">📂 파일 선택 및 업로드</button>
                `;
                addBotMessage('진료비 세부 산정 내역서 PDF 또는 이미지 파일을 업로드해 주세요.', fileInputHtml);
            }
        }

        // Upload medical detail statement file
        async function uploadStatementFile(input) {
            const file = input.files[0];
            if (!file) return;

            addBotMessage(`진료비 세부산정내역서 '${file.name}' 파일을 업로드하여 정밀 분석을 시작합니다...`);
            
            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetchAPI(`/cases/${activeCaseId}/medical-detail-statement`, {
                    method: 'POST',
                    body: formData,
                    headers: {} // Let browser bind multipart boundary
                });
                
                if (res.success) {
                    const dashRes = await fetchAPI(`/cases/${activeCaseId}/dashboard`);
                    addBotMessage(
                        '세부산정내역서 텍스트 파싱을 완료했습니다. 추출된 내용을 최종 검수 후 분석을 시작해 주세요.',
                        renderVerifyForm(dashRes.data.dashboard)
                    );
                }
            } catch (err) {
                addBotMessage('파일 분석 실패: ' + err.message);
            }
        }

        // Render Verify Form HTML string
        function renderVerifyForm(data) {
            // Preset values if empty
            const disease_name = data.disease_name || '기타 추간판 장애 (허리디스크)';
            const disease_kcd = data.disease_kcd || 'M51';
            const current_days = data.admission_days_current || 0;
            const diagnosed_days = data.admission_days_diagnosed || current_days || 0;
            const policy_elapsed_days = data.policy_elapsed_days || 800;
            const surgery = data.surgery ? 'checked' : '';
            const is_inpt = data.is_inpatient ? 'checked' : '';
            const is_outpt = data.is_outpatient ? 'checked' : '';
            const payment_amount = data.payment_amount || 0;
            const annual_visit_count = data.annual_visit_count || 1;
            const treatments = data.treatment_items || [];

            // Unique ID to find inputs
            const formId = 'verify-form-' + Math.floor(Math.random() * 1000);

            // Using global window callback
            setTimeout(() => {
                const btn = document.getElementById(formId + '-btn');
                if (btn) {
                    btn.onclick = () => submitVerification(formId);
                }
            }, 100);

            const names = {
                "MANUAL_THERAPY": "도수치료",
                "ECSWT": "체외충격파",
                "MRI_MRA": "MRI/MRA",
                "INJECTION": "주사치료",
                "XRAY": "엑스레이",
                "PHYSICAL_THERAPY": "물리치료",
                "ETC": "기타"
            };
            const treatmentText = treatments.length > 0 ?
                treatments.map(v => {
                    if (typeof v === 'string' && v.startsWith('ETC:')) {
                        return `기타(${v.substring(4)})`;
                    }
                    return names[v] || v;
                }).join(', ') : "없음";

            const isCase2 = (serviceType === 'CASE2');
            const diagnosedDaysFieldHtml = isCase2 ? `
                <div class="verify-form-group" style="flex:1;">
                    <label>의사 권고 입원일수 (일)</label>
                    <input type="number" class="verify-input" name="diagnosed_days" value="${diagnosed_days}">
                </div>
            ` : `<input type="hidden" name="diagnosed_days" value="${current_days}">`;

            return `
                <div class="verify-card" id="${formId}">
                    <div class="verify-form-group">
                        <label>질병명 및 KCD 코드</label>
                        <input type="text" class="verify-input" name="disease" value="${disease_name} (${disease_kcd})" disabled>
                        <input type="hidden" name="disease_kcd" value="${disease_kcd}">
                        <input type="hidden" name="disease_name" value="${disease_name}">
                    </div>
                    <div style="display:flex; gap:0.5rem; margin-top:0.25rem;">
                        <div class="verify-checkbox-area" style="flex:1;">
                            <input type="radio" id="${formId}-inpt" name="treatment_type" value="inpatient" ${is_inpt ? 'checked' : ''}>
                            <label for="${formId}-inpt" style="cursor:pointer; font-size:0.8rem;">입원치료</label>
                        </div>
                        <div class="verify-checkbox-area" style="flex:1;">
                            <input type="radio" id="${formId}-outpt" name="treatment_type" value="outpatient" ${is_outpt ? 'checked' : ''}>
                            <label for="${formId}-outpt" style="cursor:pointer; font-size:0.8rem;">통원치료</label>
                        </div>
                    </div>
                    <div style="display:flex; gap:0.5rem; margin-top:0.25rem;">
                        <div class="verify-form-group" style="flex:1;">
                            <label>${isCase2 ? '현재 입원일수 (일)' : '치료(입원) 일수 (일)'}</label>
                            <input type="number" class="verify-input" name="current_days" value="${current_days}">
                        </div>
                        ${diagnosedDaysFieldHtml}
                        <div class="verify-form-group" style="flex:1;">
                            <label>가입 후 경과일 (일)</label>
                            <input type="number" class="verify-input" name="policy_elapsed_days" value="${policy_elapsed_days}">
                        </div>
                    </div>
                    <div style="display:flex; gap:0.5rem; margin-top:0.25rem;">
                        <div class="verify-form-group" style="flex:1;">
                            <label>결제 금액 (원)</label>
                            <input type="number" class="verify-input" name="payment_amount" value="${payment_amount}">
                        </div>
                        <div class="verify-form-group" style="flex:1;">
                            <label>연간 진료 횟수 (회)</label>
                            <input type="number" class="verify-input" name="annual_visit_count" value="${annual_visit_count}">
                        </div>
                    </div>
                    <div style="font-size:0.75rem; margin-top:0.25rem; color:var(--text-muted);">
                        선택된 추가 치료: <strong style="color:var(--text-main);">${treatmentText}</strong>
                        <input type="hidden" name="treatment_items" value='${JSON.stringify(treatments)}'>
                    </div>
                    <div class="verify-checkbox-area" style="margin-top:0.25rem;">
                        <input type="checkbox" id="${formId}-surg" name="surgery" ${surgery}>
                        <label for="${formId}-surg" style="cursor:pointer;">수술적 처치를 받으셨습니까?</label>
                    </div>
                    <button id="${formId}-btn" class="msg-btn msg-btn-primary" style="margin-top:0.5rem;">✅ 의료정보 확정 및 보장 분석</button>
                </div>
            `;
        }

        // Submit verification and invoke RAG search
        async function submitVerification(formId) {
            const form = document.getElementById(formId);
            if (!form) return;

            const current_days = parseInt(form.querySelector('[name="current_days"]').value) || 0;
            const diagnosed_days = parseInt(form.querySelector('[name="diagnosed_days"]')?.value) || current_days || 0;
            const policy_elapsed_days = parseInt(form.querySelector('[name="policy_elapsed_days"]').value) || 0;
            const surgery = form.querySelector('[name="surgery"]').checked;
            const disease_kcd = form.querySelector('[name="disease_kcd"]').value;
            const disease_name = form.querySelector('[name="disease_name"]').value;

            const is_inpatient = form.querySelector('input[name="treatment_type"]:checked')?.value === 'inpatient';
            const is_outpatient = form.querySelector('input[name="treatment_type"]:checked')?.value === 'outpatient';
            const payment_amount = parseInt(form.querySelector('[name="payment_amount"]').value) || 0;
            const annual_visit_count = parseInt(form.querySelector('[name="annual_visit_count"]').value) || 1;
            const treatment_items = JSON.parse(form.querySelector('[name="treatment_items"]').value || '[]');

            addBotMessage('입력하신 치료 상황을 확정하여 분석을 실행합니다. (RAG 및 룰 엔진 구동중...)');

            try {
                // 1. PATCH /cases/{id}/dashboard (v2.1)
                await fetchAPI(`/cases/${activeCaseId}/dashboard`, {
                    method: 'PATCH',
                    body: {
                        disease_kcd,
                        disease_name,
                        surgery,
                        admission_days_current: current_days,
                        admission_days_diagnosed: diagnosed_days,
                        policy_elapsed_days,
                        is_inpatient,
                        is_outpatient,
                        payment_amount,
                        annual_visit_count,
                        treatment_items
                    }
                });

                // 2. POST /analysis/search
                const searchRes = await fetchAPI('/analysis/search', {
                    method: 'POST',
                    body: { case_id: activeCaseId }
                });

                // 3. POST /analysis/compare (v2.1)
                const targetDays = (serviceType === 'CASE2') ? diagnosed_days : (current_days > 3 ? 30 : 14);
                const compareRes = await fetchAPI('/analysis/compare', {
                    method: 'POST',
                    body: {
                        case_id: activeCaseId,
                        current_days: current_days,
                        target_days: targetDays
                    }
                });

                // 4. POST /reports
                const reportInitRes = await fetchAPI('/reports', {
                    method: 'POST',
                    body: { case_id: activeCaseId }
                });

                // 5. GET /reports/{id}
                const reportRes = await fetchAPI(`/reports/${reportInitRes.data.report_id}`);

                // Merge and show dashboard
                analysisData = {
                    search: searchRes.data,
                    compare: compareRes.data,
                    report: reportRes.data ? reportRes.data.body : { claim_documents: [] }
                };

                showDashboard();
                addBotMessage('보장 분석 및 비교 리포트 생성을 완료했습니다! 우측 패널의 리포트를 탭하여 확인해 보세요.');

                // 임의 데이터 보완에 대한 알림(notice) 챗봇 출력
                if (searchRes.data.notice) {
                    addBotMessage(`⚠️ [알림]\\n${searchRes.data.notice}`);
                }
                if (compareRes.data.notice && compareRes.data.notice !== searchRes.data.notice) {
                    addBotMessage(`⚠️ [알림]\\n${compareRes.data.notice}`);
                }

            } catch (err) {
                addBotMessage('RAG 분석 도중 실패: ' + err.message);
            }
        }

        // Show Dashboard Panel with data
        function showDashboard() {
            document.getElementById('empty-dashboard').style.display = 'none';
            document.getElementById('dashboard-content').style.display = 'flex';

            // Summary Counters
            document.getElementById('summary-eligible-count').innerText = analysisData.search.summary.eligible_count || 0;
            document.getElementById('summary-missed-count').innerText = analysisData.search.summary.missed_count || 0;

            // Render cards
            renderCoverageCards();
            renderCompareTable();
            renderChecklist();

            // Default tab
            switchTab('eligible');
        }

        // Render coverage cards in Eligible and Missed tabs
        function renderCoverageCards() {
            const eligibleContainer = document.getElementById('eligible-cards');
            const missedContainer = document.getElementById('missed-cards');

            eligibleContainer.innerHTML = '';
            missedContainer.innerHTML = '';

            const results = analysisData.search.results || [];
            
            if (results.length === 0) {
                const emptyMsg = '<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted);">매칭되는 청구 가능 보장이 없습니다.</div>';
                eligibleContainer.innerHTML = emptyMsg;
                missedContainer.innerHTML = emptyMsg;
                return;
            }

            results.forEach(r => {
                const card = document.createElement('div');
                card.className = 'coverage-card';
                card.onclick = () => openModal(r);

                // Badge mapping
                let statusLabel = '대기';
                let statusClass = 'status-potential';
                if (r.status === 'eligible') { statusLabel = '청구 가능'; statusClass = 'status-eligible'; }
                else if (r.status === 'claimed') { statusLabel = '기청구'; statusClass = 'status-claimed'; }
                else if (r.status === 'boundary_not_met') { statusLabel = '조건 미충족'; statusClass = 'status-boundary_not_met'; }
                else if (r.status === 'waiting_period_not_met') { statusLabel = '면책기간 미경과'; statusClass = 'status-waiting_period_not_met'; }
                else if (r.status === 'potential') { statusLabel = '관련 가능 보장'; statusClass = 'status-potential'; }

                // Check missed to highlight
                const isMissed = r.missed;

                card.innerHTML = `
                    <div class="coverage-meta">
                        <span class="coverage-insurer">${r.policy}</span>
                        <span class="coverage-status ${statusClass}">${statusLabel}</span>
                    </div>
                    <h4 class="coverage-name">${r.rider}</h4>
                    ${r.calc ? `<div class="coverage-calc">계산 구조:<div class="coverage-calc-val">${r.calc}</div></div>` : ''}
                    <div class="coverage-click-tip">약관 원문 보기 &gt;</div>
                `;

                if (isMissed) {
                    const missedCard = card.cloneNode(true);
                    missedCard.onclick = () => openModal(r);
                    missedContainer.appendChild(missedCard);
                }
                
                eligibleContainer.appendChild(card);
            });

            if (missedContainer.children.length === 0) {
                missedContainer.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-success);">🎉 놓치고 계신 보장이 없습니다! 모두 청구 상태입니다.</div>';
            }
        }

        // Render Compare view scenario table
        function renderCompareTable() {
            const tbody = document.getElementById('compare-table-rows');
            const table = tbody.closest('table');
            const thead = table.querySelector('thead');
            tbody.innerHTML = '';

            const rawCompare = analysisData.compare || {};
            const comparisons = rawCompare.comparison || [];
            const slider = rawCompare.slider || {};
            
            const currentDays = slider.current || 3;
            const targetDays = slider.target || 14;

            // Update headers dynamically
            thead.innerHTML = `
                <tr>
                    <th>보험상품 / 특약명</th>
                    <th>현재 퇴원 시점 (${currentDays}일)</th>
                    <th>비교 퇴원 시점 (${targetDays}일)</th>
                </tr>
            `;

            if (comparisons.length === 0) {
                tbody.innerHTML = `<tr>
                    <td colspan="3" style="text-align:center; color:var(--text-muted);">
                        비교 가능한 입원 일당 특약이 존재하지 않습니다.
                    </td>
                </tr>`;
                return;
            }

            comparisons.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><strong>[${item.policy_name}]</strong><br>${item.rider_name}</td>`;

                const scenarios = item.scenarios || [];
                scenarios.forEach(sc => {
                    let badgeClass = 'status-potential';
                    let label = '미해당';
                    if (sc.status === 'eligible') { badgeClass = 'status-eligible'; label = '청구 가능'; }
                    else if (sc.status === 'boundary_not_met') { badgeClass = 'status-boundary_not_met'; label = '경계 미달'; }
                    else if (sc.status === 'waiting_period_not_met') { badgeClass = 'status-waiting_period_not_met'; label = '면책 미경과'; }

                    const boundaryText = sc.gap_days ? `<span class="compare-boundary-highlight">⚠️ ${sc.gap_days}일 부족으로 미해당</span>` : '';
                    const calcText = sc.calc ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">${sc.calc}</div>` : '';
                    const amountText = sc.amount_note ? `<div style="font-size:0.8rem; font-weight:600; color:var(--accent-color);">${sc.amount_note}</div>` : '';

                    tr.innerHTML += `
                        <td>
                            <span class="compare-status-badge ${badgeClass}">${label}</span>
                            ${boundaryText}
                            ${amountText}
                            ${calcText}
                        </td>
                    `;
                });
                tbody.appendChild(tr);
            });
        }

        // Render Checklist view
        function renderChecklist() {
            const container = document.getElementById('checklist-items');
            container.innerHTML = '';

            const docs = analysisData.report.claim_documents || [];
            
            if (docs.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted);">필요 서류 체크리스트가 준비되지 않았습니다.</div>';
                return;
            }

            const docMap = {};
            docs.forEach(doc => {
                const category = doc.category || '기타 구비서류';
                if (!docMap[category]) docMap[category] = [];
                docMap[category].push(doc.name);
            });

            Object.keys(docMap).forEach(cat => {
                const section = document.createElement('div');
                section.className = 'checklist-section';
                section.innerHTML = `<h4 class="checklist-title">${cat}</h4>`;

                docMap[cat].forEach(docName => {
                    const item = document.createElement('div');
                    item.className = 'checklist-item';
                    item.innerHTML = `
                        <input type="checkbox" class="checklist-cb" id="doc-${docName}">
                        <label for="doc-${docName}" style="cursor:pointer;">${docName}</label>
                    `;
                    section.appendChild(item);
                });

                container.appendChild(section);
            });
        }

        // Switch Tab helper
        function switchTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.style.display = 'none');

            // Find matching tab button
            const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.onclick.toString().includes(tabName));
            if (btn) btn.classList.add('active');

            const pane = document.getElementById(`tab-pane-${tabName}`);
            if (pane) pane.style.display = 'block';
        }

        // Modal triggers
        function openModal(coverage) {
            document.getElementById('modal-rider-name').innerText = coverage.rider;
            document.getElementById('modal-policy-name').innerText = coverage.policy;
            document.getElementById('modal-explanation').innerText = coverage.explanation || '지급 기준 판정 진행 완료.';
            
            const evidence = coverage.evidence || {};
            document.getElementById('modal-evidence-article').innerText = (evidence.article || '미지정') + ` (조항/페이지: ${evidence.page || '-'}p)`;
            
            const rawQuote = evidence.quote || '근거 조항 원문 정보가 없습니다.';
            document.getElementById('modal-evidence-quote').innerText = rawQuote;

            document.getElementById('quote-modal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('quote-modal').classList.remove('show');
        }

        // Restart flow
        function handleRestart() {
            activeCaseId = null;
            selectedPresetIds = [];
            serviceType = 'CASE1';
            analysisData = null;
            curStep = 0;
            chatbotQuestions = [];
            currentQuestionIndex = 0;
            
            // Sequential state control variables reset
            inputMethodSelected = false;
            tempPaymentAmount = null;
            tempPaymentDate = null;
            tempHospitalName = null;
            tempInferredVisitType = null;
            tempVisitTypeInferred = false;

            document.getElementById('step-service').style.display = 'flex';
            document.getElementById('step-preset').style.display = 'none';
            document.getElementById('step-main').style.display = 'none';
            document.getElementById('presets-container').innerHTML = '';
            document.getElementById('chat-messages').innerHTML = '';
            document.getElementById('empty-dashboard').style.display = 'flex';
            document.getElementById('dashboard-content').style.display = 'none';
        }
    </script>
</body>
</html>
"""


@bp.get("/test-ui")
def get_test_ui():
    """테스트 클라이언트 HTML 단일 페이지를 반환합니다."""
    return Response(HTML_CONTENT, mimetype="text/html")
