# arirang-soorirang-roco
## 한글을 배우고자 하는 고려인들을 위한 한국어 발음 교정 시스템


## Tech Role
[![](https://img.shields.io/badge/Python-14354C?style=for-the-badge&logo=python&logoColor=white)](#)
[![](https://img.shields.io/badge/LangChain-3a5953?style=for-the-badge&logo=langchain&logoColor=white)](#)
[![](https://img.shields.io/badge/Discord-50565F?style=for-the-badge&logo=discord&logoColor=white)](#)
[![](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![](https://img.shields.io/badge/Linux-C76D8E?style=for-the-badge&logo=linux&logoColor=white)](#)
[![](https://img.shields.io/badge/Openai-1A1B1B?style=for-the-badge&logo=openai&logoColor=white)](#)

## 그라운드 룰
### 업무 관리
Notion
업무 내용을 문서화해서 저장해놨어요. 회의록이나 팀 규칙, 일정 등 노션에 정리해서 일괄적으로 확인할 수 있어요.

### 회의
Discord
주로 Discord를 활용해서 회의를 진행해요. 온라인 회의인 만큼 집중력이 분산되는 것을 막기 위해 카메라를 킨 상태로 참여해요. 회의를 진행하면서 Notion에 실시간으로 정리하기 때문에 원활한 교류가 가능해요.

## 프로젝트 컨벤션 & 협업 가이드
### 브랜치 전략
Git Flow
<img width="2196" height="1364" alt="image" src="https://github.com/user-attachments/assets/2e6427b2-c087-48c3-9315-f2eeee6625fc" />

브랜치 네이밍 컨벤션
| 유형 | 형식 | 예시 |
| --- | --- | --- |
| 기능 추가 | feature/#<이슈번호>/<기능명>	| feature/#12/user-login-page |
| 버그 수정 | fix/#<이슈번호>/<기능명> |	fix/#34/fix-login-redirect |
| 리팩토링 | refactor/#<이슈번호>/<기능명> |	refactor/#21/refactor-user-service |
| 긴급 패치 | hotfix/#<이슈번호>/<기능명>	| hotfix/#88/fix-navbar-crash |
- 기능명에는 kebab-case 사용
- 이슈 번호는 GitHub 이슈와 연동

### 커밋 컨벤션
| prefix | 설명 |
| feat | 새로운 기능 추가 |
| fix | 버그 수정 |
| docs | 문서 수정 (README 등) |
| design | UI/스타일 변경 |
| refactor | 기능 변경 없이 코드 리팩토링|
| test | 테스트 코드 추가 변경 |
| chore | 설정, 빌드, 패키지 등 작업 (프로덕션 코드 영향 없음) |
| hotfix | 배포 후 긴급 수정 |

feat: 마이페이지 UI 구현
fix: 로그인 시 토큰 누락 오류 수정
refactor: userService 코드 정리
design: 버튼 hover 효과 추가
docs: README에 브랜치 전략 설명 추가
hotfix: 배포 후 500 에러 응급 조치

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
