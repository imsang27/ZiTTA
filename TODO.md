# ZiTTA Core 확장 로드맵 / TODO (2 · 3 · 4)
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

## ZiTTA Core 확장 로드맵 (2 · 3 · 4)
---

### 목표 요약
---
- **3 (Enum 고정)**: 도메인 계약을 잠가서 이후 확장(패키징/CLI/플러그인)이 흔들리지 않게 만들기
- **2 (패키징)**: core를 진짜 라이브러리로 만들어 재사용·배포·엔트리포인트 기반을 마련
- **4 (CLI)**: "한 줄 실행" 인터페이스로 사용성과 개발 생산성 확보

### 진행 순서 권장
---
- [ ] **3 → 2 → 4**
  - 이유: 계약(데이터 모델)을 먼저 고정해야 패키징/CLI가 덜 깨진다.

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

## Intent.type / action을 Enum으로 고정 (3)
---
### 목표
Intent / Action을 문자열이 아닌 **계약(Contract)** 으로 고정

### 완료 기준
- [ ] 코드 전반에서 `intent.type` / `action`을 **문자열 비교로 분기하지 않음**
- [ ] 외부 입력(LLM/payload/CLI)은 **파싱 함수로 Enum 변환** 후 처리
- [ ] 최소 테스트 포함

### TODO
- [ ] Enum 설계 확정
  - [ ] `IntentType` Enum 생성
  - [ ] `Action`(또는 `ActionType`) Enum 생성
  - [ ] `UNKNOWN` 포함 여부 결정(권장: 포함)
- [ ] 변환 로직 추가
  - [ ] `parse_intent_type(str) -> IntentType`
  - [ ] `parse_action(str) -> Action`
  - [ ] 대소문자/공백/하이픈 등 정규화 규칙 정의
- [ ] 라우팅 코드 교체
  - [ ] 기존 `"todo"` / `"memo"` 같은 문자열 분기 제거 → Enum 기반 분기
- [ ] 테스트 추가
  - [ ] 정상 입력 → Enum 매핑
  - [ ] 변형 입력(대소문자/공백) 처리
  - [ ] 알 수 없는 값 → 처리 정책 결정 및 검증(UNKNOWN Enum/기본값/예외 중 선택)

### 리스크 체크
- [ ] LLM이 만들어내는 값이 흔들려도 **정규화/UNKNOWN**으로 흡수되도록 했는가?

### 🔹 추가 (설계 강제 – TODO 1에서 이식)
- [ ] **Unknown intent/action 입력에 대한 처리 정책을 명시적으로 결정**

---

## core를 진짜 패키지로 만들기 (pyproject.toml) (2)
---
### 목표
ZiTTA core를 **진짜 Python 패키지**로 만들어 재사용/확장 기반 확보

### 완료 기준
- [ ] `pip install -e .` 후 **어디서든 `import zitta` 가능**
- [ ] CI/pytest 통과
- [ ] `python -m zitta`(4번)로 연결 가능한 기반 마련

### TODO
- [ ] 패키지 네이밍 확정
  - [ ] 권장: `zitta` (모듈명과 import 일관성)
- [ ] 레이아웃 선택
  - [ ] 권장: `src/zitta/...` (장기 안정)
  - [ ] 단기: 현재 레이아웃 유지 (나중에 다시 공사 가능성 큼)
- [ ] `pyproject.toml` 작성
  - [ ] project metadata(name, version, description, requires-python)
  - [ ] dependencies 정리 (runtime)
  - [ ] optional-dependencies: `dev` (pytest 등)
- [ ] 엔트리 파일 정리
  - [ ] 기존 `main.py` 역할을 어디에 둘지 결정(패키지 내부로 흡수 권장)
- [ ] 설치/동작 검증
  - [ ] `pip install -e .`
  - [ ] `python -c "import zitta; print(zitta.__version__)"` (버전 노출하면 좋음)
  - [ ] `pytest` 통과

### 리스크 체크
- [ ] 테스트가 `sys.path`/루트 경로에 기대고 있지 않은가?
- [ ] import 경로가 `core.*`와 `zitta.*`로 혼재되지 않는가?

---

## CLI 인터페이스 얹기 (python -m zitta "...") (4)
---
### 목표
ZiTTA를 **한 줄 명령으로 실행** 가능하게 만들기

### 완료 기준
- [ ] `python -m zitta "할 일 추가"`가 동작
- [ ] CLI는 core를 "우회"하지 않고 **core 파이프라인을 호출**
- [ ] 최소 스모크 테스트 포함

### MVP 스펙(과욕 금지)
- [ ] 입력: 단일 문자열(따옴표로 감싼 문장)
- [ ] 출력: 처리 결과를 stdout에 출력
- [ ] 에러: 사용자 친화 메시지 + non-zero exit code

### TODO
- [ ] `zitta/__main__.py` 추가
  - [ ] argv 파싱 (빈 입력 처리 포함)
  - [ ] core 호출(예: `process_text(text)` 같은 단일 진입점 만들기)
- [ ] "단일 진입점" 함수 마련
  - [ ] CLI/GUI/테스트가 공용으로 쓸 수 있는 함수 1개로 정리
- [ ] 스모크 테스트
  - [ ] `python -m zitta ""` → 도움말/사용법
  - [ ] `python -m zitta "할 일 추가 ..."` → 성공
  - [ ] 알 수 없는 명령 → 에러 메시지

### 리스크 체크
- [ ] CLI가 커지기 시작하면 유지보수 지옥이다 → **MVP만** 하고 멈출 것

---

## 운영 체크리스트
---
- [ ] 각 작업 끝날 때마다 **완료 기준(Definition of Done)** 체크
- [ ] PR/커밋 단위는 "한 가지 의도"만 담기 (Enum / 패키징 / CLI 혼합 금지)
- [ ] 3번(Enum) 끝나기 전엔 4번(CLI) 스펙 확장 금지

---

## 리스크 & 기술 부채 (추적용 메모)
---
- [ ] `google.generativeai` → `google.genai` 마이그레이션
- [ ] Python 3.11+ 전환 계획 (2026-10-04 이전)
- [ ] GitHub Actions pip 캐시 비대 문제 (필요 시 정리)

---
