# Frontend 세팅 가이드 (pnpm)

## 개발 환경 구축
`frontend` 디렉토리 내의 프로젝트 환경을 설정하려면 아래 명령어를 순서대로 실행하세요.

```bash
# 1. 디렉토리 이동
cd frontend

# 2. pnpm 설치 (아직 설치되지 않은 경우)
npm install -g pnpm

# 3. 프로젝트 의존성 설치
pnpm install
```

> [!NOTE]
> 현재 프로젝트에는 별도로 설정해야 할 **환경 변수(.env)**가 존재하지 않습니다. 추가적인 환경 설정 없이 바로 실행 가능합니다.

## 디렉토리 구조 및 실행 방식
본 프론트엔드 프로젝트는 `pnpm` 패키지 매니저를 기반으로 구성되어 있습니다.

### 디렉토리 구조
프로젝트 루트 기준 `frontend` 디렉토리 구성은 다음과 같습니다.
```text
frontend/               
├── src/                
│   ├── api/            <-- api 호출 관련
│   ├── assets/         <-- 이미지, 폰트 등 정적 자원
│   ├── components/     <-- 재사용 가능한 공통 UI 컴포넌트
│   └── pages/          <-- 화면별 라우팅 컴포넌트
├── package.json
└── pnpm-lock.yaml
```

### 스크립트 실행
개발 및 빌드 작업을 진행할 때는 `frontend` 디렉토리 내에서 `pnpm run` 명령을 사용합니다.

**주요 실행 명령어 예시:**
```bash
# 1. 로컬 개발 서버 실행
pnpm dev

# 2. 프로덕션 빌드
pnpm build
```

## 배포
본 프로젝트는 **Vercel**을 통해 배포 및 호스팅되고 있습니다.

- **배포 URL:** [https://arirang-soorirang-roco.vercel.app/](https://arirang-soorirang-roco.vercel.app/)
- **자동 배포:** `frontend/production` 브랜치에 코드가 push되면 Vercel을 통해 자동으로 빌드 및 배포가 진행됩니다.

