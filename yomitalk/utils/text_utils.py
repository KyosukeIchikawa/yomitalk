"""Text processing utilities for the Paper Podcast Generator.

Contains utility functions for text processing, romanization support, and more.
"""

import re


def is_romaji_readable(word: str) -> bool:
    """
    大文字アルファベットで構成された単語が、日本語のローマ字として音節に分解して読めるかを判定します。

    判定基準：
    - 単語は母音(A,I,U,E,O)、子音+母音、拗音(KYAなど)、撥音(N)の組み合わせで構成される。
    - 撥音Nは、後に子音が続くか、語末にある場合に成立する。
    - 促音(例: TT, SS, KK)は基本的に考慮しない。(例: URRI, LLA, KITTE, NISSAN は不可)
    - ユーザー指定の例に基づき、HONDAやAIKOは可能、URRIやLLAは不可能とする。

    Args:
        word (str): 判定対象の大文字アルファベットの文字列。

    Returns:
        bool: ローマ字読み可能であればTrue、そうでなければFalse。
    """
    if not isinstance(word, str) or not word:  # 空文字列やNoneはFalse
        return False
    if not re.fullmatch(r"[A-Z]+", word):  # 大文字アルファベット以外が含まれている場合はFalse
        return False

    # 単一の母音のケース（1文字の場合はパターン照合前に判定）
    if len(word) == 1:
        return word in "AIUEO"

    # ローマ字の音節パターンリスト（優先順位順に定義）
    # 長いもの、特殊なものから順にマッチさせることで、正しい音節分割を促す。
    syllable_patterns = [
        # 特殊な複合子音
        r"TSU",  # つ
        r"SHI",  # し
        r"CHI",  # ち
        # 特殊な拗音
        r"CH[AUO]",  # ちゃ, ちゅ, ちょ
        r"SH[AUO]",  # しゃ, しゅ, しょ
        # 拗音 (子音 + Y + 母音)
        # 例: KYA, SYA (訓令式 しゃ), TYA (訓令式 ちゃ), NYA, HYA, MYA, RYA, GYA, JYA, DYA, BYA, PYA
        # SH[AUO], CH[AUO] は上で定義済みなので、ここではそれ以外の Y を含む拗音をカバー。
        # ZY[AUO] (じゃ等)も JYA と同様にここでカバー。
        r"(?:K|S|T|N|H|M|R|G|Z|J|D|B|P)Y[AUO]",
        # 通常の子音 + 母音
        # 例: KA, KI, FU, MI, TO, WA, YA, SU, JI (ZI,DIも含む), ZO
        # F[AIUEO], W[AIUEO], Y[AUO] (YA,YU,YO) も含む
        # J[AUO] (JA,JU,JO) も含む
        # (SI, TI, HU, DI, ZU など、訓令式/日本式に近い表記も許容)
        r"[BCDFGHJKLMNPQRSTVWXYZ][AIUEO]",
        # 母音単独
        r"[AIUEO]",
        # 撥音「ん」
        # このNは、正規表現のマッチングプロセスにより、
        # Nの後に母音やYが続く場合は、上記のより長いパターン(例:NA, NI, NYA)で先にマッチされる。
        # そのため、このNが単独でマッチするのは、主に後に子音が続く場合(例:HONDAのN)や
        # 語末(例:KENのN)、またはNの後にさらにNで始まる音節が続く場合(例:GINNANの最初のN)。
        r"N",
    ]

    # 各音節パターンを非キャプチャグループ (?:...) で囲み、OR (|) で結合
    syllable_regex_part = "|".join([f"(?:{p})" for p in syllable_patterns])

    # 単語全体が「(音節パターン1 | 音節パターン2 | ...)+」に完全一致するかを判定
    # これにより、単語が上記の音節の繰り返しのみで構成されているかをチェックする。
    full_word_regex = re.compile(f"^({syllable_regex_part})+$")

    # 文字列がマッチするかどうかを判定
    if full_word_regex.fullmatch(word):
        return True

    # 一部の複合音（SH+I, CH+I）のパターンを特別に許容する
    # これは正規表現での優先的なマッチングが難しいため、手動チェックする
    temp_word = word
    temp_word = re.sub(r"SHI", "SI", temp_word)
    temp_word = re.sub(r"CHI", "TI", temp_word)
    temp_word = re.sub(r"SHA", "SA", temp_word)
    temp_word = re.sub(r"SHU", "SU", temp_word)
    temp_word = re.sub(r"SHO", "SO", temp_word)
    temp_word = re.sub(r"CHA", "TA", temp_word)
    temp_word = re.sub(r"CHU", "TU", temp_word)
    temp_word = re.sub(r"CHO", "TO", temp_word)

    # 置換後の文字列で再チェック
    return bool(full_word_regex.fullmatch(temp_word))
