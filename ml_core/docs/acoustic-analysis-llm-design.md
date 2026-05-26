# Acoustic Analysis + LLM Interpretation Design

## Goal

Extend the current MDD service from `phoneme sequence mismatch detection` into `phonetic evidence based feedback`.

The current service already does:

- audio normalization
- canonical phoneme generation from script
- fairseq-based phoneme prediction
- edit-distance issue summary

It does not yet do:

- time alignment between signal and target units
- prosody analysis
- evidence-to-feedback interpretation

## Design Principle

The LLM should not receive raw audio or opaque embeddings as its primary evidence.
It should receive a structured evidence packet that has already been aligned, measured, and reliability-scored.

Recommended architecture:

1. `Alignment layer`
2. `Prosody evidence layer`
3. `Candidate diagnosis layer`
4. `LLM interpretation layer`

## Proposed Pipeline

```text
audio + script
-> canonical phonemes
-> forced alignment
-> syllable / word intervals
-> timing + prosody evidence extraction
-> rule-based diagnostic candidates
-> LLM evidence packet
-> learner-facing feedback
```

## Layer 1: Alignment

The alignment layer should output time spans for:

- syllable
- word

Required fields:

- `label`
- `unit_type`
- `start_ms`
- `end_ms`
- `confidence`

This layer is mandatory because timing diagnostics need stable syllable and word windows.

## Layer 2: Prosody Evidence

Only interpretable timing evidence should be passed downstream.

- `speech_rate_syllables_per_second`
- `articulation_rate_syllables_per_second`
- `pause_count`
- `pause_total_ms`

### Audio quality guards

- `snr_db`
- `clipping_detected`
- `voiced_ratio`
- `overall_reliability`

## Layer 3: Diagnostic Candidates

Before calling the LLM, a deterministic layer should convert MDD phoneme edits and timing deviations into candidate findings.

Examples:

- `aspiration_insufficient`
- `fortis_tension_insufficient`
- `coda_release_missing`
- `speech_rate_unstable`

Each candidate should include:

- diagnosis code
- category
- severity
- confidence
- evidence keys
- rationale

## Layer 4: LLM Interpretation

The LLM consumes a structured packet and produces:

- short summary
- prioritized issue list
- likely listener perception
- coaching instructions
- confidence-aware wording

The LLM prompt should enforce:

- no claims beyond evidence
- no feedback from low-reliability measurements
- pedagogical Korean output by default

## Korean Phonetics Priorities

The first implementation should focus on the contrasts that matter most for Korean learner feedback:

- lenis / fortis / aspirated stop contrast
- coda neutralization and release behavior
- liaison and resyllabification sensitive contexts
- speech rate and interior pause timing

## API Extension Strategy

Keep the current `PredictResponse` stable for existing clients.
Introduce a second response block or a second endpoint for acoustic analysis.

Recommended additions:

- `alignment`
- `prosody`
- `diagnostic_candidates`
- `llm_feedback`

This allows gradual rollout without breaking the current phoneme-only clients.

## Suggested Endpoint Shape

```text
POST /analyze-pronunciation
```

Request:

- `script`
- `audio`
- optional analysis profile

Response:

- existing phoneme prediction summary
- structured acoustic evidence
- LLM-generated feedback

## Implementation Phases

### Phase 1

- define evidence schema
- implement placeholder endpoint contract
- keep current model untouched

### Phase 2

- add forced alignment
- emit phoneme and syllable intervals

### Phase 3

- extract utterance-level timing/prosody evidence
- add reliability gating

### Phase 4

- add rule-based diagnostic candidates
- add LLM prompt and post-processing

### Phase 5

- calibrate native-speaker baselines
- tune severity thresholds

## Current Repository Mapping

- existing phoneme pipeline: [app/pipeline.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/pipeline.py:214)
- current response schema: [app/schemas.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/schemas.py:31)
- proposed evidence schema: [app/acoustic_schemas.py](/C:/Users/dobi/Desktop/study/arirang-soorirang-roco/ml_core/app/acoustic_schemas.py:1)

## Notes

- This branch defines the contract and interpretation shape, not the full DSP implementation.
- The branch is safe to review independently because it does not change the current inference behavior.
