# Pronunciation Analysis API Fields

This document explains the response fields for:

- `POST /analyze-pronunciation-llm`
- `POST /reference-cache`
- `POST /reference-cache/generate`
- `GET /reference-cache/{cache_key}`

By default, the analysis endpoint returns a compact response. Pass `debug=true` to include full alignments and phoneme scores.

## Request Fields

| Field | Required | Default | Description |
| --- | --- | --- | --- |
| `script` | yes | - | Target Korean sentence to evaluate. |
| `audio` | yes | - | Learner speech audio file. |
| `language` | no | `Korean` | Language name passed to the forced aligner. Usually omit this for Korean. |
| `feedback_language` | no | `ko` | Language used for LLM feedback text. Examples: `ko`, `en`, `ja`, `zh-CN`. |
| `reference_cache_key` | no | - | Cache key for a TTS reference audio/alignment entry. When provided, prosody diagnostics compare learner timing against this reference. If the key is missing and `use_tts_reference=true`, the API falls back to automatic TTS reference lookup/generation. |
| `use_tts_reference` | no | `true` | Generate or reuse a TTS reference automatically when no cache key is supplied, or when a supplied cache key cannot be found. |
| `debug` | no | `false` | If `true`, returns full diagnostic internals. If `false`, returns compact fields only. |

## Reference Cache

The reference cache stores TTS-generated answer audio and its Qwen forced alignment result in object storage. In Docker Compose this uses MinIO.

`POST /reference-cache` accepts:

| Field | Required | Default | Description |
| --- | --- | --- | --- |
| `script` | yes | - | Target script used to generate the TTS reference. |
| `audio` | yes | - | TTS reference audio, normally normalized WAV. |
| `alignment_json` | yes | - | Qwen forced alignment response JSON for the TTS reference audio. |
| `language` | no | `Korean` | Alignment language. |
| `tts_provider` | no | `unknown` | TTS provider name. |
| `tts_model` | no | `unknown` | TTS model or engine version. |
| `voice_id` | no | `default` | TTS voice identifier. |
| `speaking_rate` | no | `1.0` | TTS speaking rate used when generating the reference. |
| `audio_format` | no | `wav_16khz_mono` | Normalized audio format. |
| `aligner_model_id` | no | `Qwen/Qwen3-ForcedAligner-0.6B` | Aligner model used to create `alignment_json`. |
| `alignment_resolution_ms` | no | `80` | Aligner timestamp resolution. |

The cache key is a SHA-256 hash over normalized script, language, TTS provider/model/voice/rate, audio format, aligner model, aligner resolution, and cache schema version.

Objects are stored as:

```text
tts-reference/{cache_key}/reference.wav
tts-reference/{cache_key}/alignment.json
tts-reference/{cache_key}/manifest.json
```

`GET /reference-cache/{cache_key}` returns the manifest if the cache entry exists.

`POST /reference-cache/generate` accepts `script` and optional `language`. It generates a TTS reference audio file, runs Qwen forced alignment for that TTS audio, stores both objects in MinIO, and returns the manifest. The analysis endpoints call this path automatically when `use_tts_reference=true` and no `reference_cache_key` was supplied, or when the supplied key is not found.

## Top-Level Response Fields

| Field | Meaning |
| --- | --- |
| `script` | Original target sentence from the request. |
| `canonical_phonemes` | Target phoneme sequence generated from `script` by G2P and Hangul decomposition. Punctuation is removed. |
| `predicted_phonemes` | MDD model's predicted phoneme sequence. |
| `pronunciation_score` | Always-returned 0-100 heuristic pronunciation score summary. |
| `audio_quality` | Overall recording quality summary. |
| `phoneme_edits` | Edit-aligned mismatch summary between canonical and predicted phonemes. This is the primary error source. |
| `diagnostic_candidates` | Candidate pronunciation issues derived from `phoneme_edits` and supporting evidence. |
| `llm_feedback` | Learner-facing feedback. Present only on `/analyze-pronunciation-llm` when Gemini is configured. |
| `notes` | Operational notes and limitations for this analysis. |

The following fields are compacted unless `debug=true`:

| Field | Compact Behavior |
| --- | --- |
| `alignments` | Only issue-related phoneme/syllable units or a few word units are returned. |
| `predicted_phoneme_scores` | Only issue-related predicted phoneme scores are returned. |
| `target_phoneme_scores` | Only issue-related target phoneme scores are returned. |
| `syllable_candidate_scores` | Only issue-related syllable candidate scores are returned. |
| `prosody` | Removed in compact mode unless a top diagnostic candidate is prosodic. |
| `model_score` | Removed in compact mode. |

## Important Confidence Types

## `pronunciation_score`

This top-level score is returned by `/analyze-pronunciation-llm` in both compact and debug responses.

| Field | Description |
| --- | --- |
| `overall` | 0-100 combined score. Higher is better. |
| `segmental` | 0-100 score from target phoneme confidence when available, with edit-alignment fallback. |
| `prosody` | 0-100 timing/prosody score from speech duration ratio, pauses, and stretched intervals. |
| `audio_quality` | 0-100 recording quality score derived from reliability, clipping, and SNR. This is reported separately and does not affect `overall`. |
| `source` | Scoring implementation identifier. Currently `heuristic_v1`. |
| `note` | Calibration and interpretation note. |

The score is a deterministic heuristic intended for app display and rough ranking. `overall` combines segmental and prosody scores plus diagnostic penalties; it does not include audio quality. It is not an externally calibrated pronunciation grade.

## Error Behavior

The analysis endpoints require forced alignment. If the aligner service is unreachable, returns an upstream error, or returns no timing items, the request fails instead of returning a heuristic timing analysis.

Common cases:

| Case | HTTP status |
| --- | --- |
| Internal inference service unavailable | `502` |
| Forced aligner unavailable | `502` |
| Forced aligner returns no timing items | `502` |
| Upstream inference/aligner returns validation or runtime error | Same upstream status |

The API has several different confidence values. They do not mean the same thing.

| Field | Meaning |
| --- | --- |
| `alignments[].confidence` | Timing confidence for an alignment unit. It is not pronunciation confidence. Current phoneme timings are approximate subdivisions inside Qwen-aligned syllable spans. |
| `predicted_phoneme_scores[].confidence` | MDD posterior-derived confidence for a predicted phoneme segment. |
| `target_phoneme_scores[].confidence` | Confidence of the predicted segment aligned to a target phoneme. |
| `diagnostic_candidates[].confidence` | Diagnostic confidence after edit alignment and supporting evidence. |
| `llm_feedback.issues[].confidence` | LLM-generated wording confidence. This should be treated as presentation-level confidence, not raw model confidence. |

## `audio_quality`

| Field | Description |
| --- | --- |
| `snr_db` | Estimated signal-to-noise ratio. |
| `clipping_detected` | Whether peak amplitude suggests clipping. |
| `voiced_ratio` | Rough voiced/non-noisy ratio estimate. |
| `noise_floor_db` | Estimated noise floor from the tail portion of the audio. |
| `overall_reliability` | `high`, `medium`, or `low` reliability summary for acoustic interpretation. |

## `phoneme_edits`

This is the main mismatch representation. It uses edit alignment, so a single deletion does not shift all later phonemes into substitutions.

| Field | Description |
| --- | --- |
| `edit_type` | `substitution`, `insertion`, or `deletion`. |
| `expected` | Expected canonical phoneme. |
| `actual` | Predicted phoneme, if present. |
| `expected_index` | Index in `canonical_phonemes`. |
| `actual_index` | Index in `predicted_phonemes`. |
| `context` | Nearby canonical phonemes around the edit. Useful when the same phoneme appears multiple times. |
| `syllable` | Canonical syllable containing the edit, when available. |
| `syllable_index` | Index of the syllable containing the edit. |

Example:

```json
{
  "edit_type": "deletion",
  "expected": "ㅎ",
  "expected_index": 6,
  "context": "ㅜㄹㅎㅏㄱ",
  "syllable": "하",
  "syllable_index": 3
}
```

This means the `ㅎ` in `하` was missing from the MDD predicted phoneme sequence.

## `alignments`

Alignment units connect text units to time spans.

| Field | Description |
| --- | --- |
| `start_ms`, `end_ms` | Time span in milliseconds. |
| `confidence` | Timing confidence, not pronunciation confidence. |
| `label` | Unit label. |
| `unit_type` | `word`, `syllable`, or `phoneme`. |
| `expected_label` | Expected label. |
| `observed_label` | Predicted/observed label after edit alignment, if available. |
| `source` | `forced` or `heuristic`. |

Qwen forced alignment provides word/character or syllable-like spans. Phoneme spans are currently subdivided inside syllable spans, so phoneme timing is approximate.

## `prosody`

Prosody is computed from Qwen forced alignment when aligned word and syllable units are available. If `reference_cache_key` is supplied, timing diagnostics are based on comparison against the cached TTS reference alignment. The thresholds are intentionally lenient for non-native Korean learners; the TTS reference is a baseline, not a required native-speed target. Without a TTS reference, prosody values may be returned but prosodic diagnostic candidates are not emitted.

| Field | Description |
| --- | --- |
| `timing_source` | `forced_alignment`, `acoustic`, or `none`. |
| `speech_rate_syllables_per_second` | Expected syllables divided by the aligned speech span. |
| `articulation_rate_syllables_per_second` | Expected syllables divided by aligned speech span after removing detected interior pauses. |
| `expected_syllable_count` | Number of aligned syllable units used for rate calculation. |
| `speech_duration_ms` | Time from the first aligned word to the last aligned word. |
| `leading_silence_ms`, `trailing_silence_ms` | Silence before/after the aligned speech span. These are not treated as slow pronunciation. |
| `interior_pause_count`, `interior_pause_total_ms` | Count and total duration of word-gap pauses inside the utterance. |
| `longest_interior_pause_ms` | Longest Qwen-aligned gap between adjacent words/tokens. |
| `pause_intervals` | Start/end/duration for detected interior pauses. |
| `slowest_aligned_unit` | Word/token with the largest duration per syllable. |
| `slowest_aligned_unit_ms_per_syllable` | Duration per syllable for `slowest_aligned_unit`. |
| `rate_reliability` | Reliability of rate and pause calculations. |
| `reference_timing_source` | `tts_reference` when a cached TTS reference was used. |
| `reference_speech_duration_ms` | Speech span of the cached TTS reference. |
| `speech_duration_ratio` | Learner speech duration divided by reference speech duration. |
| `reference_duration_comparisons` | Per-syllable/word learner duration vs reference duration. |
| `reference_pause_comparisons` | Learner word-gap pauses vs reference word-gap pauses. |

## `predicted_phoneme_scores`

These scores are derived from the MDD model's frame-level emissions and Viterbi path.

| Field | Description |
| --- | --- |
| `phoneme` | Predicted phoneme. |
| `predicted_index` | Index in the predicted phoneme sequence. |
| `confidence` | Mean posterior over frames assigned to this predicted phoneme segment. |
| `frame_start`, `frame_end` | MDD frame range for the predicted segment. |
| `frame_count` | Number of frames in the segment. |

This is useful for predicted phonemes, but it does not directly score a deleted target phoneme.

## `target_phoneme_scores`

These scores align canonical target phonemes to predicted Viterbi segments.

| Field | Description |
| --- | --- |
| `phoneme` | Target phoneme. |
| `canonical_index` | Index in the canonical phoneme sequence. |
| `edit_type` | Edit relation: `match`, `substitution`, `deletion`, or `insertion`. |
| `predicted_phoneme` | Predicted phoneme aligned to the target, if any. |
| `predicted_index` | Predicted phoneme index, if any. |
| `target_posterior` | Mean posterior of the target phoneme over the aligned predicted segment. |
| `competing_posterior` | Mean strongest competing posterior over the same segment. |
| `gop_like_score` | Log posterior ratio: `log(target) - log(competing)`. Higher is better for the target. |
| `confidence` | Confidence of the aligned predicted segment. |
| `note` | Explanation or limitation. |

For deletion edits, there may be no predicted segment. In that case posterior fields may be absent.

## `syllable_candidate_scores`

This field is used to validate deletion candidates at syllable level.

For example, if the target syllable is `하` and MDD predicted only `ㅏ`, the API compares:

- target sequence: `["ㅎ", "ㅏ"]`
- deletion alternative: `["ㅏ"]`

| Field | Description |
| --- | --- |
| `syllable` | Canonical syllable being evaluated. |
| `syllable_index` | Syllable index in the sentence. |
| `start_phoneme_index`, `end_phoneme_index` | Canonical phoneme span for the syllable. |
| `target_sequence` | Full canonical phoneme sequence for the syllable. |
| `alternative_sequence` | Candidate sequence after deletion. |
| `target_ctc_logprob` | CTC log-likelihood of the full target sequence. |
| `alternative_ctc_logprob` | CTC log-likelihood of the deletion alternative. |
| `logprob_margin` | `alternative_ctc_logprob - target_ctc_logprob`. Positive means the deletion alternative is more likely. |
| `confidence` | Sigmoid-transformed margin. |
| `note` | Explains skipped or unreliable comparisons. |

If the aligned frame window is too short, the comparison is skipped and only `note` is returned.

## `diagnostic_candidates`

These are pronunciation issue candidates selected by deterministic rules and model evidence.

| Field | Description |
| --- | --- |
| `diagnosis_code` | Machine-readable issue type. |
| `category` | `segmental`, `prosodic`, or `quality`. |
| `target_unit` | Target phoneme or unit. |
| `severity` | `low`, `medium`, or `high`. |
| `confidence` | Diagnostic confidence, not raw model posterior. |
| `evidence_keys` | Which evidence sources were used. |
| `rationale` | Short explanation of the diagnosis. |

Common codes:

| Code | Meaning |
| --- | --- |
| `segmental_deletion` | Expected phoneme was missing from the predicted sequence. |
| `segmental_insertion` | Extra phoneme appeared in prediction. |
| `segmental_substitution` | Expected phoneme was decoded as another phoneme. |
| `aspiration_insufficient` | Aspirated consonant was decoded closer to a lenis consonant. |
| `vowel_quality_shift` | Vowel was decoded as another vowel. |
| `speech_rate_too_slow` | Qwen alignment indicates the utterance syllable rate is too slow. |
| `long_interior_pause` | Qwen alignment found a long pause between aligned words/tokens. |
| `excessive_interior_pause` | Qwen alignment found repeated interior pauses. |
| `stretched_aligned_unit` | One aligned word/token is long relative to its syllable count. |
| `audio_quality_limited` | Audio quality limits interpretation. |

## `llm_feedback`

Only returned by `/analyze-pronunciation-llm` when Gemini is configured.

| Field | Description |
| --- | --- |
| `summary` | Short learner-facing summary. |
| `issues` | Per-issue feedback. |
| `overall_confidence` | LLM presentation confidence. |
| `next_practice_focus` | Suggested practice focus. |

The LLM receives compact structured evidence, not raw audio. It is instructed not to invent errors outside `phoneme_edits` and `diagnostic_candidates`.

## Recommended Client Usage

For learner-facing UI:

- Use `debug=false`.
- Display `llm_feedback` if available.
- Display top `diagnostic_candidates` only when LLM feedback is unavailable.

For debugging or research:

- Use `debug=true`.
- Inspect `phoneme_edits`, `target_phoneme_scores`, and `syllable_candidate_scores`.
- Do not interpret `alignments[].confidence` as pronunciation confidence.
