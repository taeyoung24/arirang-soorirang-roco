# arirang-soorirang-roco

## 개요

**한글을 배우고자 하는 고려인들을 위한 한국어 발음 교정 시스템**

'아리랑 수리랑(Arirang Soorirang)'은 한국어 소통에 어려움을 겪는 고려인 학습자를 위한 맞춤형 통합 한국어 학습 시스템입니다. 이 프로젝트는 학습자가 가장 까다로워하는 '문맥에 따른 다의어 이해'와 '발음 연습 및 교정'을 분리하지 않고 하나의 반복적인 학습 루프로 연결한 것이 핵심입니다. 학습자는 실생활 상황 기반의 퀴즈로 단어의 뜻을 구별하고, 곧바로 이어지는 섀도잉 훈련을 통해 실질적인 발음 피드백을 받습니다. 이를 통해 학습의 심리적 부담은 줄이면서 실전 의사소통 능력을 효과적으로 기를 수 있으며, 향후 정교한 발음 평가 로직과 개인화된 학습 기록 관리까지 지원하는 종합 교육 플랫폼으로의 발전을 목표로 합니다.


## Tech Role

[![](https://img.shields.io/badge/Python-14354C?style=for-the-badge&logo=python&logoColor=white)](#)
[![](https://img.shields.io/badge/LangChain-3a5953?style=for-the-badge&logo=langchain&logoColor=white)](#)
[![](https://img.shields.io/badge/Discord-50565F?style=for-the-badge&logo=discord&logoColor=white)](#)
[![](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![](https://img.shields.io/badge/Linux-C76D8E?style=for-the-badge&logo=linux&logoColor=white)](#)
[![](https://img.shields.io/badge/Openai-1A1B1B?style=for-the-badge&logo=openai&logoColor=white)](#)


## 그라운드 룰

### 업무 관리 - GitHub Issues
기본적으로 GitHub Repository의 Issue 기능을 활용하여 Todo List를 Task의 일환으로 추적합니다. 모든 업무 진행 상황을 체계적으로 관리하고 공유합니다.

### 회의 - Discord
매주 월요일 17:30 ~ 18:30에 정기 회의를 진행합니다. 효율적인 업무 환경을 위해 비대면 음성 회의로 진행하며, 회의 중 필요한 경우 Notion을 활용하여 내용을 실시간으로 공유하고 기록합니다.


## 프로젝트 컨벤션

### 프로젝트 영역 정의
| 영역(Directory) | 설명 | 비고 |
| --- | --- | --- |
| `frontend` | 사용자 인터페이스(UI) 및 클라이언트 로직 담당 | React 기반 |
| `backend` | 메인 비즈니스 로직 및 API 서버 | FastAPI 기반 |
| `content_data` | 학습용 원천 데이터 관리 및 데이터 정제/검증 스크립트 | `uv` 파이썬 환경 |
| `ml_core` | 음성 인식 AI 모델 연구 및 추론(Inference) 서빙 엔진 | GPU 워커 독립 동작 |

### 브랜치 전략 (Customized Git Flow)
> 본 프로젝트는 루트 디렉토리가 아닌 각 영역별 폴더(backend, frontend 등) 내에서 환경을 초기화하는 구조를 가집니다. 하지만 버전 추적은 전체 Repository(main) 기준으로 이루어지므로, 일반적인 Git Flow를 그대로 적용 시 형상 관리 비용이 지나치게 커집니다. 따라서 이를 경량화하고 응용한 다음의 브랜치 전략을 사용합니다.

1.  **`main`**: 프로젝트 전체 종합 및 레포지토리 간판 역할을 하는 메인 브랜치입니다.
2.  **`integration`**: 서로 다른 영역(frontend, backend 등) 간의 변경 사항을 종합하여 커밋을 추적하는 브랜치이며, 최종적으로 `main`의 병합 대상이 됩니다.
3.  **`frontend/production`, `ml_core/production` 등 (영역별 production)**: 커밋 시 자동 배포가 이루어지는 브랜치입니다. 직접 커밋하지 않으며 오직 `fast-forward` 또는 `reset`을 통해서만 업데이트를 진행합니다. 추후 새로운 영역 등장 시 동일한 네이밍 패턴(`영역명/production`)을 생성하여 사용합니다.
4.  **`frontend/develop`, `ml_core/develop` 등 (영역별 develop)**: `integration`으로 병합되기 전, 해당 영역의 변경 사항을 일차적으로 종합하는 브랜치입니다.

**브랜치 네이밍 컨벤션 일반 룰 (영역 구분 없이 적용)**
| 유형 | 형식 | 예시 |
| --- | --- | --- |
| 기능 추가 | feature/#<이슈번호>/<기능명>	| feature/#12/user-login-page |
| 버그 수정 | fix/#<이슈번호>/<기능명> |	fix/#34/fix-login-redirect |
| 리팩토링 | refactor/#<이슈번호>/<기능명> |	refactor/#21/refactor-user-service |
| 긴급 패치 | hotfix/#<이슈번호>/<기능명>	| hotfix/#88/fix-navbar-crash |

- 기능명에는 `kebab-case`를 사용합니다.
- 이슈 번호는 GitHub Issue와 반드시 연동합니다.
- 위 일반 룰에 따라 생성된 작업 브랜치들은 **되도록 각 영역별 `develop` 브랜치에서 먼저 종합한 뒤 `integration` 브랜치로 병합해 나가는 것을 권장**하지만, 경우에 따라 `integration` 브랜치로 **직접 병합도 가능**합니다.

### 커밋 컨벤션
커밋 메시지는 '영문 접두어 + 영/한 내용' 구성의 Angular 포맷을 따릅니다.

| 유형 | 형식 |
| --- | --- |
| prefix | 설명 |
| feat | 새로운 기능 추가 |
| fix | 버그 수정 |
| docs | 문서 수정 (README 등) |
| design | UI/스타일 변경 |
| refactor | 기능 변경 없이 코드 리팩토링|
| test | 테스트 코드 추가 변경 |
| chore | 설정, 빌드, 패키지 등 작업 (프로덕션 코드 영향 없음) |
| hotfix | 배포 후 긴급 수정 |

**작성 예시**
```
feat: 마이페이지 UI 구현
fix: 로그인 시 토큰 누락 오류 수정
refactor: userService 코드 정리
design: 버튼 hover 효과 추가
docs: README에 브랜치 전략 설명 추가
hotfix: 배포 후 500 에러 응급 조치
```


## 개발 환경 세팅 가이드

본 프로젝트는 루트 디렉토리가 아닌 각 영역별 디렉토리 내부에서 개별적으로 환경을 초기화하고 실행해야 합니다. 자세한 환경 세팅 가이드는 아래의 각 영역별 링크를 참고해 주십시오.

- [Backend 세팅 가이드](#)
- [Content Data 세팅 가이드](docs/content-data-instruction.md)
- [Frontend 세팅 가이드](#)
- [ML Core 세팅 가이드](#)


## 협업 규칙

- **커뮤니케이션**: Discord 등 지정된 채널 상시 확인 및 신속한 응답
- **이슈 공유**: 병목 지점 발생 시 즉시 공유 및 공동 해결 지향
- **전문성 유지**: 상호 존중 기반의 구성원 간 예의 준수
- **일정 관리**: 업무 마감 기한 엄수 및 일정 변동 시 사전 협의
- **할 일 관리**: 모든 TODO List는 GitHub Issue로 등록하여 투명하게 관리 및 추적

### Pull Request (PR)
- **빠른 병합**: 최소 1인의 Approve 확보 시 Merge 가능
- **유연한 관리**: 단순 UI 변경 및 사소한 오타/버그 수정은 자체 병합(Self-Merge) 후 사후 공유 허용
- **커밋 중심 관리**: PR 본문 요약 대신 명확한 커밋 메시지를 통해 변경 사항 파악. 본문에는 해결 이슈(`Resolve #이슈번호`) 및 리뷰어 필독 특이사항만 기재

### 코드 리뷰 가이드
- **신속성 우선**: 치명적인 기능 결함이나 구조적 문제가 없다면 즉각적인 승인 권장
- **피드백 효율화**: 기록 보존이 불필요한 사소한 의견이나 휘발성 코멘트는 GitHub 대신 Discord DM/채널 활용