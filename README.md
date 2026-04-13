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

## 프로젝트 컨벤션 & 협업 가이드
### 브랜치 전략 (Customized Git Flow)
본 프로젝트는 루트 디렉토리가 아닌 각 영역별 폴더(backend, frontend 등) 내에서 환경을 초기화하는 구조를 가집니다. 하지만 버전 추적은 전체 Repository(main) 기준으로 이루어지므로, 일반적인 Git Flow를 그대로 적용 시 형상 관리 비용이 지나치게 커집니다. 따라서 이를 경량화하고 응용한 다음의 브랜치 전략을 사용합니다.

1.  **`main`**: 프로젝트 전체 종합 및 레포지토리 간판 역할을 하는 메인 브랜치입니다.
2.  **`integration`**: 서로 다른 영역(frontend, backend 등) 간의 변경 사항을 종합하여 커밋을 추적하는 브랜치이며, 최종적으로 `main`의 병합 대상이 됩니다.
3.  **`frontend/production`, `backend/production` (영역별 production)**: 커밋 시 자동 배포가 이루어지는 브랜치입니다. 직접 커밋하지 않으며 오직 `fast-forward` 또는 `reset`을 통해서만 업데이트를 진행합니다. 추후 프론트/백엔드 외의 새로운 영역 등장 시 동일한 네이밍 패턴(`영역명/production`)을 생성하여 사용합니다.
4.  **`frontend/develop`, `backend/develop` (영역별 develop)**: `integration`으로 병합되기 전, 해당 영역의 변경 사항을 일차적으로 종합하는 브랜치입니다.

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

- [Frontend 세팅 가이드](#)
- [Backend 세팅 가이드](#)
- [Content Data 세팅 가이드 (uv)](docs/content-data-instruction.md)


## 협업 규칙
- 📲 디스코드 등 커뮤니케이션 채널을 수시로 확인하기
- 🧩 어려운 일이 생기면 혼자 고민하지 말고 꼭 공유하기 (함께 고민하면 더 빨리 해결할 수 있어요!)
- 🗣️ 서로의 의견을 존중하고 배려하는 말투로 소통하기
- 🎉 힘들어도 재미있게, 즐기면서 프로젝트 진행하기
- ⏰ 마감 기한을 잘 지키기 (일정이 어려울 땐 미리 말해서 조정하기)

### 질문 가이드
1. 직접 찾아보기
    - Google, ChatGPT, 공식 문서 등
    - 영어 검색 권장 → 어려우면 DeepL 등 번역기 활용

2. 구체적으로 이야기하기
    - 현재 상황(어디서, 어떤 문제가 발생했는지)
    - 내가 알고 있는 것
    - 참고한 자료나 검색한 내용
    - 이해되지 않는 부분
    - 본인이 시도한 해결 방법

3. 해결한 내용은 팀에 공유하기!

### Pull Request (PR) 규칙
- 2명 이상 Approve 후 Merge
- 리뷰 확인하면 이모지 남기기
- 리뷰 반영 시 작업 단위로 커밋 나눠서, 리뷰 댓글에 커밋 번호 남겨서 알려주기
- 리뷰 반영 후에는 re-request review 하기

### 코드 리뷰 가이드
- 부드러운 어조 사용하기
- 구체적인 피드백 + 참고 링크 함께 작성하기
- 궁금한 부분도 함께 질문하기
- 다른 리뷰어가 잘 남겼다고 리뷰 안 남기지 말고 간단하게라도 코멘트랑 남기고 approve/request change 하기
- LGTM 지양하기