# MDD Service

MDD 모델 `checkpoint_mdd_sjr.pt`를 사용해서 추론을 제공하는 분리형 서비스입니다.

## 구조

- `app/server.py`: 외부 API 게이트웨이
- `app/inference_server.py`: 내부 추론 서비스
- `app/aligner_server.py`: Qwen3 강제정렬 서비스
- `app/pipeline.py`: 전처리, manifest 생성, 후처리
- `app/fairseq_runner.py`: fairseq 모델을 프로세스 시작 시 한 번만 로드하는 in-process runner
- `app/acoustic_schemas.py`: 음향 분석 + LLM 해석용 구조화 스키마 초안
- `assets/dict.phn.txt`: 추론용 phoneme dictionary
- `docker-compose.yml`: `api` + `inference` + `aligner` 컨테이너 실행 정의

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
음향 분석 확장 설계 초안은 [docs/acoustic-analysis-llm-design.md](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/docs/acoustic-analysis-llm-design.md:1)에 정리했습니다.
현재 브랜치의 실제 구현 범위와 검증 상태는 [docs/acoustic-analysis-implementation-status.md](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/docs/acoustic-analysis-implementation-status.md:1)에 정리했습니다.

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

기본 음향 분석 요청:

```powershell
curl -X POST http://localhost:8000/analyze-pronunciation-basic `
  -F "script=옷을 입어요" `
  -F "feedback_language=ko" `
  -F "debug=false" `
  -F "audio=@.\sample.wav"
```

LLM 피드백 포함 분석 요청:

```powershell
curl -X POST http://localhost:8000/analyze-pronunciation-llm `
  -F "script=옷을 입어요" `
  -F "feedback_language=ko" `
  -F "debug=false" `
  -F "audio=@.\sample.wav"
```

현재 분석 API는 다음 단계를 수행합니다.

- 기존 MDD 추론으로 `predicted_phonemes` 생성
- `Qwen/Qwen3-ForcedAligner-0.6B`로 word/character timestamp 정렬
- 정렬 결과를 바탕으로 음절/음소 구간 생성
- lightweight acoustic feature extractor로 구간별 debug feature 추출
- in-process fairseq backend에서는 hypothesis decoder score를 `model_score`로 노출
- MDD 음소 mismatch를 중심으로 오류 후보 생성
- `/analyze-pronunciation-llm`에서는 `MDD_GEMINI_API_KEY`가 있으면 상위 진단과 관련 feature만 압축해 Gemini API로 한국어 피드백 생성
- `/analyze-pronunciation-basic`은 Gemini 키가 있어도 LLM을 호출하지 않음

`language`는 forced aligner에 넘기는 발화 언어이며 기본값은 `Korean`입니다.
`feedback_language`는 LLM 피드백 언어이며 기본값은 `ko`입니다. 예: `ko`, `en`, `ja`, `zh-CN`, `Spanish`.
`debug`는 상세 응답 여부이며 기본값은 `false`입니다. `debug=true`이면 전체 alignment, segment feature, phoneme score를 포함합니다.

주의:

- 강제정렬은 별도 `aligner` 컨테이너에서 수행됩니다.
- 음소 경계는 강제정렬된 음절 구간 내부에서 분할한 값이라, word/syllable보다 신뢰도가 낮습니다.
- acoustic feature는 debug/evidence 용도이며, 발음 오류 판정은 MDD phoneme edit alignment를 우선합니다.
- `model_score`는 calibrated GOP가 아니라 decoder hypothesis score이므로, 음소별 confidence로 쓰려면 추가 calibration/후처리가 필요합니다.

## CLI

```powershell
.venv\Scripts\python.exe main.py .\sample.wav "옷을 입어요"
```

## Gemini 설정

다음 환경변수를 설정하면 `/analyze-pronunciation-llm` 응답에 `llm_feedback`이 포함됩니다.

- `MDD_GEMINI_API_KEY`
- `MDD_GEMINI_MODEL` 기본값: `gemini-2.5-flash`
- `MDD_GEMINI_TIMEOUT_SECONDS` 기본값: `30`

## Forced Aligner 설정

기본 compose는 `Qwen/Qwen3-ForcedAligner-0.6B`를 별도 GPU 컨테이너로 띄웁니다.

- aligner 내부 모델 ID: `MDD_ALIGNER_MODEL_ID`
- api -> aligner 연결 주소: `MDD_ALIGNER_BASE_URL`
- 기본 언어: `MDD_ALIGNER_LANGUAGE` 기본값 `Korean`

공식 예시는 `qwen-asr` 패키지에서 `Qwen3ForcedAligner.align(audio, text, language)` 형태입니다.
참고:

- Qwen GitHub: https://github.com/QwenLM/Qwen3-ASR
- Hugging Face model: https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B

## 주의

- `api` 컨테이너는 음향 feature 추출과 Gemini 해석을 담당합니다.
- `inference` 컨테이너가 모델을 시작 시 한 번 로드한 뒤 요청마다 재사용합니다.
- `aligner` 컨테이너가 Qwen3 forced aligner를 시작 시 로드한 뒤 요청마다 재사용합니다.
- 현재 compose는 `inference` 서비스에 `runtime: nvidia`를 사용합니다.
- 현재 compose는 `aligner` 서비스에도 `runtime: nvidia`를 사용합니다.
- 호스트 NVIDIA 드라이버가 컨테이너 CUDA와 맞지 않으면 CPU로 돌거나 실패할 수 있습니다.
