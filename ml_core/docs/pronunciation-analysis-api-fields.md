# Pronunciation Analysis API Fields

This document explains the response fields for:

- `POST /analyze-pronunciation-basic`
- `POST /analyze-pronunciation-llm`

By default, both endpoints return a compact response. Pass `debug=true` to include full alignments, acoustic features, and phoneme scores.

## Request Fields

| Field | Required | Default | Description |
| --- | --- | --- | --- |
| `script` | yes | - | Target Korean sentence to evaluate. |
| `audio` | yes | - | Learner speech audio file. |
| `language` | no | `Korean` | Language name passed to the forced aligner. Usually omit this for Korean. |
| `feedback_language` | no | `ko` | Language used for LLM feedback text. Examples: `ko`, `en`, `ja`, `zh-CN`. |
| `debug` | no | `false` | If `true`, returns full diagnostic internals. If `false`, returns compact fields only. |

## Top-Level Response Fields

| Field | Meaning |
| --- | --- |
| `script` | Original target sentence from the request. |
| `canonical_phonemes` | Target phoneme sequence generated from `script` by G2P and Hangul decomposition. Punctuation is removed. |
| `predicted_phonemes` | MDD model's predicted phoneme sequence. |
| `audio_quality` | Overall recording quality summary. |
| `phoneme_edits` | Edit-aligned mismatch summary between canonical and predicted phonemes. This is the primary error source. |
| `diagnostic_candidates` | Candidate pronunciation issues derived from `phoneme_edits` and supporting evidence. |
| `llm_feedback` | Learner-facing feedback. Present only on `/analyze-pronunciation-llm` when Gemini is configured. |
| `notes` | Operational notes and limitations for this analysis. |

The following fields are compacted unless `debug=true`:

| Field | Compact Behavior |
| --- | --- |
| `alignments` | Only issue-related phoneme/syllable units or a few word units are returned. |
| `segment_features` | Removed in compact mode. |
| `predicted_phoneme_scores` | Only issue-related predicted phoneme scores are returned. |
| `target_phoneme_scores` | Only issue-related target phoneme scores are returned. |
| `syllable_candidate_scores` | Only issue-related syllable candidate scores are returned. |
| `prosody` | Removed in compact mode. |
| `model_score` | Removed in compact mode. |

## Important Confidence Types

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
| `audio_quality_limited` | Audio quality limits interpretation. |

## `segment_features`

Returned only with `debug=true`.

Each bundle contains acoustic measurements for a phoneme segment:

- `duration_ms`
- `rms_energy`
- `pitch_hz`
- `spectral_centroid_hz`
- `zero_cross_rate`
- `high_frequency_ratio`
- `burst_peak`
- `frication_ms`

These features are lightweight debug measurements. They should not be treated as standalone pronunciation errors.

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
- Inspect `phoneme_edits`, `target_phoneme_scores`, `syllable_candidate_scores`, and `segment_features`.
- Do not interpret `alignments[].confidence` as pronunciation confidence.
