# Acoustic Analysis Implementation Status

## Scope

This document records what has actually been implemented on the `feat-acoustic-analysis-llm` branch.
It is separate from the design document and focuses on current behavior, validation status, and known limitations.

## Implemented Components

- External API gateway: [app/server.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/server.py:1)
- Internal inference service: [app/inference_server.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/inference_server.py:1)
- Qwen3 forced aligner service: [app/aligner_server.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/aligner_server.py:1)
- Acoustic analyzer: [app/acoustic_analysis.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/acoustic_analysis.py:1)
- Analysis service orchestration: [app/pronunciation_analysis_service.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/pronunciation_analysis_service.py:1)
- Structured response schema: [app/acoustic_schemas.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/acoustic_schemas.py:1)
- Gemini integration: [app/gemini_client.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/gemini_client.py:1)
- Aligner client: [app/aligner_client.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/aligner_client.py:1)
- Compose topology: [docker-compose.yml](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/docker-compose.yml:1)

## Current Request Flow

`POST /analyze-pronunciation`

1. API receives `script` and `audio`.
2. API calls internal `/predict` on the inference service.
3. API calls Qwen3 forced aligner with the same audio and script.
4. Analyzer builds word, syllable, and approximate phoneme spans.
5. Analyzer extracts heuristic acoustic and prosodic features.
6. Analyzer creates rule-based diagnostic candidates.
7. If Gemini is configured, structured evidence is sent for learner-facing feedback generation.

## Container Layout

- `api`
  - FastAPI gateway
  - acoustic feature extraction
  - diagnostic candidate generation
  - optional Gemini call
- `inference`
  - original fairseq-based MDD phoneme prediction
- `aligner`
  - `Qwen/Qwen3-ForcedAligner-0.6B`

## Implemented Endpoints

- `GET /health`
- `POST /predict`
- `POST /analyze-pronunciation`

## Implemented Error Handling

### Fixed issues

- The `NameError: name 'cls' is not defined` issue in `_canonical_syllable_groups` was fixed by changing the method to a classmethod in [app/acoustic_analysis.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/acoustic_analysis.py:346).
- Nested upstream error payload formatting was cleaned up in [app/server.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/server.py:26).
- Empty-phoneme inference results no longer surface as generic `500` errors from the inference service.

### Current behavior

If the audio contains no recognizable speech, the inference service now returns:

- HTTP `422`
- detail: `No recognizable speech was detected in the audio.`

This mapping is implemented in [app/inference_server.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/inference_server.py:18).

## Validation Performed

### Service health

Verified that the following services can all reach healthy state after startup:

- `api`
- `inference`
- `aligner`

Observed API health shape:

```json
{
  "status": "ok",
  "service_mode": "api",
  "inference_status": "ok",
  "aligner_status": "ok",
  "aligner_model_id": "Qwen/Qwen3-ForcedAligner-0.6B",
  "gemini_status": "disabled"
}
```

### End-to-end request validation

A temporary silent wav file was used to verify the non-speech path.

Observed result:

```json
{
  "detail": "No recognizable speech was detected in the audio."
}
```

This confirms:

- API routing works
- API to inference communication works
- inference to API error propagation works
- forced aligner startup does not block API health

## Known Limitations

- Forced alignment currently provides reliable word and character timing, but phoneme spans are still subdivided inside aligned syllable spans and remain approximate.
- Acoustic features are heuristic and lightweight. They are not a full phonetics-grade DSP stack.
- Vowel formant-related values are proxy features, not a robust formant-tracking pipeline.
- Gemini feedback is skipped unless `MDD_GEMINI_API_KEY` is configured.
- Real user speech has not yet been validated in this document; current recorded end-to-end check used silent audio to validate failure behavior.

## Operational Notes

- `inference` startup can take noticeable time after rebuild because the model and runtime stack initialize slowly.
- `api` may temporarily report `inference_status: "unreachable"` during inference startup; this is expected until the internal service binds to port `8080`.
- `aligner` is run as a separate service so API failures do not require model reloading on every request.

## Remaining Work

- Validate `/analyze-pronunciation` with real Korean speech input.
- Improve phoneme-level timing from approximate subdivision to a more defensible alignment strategy.
- Replace proxy vowel features with a stronger measurement pipeline.
- Add native baseline calibration and threshold tuning.
- Enable and test Gemini output with a real API key.
