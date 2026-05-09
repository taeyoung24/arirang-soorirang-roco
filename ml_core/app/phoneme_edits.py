from __future__ import annotations

from app.acoustic_schemas import PhonemeEdit


def align_phonemes(canonical: str, predicted: str) -> tuple[list[str | None], list[PhonemeEdit]]:
    """Global edit alignment that avoids treating one deletion as many substitutions."""
    expected = list(canonical)
    actual = list(predicted)
    rows = len(expected) + 1
    cols = len(actual) + 1
    dp = [[0] * cols for _ in range(rows)]
    back = [[""] * cols for _ in range(rows)]

    for i in range(1, rows):
        dp[i][0] = i
        back[i][0] = "delete"
    for j in range(1, cols):
        dp[0][j] = j
        back[0][j] = "insert"

    for i in range(1, rows):
        for j in range(1, cols):
            match_cost = 0 if expected[i - 1] == actual[j - 1] else 2
            candidates = [
                (dp[i - 1][j - 1] + match_cost, "match" if match_cost == 0 else "replace"),
                (dp[i - 1][j] + 1, "delete"),
                (dp[i][j - 1] + 1, "insert"),
            ]
            dp[i][j], back[i][j] = min(candidates, key=lambda item: item[0])

    observed_by_expected: list[str | None] = [None] * len(expected)
    edits: list[PhonemeEdit] = []
    i = len(expected)
    j = len(actual)
    while i > 0 or j > 0:
        op = back[i][j]
        if op == "match":
            observed_by_expected[i - 1] = actual[j - 1]
            i -= 1
            j -= 1
        elif op == "replace":
            observed_by_expected[i - 1] = actual[j - 1]
            if _is_feedback_unit(expected[i - 1]) or _is_feedback_unit(actual[j - 1]):
                edits.append(
                    PhonemeEdit(
                        edit_type="substitution",
                        expected=expected[i - 1],
                        actual=actual[j - 1],
                        expected_index=i - 1,
                        actual_index=j - 1,
                    )
                )
            i -= 1
            j -= 1
        elif op == "delete":
            if _is_feedback_unit(expected[i - 1]):
                edits.append(
                    PhonemeEdit(
                        edit_type="deletion",
                        expected=expected[i - 1],
                        expected_index=i - 1,
                    )
                )
            i -= 1
        else:
            if j > 0 and _is_feedback_unit(actual[j - 1]):
                edits.append(
                    PhonemeEdit(
                        edit_type="insertion",
                        actual=actual[j - 1],
                        actual_index=j - 1,
                    )
                )
            j -= 1

    edits.reverse()
    _attach_context(canonical, edits)
    return observed_by_expected, edits


def _is_feedback_unit(value: str) -> bool:
    return "\u3131" <= value <= "\u318e"


def _attach_context(canonical: str, edits: list[PhonemeEdit]) -> None:
    syllable_spans = _canonical_syllable_spans(canonical)
    for edit in edits:
        index = edit.expected_index
        if index is None:
            index = _nearest_expected_index(edit.actual_index, edits)
        if index is None:
            continue
        start = max(0, index - 2)
        end = min(len(canonical), index + 3)
        edit.context = canonical[start:end]
        for syllable_index, syllable, span_start, span_end in syllable_spans:
            if span_start <= index < span_end:
                edit.syllable = syllable
                edit.syllable_index = syllable_index
                break


def _nearest_expected_index(actual_index: int | None, edits: list[PhonemeEdit]) -> int | None:
    if actual_index is None:
        return None
    candidates = [edit.expected_index for edit in edits if edit.expected_index is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda value: abs(value - actual_index))


def _canonical_syllable_spans(canonical: str) -> list[tuple[int, str, int, int]]:
    spans: list[tuple[int, str, int, int]] = []
    index = 0
    syllable_index = 0
    while index < len(canonical):
        start = index
        if canonical[index] not in CHOSEONG or index + 1 >= len(canonical) or canonical[index + 1] not in JUNGSEONG:
            spans.append((syllable_index, canonical[index], start, index + 1))
            index += 1
            syllable_index += 1
            continue
        choseong = canonical[index]
        jungseong = canonical[index + 1]
        index += 2
        jongseong = ""
        if index < len(canonical) and canonical[index] in JONGSEONG[1:]:
            next_is_vowel = index + 1 < len(canonical) and canonical[index + 1] in JUNGSEONG
            if not next_is_vowel:
                jongseong = canonical[index]
                index += 1
        spans.append((syllable_index, _compose_syllable(choseong, jungseong, jongseong), start, index))
        syllable_index += 1
    return spans


def _compose_syllable(choseong: str, jungseong: str, jongseong: str) -> str:
    jong_index = JONGSEONG.index(jongseong) if jongseong else 0
    return chr(0xAC00 + (CHOSEONG.index(choseong) * 588) + (JUNGSEONG.index(jungseong) * 28) + jong_index)


CHOSEONG = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
    "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]
JUNGSEONG = [
    "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
    "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
]
JONGSEONG = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ",
    "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ",
    "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]
