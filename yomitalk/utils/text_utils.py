"""Text processing utilities for the Paper Podcast Generator.

Contains utility functions for text processing, romanization support, and more.
"""

import re
import unicodedata


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


def normalize_text(text: str) -> str:
    """
    テキストを正規化する（文字列比較のために統一形式に変換）

    「正規化」とは、異なる表記方法で書かれた同じ意味の文字列を
    統一された形式に変換することです。

    具体的な変換処理：
    1. Unicode正規化（全角→半角、合成文字→分解文字など）
    2. 空白・記号の除去（スペース、ハイフン、アンダースコアなど）
    3. ひらがな→カタカナ変換
    4. 英字の小文字化

    例：
    - "四国 めたん" → "シコクメタン"
    - "四-めたん" → "シメタン"
    - "ずんだ_もん" → "ズンダモン"
    - "Zundamon" → "zundamon"
    - "ｚｕｎｄａ" → "zunda" (全角→半角)

    Args:
        text (str): 正規化するテキスト

    Returns:
        str: 正規化されたテキスト（統一形式）
    """
    if not text:
        return ""

    # Unicode正規化
    normalized = unicodedata.normalize("NFKC", text)

    # 空白、ハイフン、その他の記号を除去
    normalized = re.sub(r"[\s\-_・−ー]", "", normalized)

    # ひらがなをカタカナに変換
    normalized = hiragana_to_katakana(normalized)

    # 小文字に統一（英字部分）
    normalized = normalized.lower()

    return normalized


def hiragana_to_katakana(text: str) -> str:
    """
    ひらがなをカタカナに変換する

    Args:
        text (str): 変換するテキスト

    Returns:
        str: カタカナに変換されたテキスト
    """
    result = []
    for char in text:
        # ひらがな範囲 (U+3041-U+3096) をカタカナ範囲 (U+30A1-U+30F6) に変換
        if "\u3041" <= char <= "\u3096":
            result.append(chr(ord(char) + 0x60))
        else:
            result.append(char)
    return "".join(result)


def calculate_text_similarity(str1: str, str2: str) -> float:
    """
    2つの文字列の類似度を計算する（表記ゆれに対応したファジーマッチング）

    この関数は文字列の「表記ゆれ」を考慮した類似度計算を行います。
    まず両方の文字列を正規化（統一形式に変換）してから、
    複数の手法で類似度を測定し、最も高い値を返します。

    Args:
        str1 (str): 比較する文字列1
        str2 (str): 比較する文字列2

    Returns:
        float: 類似度 (0.0-1.0、1.0が完全一致)
    """
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0

    # 正規化
    norm_str1 = normalize_text(str1)
    norm_str2 = normalize_text(str2)

    if norm_str1 == norm_str2:
        return 1.0

    # レーベンシュタイン距離ベースの類似度
    levenshtein_sim = levenshtein_similarity(norm_str1, norm_str2)

    # 部分文字列マッチング（短い方が長い方に含まれる）
    substring_sim = 0.0
    if norm_str1 in norm_str2 or norm_str2 in norm_str1:
        shorter = min(len(norm_str1), len(norm_str2))
        longer = max(len(norm_str1), len(norm_str2))
        substring_sim = shorter / longer if longer > 0 else 0.0

    # 最大値を取る（より寛容なマッチング）
    return max(levenshtein_sim, substring_sim)


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    レーベンシュタイン距離ベースの類似度を計算する

    Args:
        s1 (str): 文字列1
        s2 (str): 文字列2

    Returns:
        float: 類似度 (0.0-1.0)
    """
    if len(s1) == 0:
        return 0.0 if len(s2) > 0 else 1.0
    if len(s2) == 0:
        return 0.0

    # レーベンシュタイン距離を計算
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    # 類似度に変換 (距離が小さいほど類似度が高い)
    return 1.0 - (distance / max_len)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    レーベンシュタイン距離を計算する

    Args:
        s1 (str): 文字列1
        s2 (str): 文字列2

    Returns:
        int: レーベンシュタイン距離
    """
    len1, len2 = len(s1), len(s2)

    # 動的プログラミング用のテーブルを初期化
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    # 初期値設定
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    # 動的プログラミング
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # 削除
                dp[i][j - 1] + 1,  # 挿入
                dp[i - 1][j - 1] + cost,  # 置換
            )

    return dp[len1][len2]
