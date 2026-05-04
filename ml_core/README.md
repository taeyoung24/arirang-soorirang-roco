# MDD Service

MDD 모델 `checkpoint_mdd_sjr.pt`를 사용해서 추론을 제공하는 분리형 서비스입니다.

## 구조

- `app/server.py`: 외부 API 게이트웨이
- `app/inference_server.py`: 내부 추론 서비스
- `app/pipeline.py`: 전처리, manifest 생성, 후처리
- `app/fairseq_runner.py`: fairseq 모델을 프로세스 시작 시 한 번만 로드하는 in-process runner
- `assets/dict.phn.txt`: 추론용 phoneme dictionary
- `docker-compose.yml`: `api` + `inference` 컨테이너 실행 정의

## 입력 계약

이 서비스는 API 입력으로 원문 문장을 받습니다. 서버 내부에서 `g2p -> 자모 분해`를 수행한 뒤 원래 MDD 모델과 비교합니다.

예:

- 원문: `옷을 입어요`
- 서버 내부 canonical phonemes 예시: `ㅇㅗㅅㅇㅡㄹㅇㅣㅂㅇㅓㅇㅛ`

## 실행

```powershell
docker compose up --build
```

외부 API 포트는 `8000`입니다. `inference` 컨테이너는 내부 네트워크에서만 `8080`으로 열립니다.

현재 기본 경로는 공식 CUDA 베이스 위에서 원본 MDD 추론 환경을 재현하는 방식입니다. 다음 항목을 원본 이미지와 맞추는 데 초점을 둡니다.

- 공식 CUDA 베이스 위에 `conda env(main)` 구성
- `Python 3.9.12`
- 원본 이미지에서 추출한 패키지 버전 락 기반 설치
- `fairseq` commit `a075481d0de112aee2d79f40ac3ab0eca37214d8`
- `flashlight` egg를 site-packages에 원본과 유사한 형태로 배치

원본 이미지에서 추출한 런타임 메모는 [docs/original-image-runtime.md](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/docs/original-image-runtime.md:1)에 정리했습니다.
현재 컨테이너는 `flashlight` 네이티브 라이브러리 탐색과 `examples.speech_recognition` import를 위해 `LD_LIBRARY_PATH`, `PYTHONPATH`를 함께 사용합니다.
원본 이미지에서 실제 런타임 명세를 덤프하려면 아래 스크립트를 실행하면 됩니다.

```powershell
.\scripts\extract-original-runtime.ps1
```

결과는 `ml_core/docs/original-image-dump/` 아래에 저장됩니다. 재구성 절차 개요는 [docs/original-image-rebuild-plan.md](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/docs/original-image-rebuild-plan.md:1)에 정리했습니다.

## 모델 파일 준비

- 모델 가중치 파일 `checkpoint_mdd_sjr.pt`는 Git으로 추적하지 않습니다.
- 실행 전에 모델 파일을 `ml_core/models/checkpoint_mdd_sjr.pt` 경로에 직접 배치해야 합니다.
- 현재 `docker-compose.yml`은 `./models`를 컨테이너의 `/opt/mdd/checkpoints`로 마운트합니다.

## API

헬스체크:

```powershell
curl http://localhost:8000/health
```

예측 요청:

```powershell
curl -X POST http://localhost:8000/predict `
  -F "script=옷을 입어요" `
  -F "audio=@.\sample.wav"
```

## CLI

```powershell
.venv\Scripts\python.exe main.py .\sample.wav "옷을 입어요"
```

## 주의

- `api` 컨테이너는 요청 프록시만 담당합니다.
- `inference` 컨테이너가 모델을 시작 시 한 번 로드한 뒤 요청마다 재사용합니다.
- 현재 compose는 `inference` 서비스에 `runtime: nvidia`를 사용합니다.
- 호스트 NVIDIA 드라이버가 컨테이너 CUDA와 맞지 않으면 CPU로 돌거나 실패할 수 있습니다.
