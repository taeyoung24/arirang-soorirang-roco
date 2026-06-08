# Whisper Pronunciation Service

Whisper 전사 결과를 target script와 비교해 발음 평가를 제공하는 `ml_core` 서비스입니다. 기존 MDD/fairseq 음소 디코더는 이 브랜치에서 API 경로와 compose 실행 구성에서 제거되었습니다.

## 구조

- `app/server.py`: 외부 API 게이트웨이
- `app/whisper_client.py`: `faster-whisper` 기반 ASR 클라이언트
- `app/whisper_pronunciation_analysis_service.py`: Whisper 전사 일치도, prosody, audio quality 기반 발음 분석
- `app/aligner_server.py`: Qwen3 강제정렬 서비스
- `app/acoustic_schemas.py`: 음향 분석 + LLM 해석용 구조화 스키마
- `docker-compose.yml`: `api` + `aligner` + `minio` 컨테이너 실행 정의

## 입력 계약

이 서비스는 API 입력으로 target script와 사용자 음성을 받습니다. 서버는 Whisper 전사 결과를 정규화한 target script와 비교하고, 일치 정도를 segmental 점수의 주 근거로 사용합니다. 기존처럼 `canonical_phonemes`/`predicted_phonemes` 필드는 API 호환을 위해 한글 자모 분해 문자열로 채웁니다.

예:

- 원문: `옷을 입어요`
- Whisper 전사: `옷을 입어요`
- canonical/predicted phonemes 예시: `ㅇㅗㅅㅇㅡㄹㅇㅣㅂㅇㅓㅇㅛ`

## 실행

```powershell
docker compose up --build
```

외부 API 포트는 `8000`입니다. Whisper 모델은 API 컨테이너에서 로드하며, 기본 모델은 `small`입니다.

## Whisper 설정

- `MDD_WHISPER_MODEL` 기본값: `small`
- `MDD_WHISPER_DEVICE` 기본값: `cuda`
- `MDD_WHISPER_COMPUTE_TYPE` 기본값: `int8_float16`
- `MDD_WHISPER_LANGUAGE` 기본값: `ko`
- `MDD_WHISPER_BEAM_SIZE` 기본값: `5`

## API

헬스체크:

```powershell
curl http://localhost:8000/health
```

발음 분석 요청:

```powershell
curl -X POST http://localhost:8000/analyze-pronunciation-llm `
  -F "script=옷을 입어요" `
  -F "feedback_language=ko" `
  -F "use_tts_reference=true" `
  -F "debug=false" `
  -F "audio=@.\sample.wav"
```

사용자 청취용 TTS asset 생성 또는 기존 위치 반환:

```powershell
curl -X POST http://localhost:8000/tts-assets/generate `
  -F "text=옷을 입어요" `
  -F "language=Korean"
```

현재 분석 API는 다음 단계를 수행합니다.

- Whisper 전사로 `predicted_text` 생성
- target script와 Whisper transcript를 정규화한 뒤 문자 단위 일치도 계산
- `Qwen/Qwen3-ForcedAligner-0.6B`로 word/character timestamp 정렬
- `use_tts_reference=true`이면 TTS reference를 자동 생성/캐싱하고, cached TTS reference alignment와 사용자 timing을 비교해 늘어짐/중간 공백 후보 생성
- 앱 표시용 0-100 휴리스틱 종합 점수를 `pronunciation_score`로 노출
- Whisper 전사 불일치, prosody, audio quality를 중심으로 오류 후보 생성
- `MDD_GEMINI_API_KEY`가 있으면 구조화 evidence를 기준으로 Gemini API 피드백 생성

`language`는 forced aligner에 넘기는 발화 언어이며 기본값은 `Korean`입니다.
`feedback_language`는 LLM 피드백 언어이며 기본값은 `ko`입니다. 예: `ko`, `en`, `ja`, `zh-CN`, `Spanish`.
`debug`는 상세 응답 여부이며 기본값은 `false`입니다.

주의:

- 강제정렬은 별도 `aligner` 컨테이너에서 수행됩니다.
- 분석 API는 강제정렬에 실패하면 fallback 분석을 반환하지 않고 오류를 반환합니다.
- Whisper는 음소 단위 MDD 모델이 아니므로 segmental 평가는 전사 일치도 기반 휴리스틱입니다.
- `pronunciation_score.overall`은 Whisper transcript agreement와 timing/prosody evidence를 합친 휴리스틱 점수입니다. `audio_quality` 점수는 별도로 표시되며 overall에는 반영되지 않습니다.
- `model_score`는 Whisper confidence proxy이며 calibrated pronunciation confidence가 아닙니다.

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

- `api` 컨테이너는 Whisper ASR, timing/prosody 분석과 Gemini 해석을 담당합니다.
- 기본 Whisper 실행은 GPU `cuda` + `int8_float16`입니다.
- `api` 컨테이너는 `nvidia-cublas-cu12`와 `nvidia-cudnn-cu12` wheel 런타임을 사용합니다.
- `aligner` 컨테이너가 Qwen3 forced aligner를 시작 시 로드한 뒤 요청마다 재사용합니다.
- 현재 compose는 `api`와 `aligner` 서비스에 GPU 런타임을 사용합니다.
