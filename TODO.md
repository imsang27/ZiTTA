# ZiTTA Core 로드맵 / TODO
---
이 문서는 ZiTTA 프로젝트에서 **CI → 도메인 고정 → 패키징 → CLI**로 이어지는 흐름을  
까먹거나 빼먹지 않고 그대로 따라가기 위한 체크리스트다.

---

## 상태 요약
---
- [x] CI에 pytest 붙이기 (GitHub Actions)
- [x] CI 로그 요약 강화 (`-ra`)
- [ ] Intent / Action 도메인 고정 (Enum)
- [ ] core 패키징 (`pyproject.toml`)
- [ ] CLI 인터페이스 추가 (`python -m zitta ...`)

---

## CI 강화 (1번 마무리) ✅
---
### 목표
테스트 결과를 한눈에 파악할 수 있는 CI 로그 구성

### TODO
- [x] `.github/workflows/tests.yml` 수정
  - `python -m pytest -q`  
    → `python -m pytest -q -ra`
- [x] 커밋
  - `👷 ci(workflow): pytest 실행 옵션에 -ra 추가하여 결과 요약 강화`
- [x] GitHub Actions 실행 성공 확인

### 체크 포인트
- [x] PR / push 시 테스트 성공·실패가 명확히 보이는가
- [x] 경고는 유지되되, 실패 신호가 묻히지 않는가

---

## Intent 도메인 고정 (3번)
---
### 목표
Intent / Action을 문자열이 아닌 **계약(Contract)** 으로 고정

### TODO
- [ ] `core/intent.py` (또는 대응 파일)에 Enum 정의
  - 예: `IntentType`, `ActionType`
- [ ] 외부 입력 → Enum 변환 로직 구현
  - 예: `parse_intent_type(value: str) -> IntentType`
- [ ] 라우팅/분기 로직에서 문자열 비교 제거
- [ ] 테스트 추가
  - [ ] 정상 케이스
  - [ ] 대소문자/공백 등 변형 입력
  - [ ] 알 수 없는 값 처리

### 반드시 결정해야 할 정책
- [ ] Unknown 값 처리 방식
  - A. `UNKNOWN` Enum으로 흡수
  - B. 예외 발생 (fail fast)
  - C. 기본값으로 fallback

### 완료 기준
- [ ] `intent.type`, `action`이 코드 전반에서 Enum으로만 사용됨
- [ ] 문자열 오타로 인한 분기 실패가 구조적으로 불가능

---

## Core 패키징 (2번)
---
### 목표
ZiTTA core를 **진짜 Python 패키지**로 만들어 재사용/확장 기반 확보

### TODO (최소 스코프)
- [ ] `pyproject.toml` 생성
- [ ] 패키지 이름 확정 (`zitta` 권장)
- [ ] 패키지 레이아웃 결정
  - [ ] `src/zitta/...` 구조 (권장)
  - [ ] 또는 현재 구조 유지 (단기 선택)
- [ ] 의존성 분리
  - [ ] runtime dependencies
  - [ ] dev dependencies (pytest 등)
- [ ] 로컬 editable install 테스트
  - `pip install -e .`
- [ ] CI에서 import / 테스트 정상 동작 확인

### 주의 구간
- [ ] 상대경로 / 절대경로 import 혼재
- [ ] 테스트가 `sys.path`에 의존하는 구조
- [ ] 엔트리 파일(`main.py`) 위치 혼선

### 완료 기준
- [ ] 어디서든 `import zitta` 가능
- [ ] CI 테스트가 동일하게 통과

---

## CLI 인터페이스 추가 (4번)
---
### 목표
ZiTTA를 **한 줄 명령으로 실행** 가능하게 만들기

### MVP 스펙
- `python -m zitta "할 일 추가"`
- 내부적으로 core 흐름 그대로 사용
- 출력은 표준 출력 위주 (부작용 최소화)

### TODO
- [ ] `zitta/__main__.py` 구현
- [ ] argv → text 파싱
- [ ] core 호출 (intent 생성 → dispatch)
- [ ] 스모크 테스트
  - [ ] 빈 입력 / help 처리
  - [ ] 정상 명령 처리
  - [ ] 알 수 없는 명령 처리

### 완료 기준
- [ ] 로컬/CI에서 CLI 실행 재현 가능
- [ ] CLI가 core를 우회하지 않고 “사용”만 함

---

## 권장 작업 순서
---
1. [x] CI 로그 요약 강화 (`-ra`) ✅
2. [ ] Intent / Action Enum 고정
3. [ ] Core 패키징
4. [ ] CLI 인터페이스 추가

---

## 리스크 & 기술 부채 (추적용 메모)
---
- [ ] `google.generativeai` → `google.genai` 마이그레이션
- [ ] Python 3.11+ 전환 계획 (2026-10-04 이전)
- [ ] GitHub Actions pip 캐시 비대 문제 (필요 시 정리)

---
