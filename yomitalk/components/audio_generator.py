"""Module providing audio generation functionality.

Provides functionality for generating audio from text using VOICEVOX Core.
"""

import datetime
import io
import os
import re
import uuid
import wave
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple

import e2k

from yomitalk.utils.logger import logger
from yomitalk.utils.text_utils import is_romaji_readable

# VOICEVOX Core imports
try:
    from voicevox_core.blocking import (
        Onnxruntime,
        OpenJtalk,
        Synthesizer,
        VoiceModelFile,
    )

    VOICEVOX_CORE_AVAILABLE = True
except ImportError as e:
    logger.error(f"VOICEVOX import error: {e}")
    logger.warning("VOICEVOX Core installation is required for audio generation.")
    logger.warning("Run 'make download-voicevox-core' to set up VOICEVOX.")
    VOICEVOX_CORE_AVAILABLE = False


# 単語タイプを表すEnum
class WordType(Enum):
    """単語タイプを表す列挙型"""

    BE_VERB = auto()
    PREPOSITION = auto()
    CONJUNCTION = auto()
    OTHER = auto()


class AudioGenerator:
    """Class for generating audio from text."""

    # VOICEVOX Core paths as constants (VOICEVOX version is managed in
    # VOICEVOX_VERSION in Makefile)
    VOICEVOX_BASE_PATH = Path("voicevox_core/voicevox_core")
    VOICEVOX_MODELS_PATH = VOICEVOX_BASE_PATH / "models/vvms"
    VOICEVOX_DICT_PATH = VOICEVOX_BASE_PATH / "dict/open_jtalk_dic_utf_8-1.11"
    VOICEVOX_LIB_PATH = VOICEVOX_BASE_PATH / "onnxruntime/lib"

    # 単語タイプのリスト
    BE_VERBS = ["am", "is", "are", "was", "were", "be", "been", "being"]
    PREPOSITIONS = [
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "at",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "by",
        "down",
        "during",
        "except",
        "for",
        "from",
        "in",
        "inside",
        "into",
        "like",
        "near",
        "of",
        "off",
        "on",
        "onto",
        "out",
        "outside",
        "over",
        "through",
        "to",
        "toward",
        "towards",
        "under",
        "underneath",
        "until",
        "up",
        "upon",
        "with",
        "within",
        "without",
    ]
    CONJUNCTIONS = [
        "and",
        "but",
        "or",
        "nor",
        "for",
        "yet",
        "so",
        "because",
        "if",
        "when",
        "although",
        "since",
        "while",
    ]

    CONVERSION_OVERRIDE = {"this": "ディス", "to": "トゥ", "a": "ア"}

    def __init__(
        self,
        session_output_dir: Optional[Path] = None,
        session_temp_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize AudioGenerator.

        Args:
            session_output_dir (Optional[Path]): Session-specific output directory.
                If not provided, defaults to "data/output"
            session_temp_dir (Optional[Path]): Session-specific temporary directory.
                If not provided, defaults to "data/temp/talks"
        """
        # Use session-specific directories if provided
        self.output_dir = (
            session_output_dir if session_output_dir else Path("data/output")
        )
        self.temp_dir = (
            session_temp_dir if session_temp_dir else Path("data/temp/talks")
        )

        # Make sure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # VOICEVOX Core
        self.core_initialized = False
        self.core_synthesizer: Optional[Synthesizer] = None
        self.core_style_ids = {
            "ずんだもん": 3,  # Zundamon (sweet)
            "四国めたん": 2,  # Shikoku Metan (normal)
            "九州そら": 16,  # Kyushu Sora (normal)
            "中国うさぎ": 61,  # Chugoku Usagi (normal)
            "中部つるぎ": 94,  # Chubu Tsurugi (normal)
        }

        # Initialize VOICEVOX Core if available
        if VOICEVOX_CORE_AVAILABLE:
            self._init_voicevox_core()

    def _init_voicevox_core(self) -> None:
        """Initialize VOICEVOX Core if components are available."""
        try:
            # Check if required directories exist
            if (
                not self.VOICEVOX_MODELS_PATH.exists()
                or not self.VOICEVOX_DICT_PATH.exists()
            ):
                logger.warning("VOICEVOX models or dictionary not found")
                return

            # Initialize OpenJTalk and ONNX Runtime following the official guide
            # https://github.com/VOICEVOX/voicevox_core/blob/main/docs/guide/user/usage.md
            try:
                # 1. Initialize OpenJtalk with dictionary
                open_jtalk = OpenJtalk(str(self.VOICEVOX_DICT_PATH))

                # 2. Initialize ONNX Runtime
                # Try to use local runtime first if available
                runtime_path = str(
                    self.VOICEVOX_LIB_PATH / "libvoicevox_onnxruntime.so.1.17.3"
                )

                # Proper initialization of ONNX runtime
                if os.path.exists(runtime_path):
                    logger.info(f"Loading ONNX runtime from: {runtime_path}")
                    ort = Onnxruntime.load_once(filename=runtime_path)
                else:
                    logger.info("Loading default ONNX runtime")
                    ort = Onnxruntime.load_once()

                # 3. Initialize synthesizer with runtime and dictionary
                self.core_synthesizer = Synthesizer(ort, open_jtalk)
                logger.info("Synthesizer initialized successfully")

                # 4. Load voice models
                model_count = 0
                for model_file in self.VOICEVOX_MODELS_PATH.glob("*.vvm"):
                    if self.core_synthesizer is not None:  # Type check for mypy
                        try:
                            with VoiceModelFile.open(str(model_file)) as model:
                                self.core_synthesizer.load_voice_model(model)
                                model_count += 1
                                logger.debug(f"Loaded voice model: {model_file}")
                        except Exception as e:
                            logger.error(f"Failed to load model {model_file}: {e}")

                if model_count > 0:
                    logger.info(f"Successfully loaded {model_count} voice models")
                    self.core_initialized = True
                    logger.info("VOICEVOX Core initialization completed")
                else:
                    logger.error("No voice models could be loaded")
                    self.core_initialized = False

            except Exception as e:
                logger.error(f"Failed to initialize VOICEVOX Core: {e}")
                self.core_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize VOICEVOX Core: {e}")
            self.core_initialized = False

    def _convert_english_to_katakana(self, text: str) -> str:
        """
        英単語をカタカナに変換し、自然な息継ぎのタイミングで空白を制御します。

        以下のルールに基づいて空白を制御します：
        1. be動詞の前では息継ぎしない（空白を入れない）
        2. 前置詞の前後では息継ぎしない
        3. 一定文字数（約30字）経過した場所で、自然な区切りがあれば息継ぎを入れる
        4. 句読点の後には通常息継ぎを入れる

        変換例：
        - "this" → "ディス"（正：ディス、誤：シス）
        - "to" → "トゥ"（正：トゥ、誤：トー）
        - "welcome" → 「ウエルカム」または「ウェルカム」（どちらでも可）

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 英単語がカタカナに変換され、自然な息継ぎを考慮して空白が制御されたテキスト
        """
        # 英単語と非英単語を分割するための正規表現パターン
        pattern = r"([A-Za-z]+|[^A-Za-z]+)"
        parts = re.findall(pattern, text)

        # 大文字で始まる部分を分割する
        split_parts = self._split_capitalized_parts(parts)

        # 英単語をカタカナに変換し、自然な息継ぎのための空白を制御
        return self._convert_parts_to_katakana(parts=split_parts, converter=e2k.C2K())

    def _split_capitalized_parts(self, parts: List[str]) -> List[str]:
        """大文字で始まる部分を適切に分割します。"""
        split_parts = []
        for part in parts:
            if re.match(r"^[A-Za-z]+$", part):
                # 連続する大文字は一つの略語として扱う
                word_parts = re.findall(r"[A-Z]{2,}|[A-Z][a-z]*|[a-z]+", part)
                split_parts.extend(word_parts)
            else:
                # 非英単語はそのまま追加
                split_parts.append(part)
        return split_parts

    def _convert_parts_to_katakana(
        self,
        parts: List[str],
        converter: e2k.C2K,
    ) -> str:
        """分割された部分をカタカナに変換し、適切な空白を制御します。"""
        result: List[str] = []
        chars_since_break = 0  # 最後の息継ぎからの文字数をカウント
        last_was_katakana = False
        last_word_type = None  # 前の単語のタイプ（前置詞、be動詞、その他）
        next_word_no_space = False  # 次の単語の前に空白を入れないフラグ

        for i, part in enumerate(parts):
            # 英単語かどうかを判定
            is_english_word = self._is_english_word(part)

            # 次の部分を確認（あれば）
            next_part = parts[i + 1] if i + 1 < len(parts) else ""
            next_is_english = self._is_english_word(next_part) if next_part else False

            # 英単語の場合の処理
            if is_english_word:
                self._process_english_word(
                    part,
                    next_part,
                    next_is_english,
                    converter,
                    result,
                    chars_since_break,
                    last_was_katakana,
                    next_word_no_space,
                )
                chars_since_break = result[-1] and len(result[-1]) or 0
                last_was_katakana = True

                # 単語のタイプを判定して更新
                word_lower = part.lower()
                if word_lower in self.BE_VERBS:
                    last_word_type = WordType.BE_VERB
                elif word_lower in self.PREPOSITIONS:
                    last_word_type = WordType.PREPOSITION
                    next_word_no_space = True
                elif word_lower in self.CONJUNCTIONS:
                    last_word_type = WordType.CONJUNCTION
                    next_word_no_space = True
                else:
                    last_word_type = WordType.OTHER
                    next_word_no_space = False

            elif re.match(r"^-+$", part):  # 1つ以上のハイフンのみで構成されている場合
                # ハイフンは捨てる
                pass
            else:
                # 句読点や改行の処理
                if re.search(r"[。．.、，,!！?？\n]", part):
                    chars_since_break = 0  # 句読点の後は文字カウントをリセット

                # 空白文字の場合の処理
                if part.isspace():
                    # 前がカタカナで、次もカタカナになる可能性がある場合は判断を保留
                    if last_was_katakana and next_is_english:
                        # 次の単語の種類によって空白を入れるかどうかを判断
                        next_word_lower = next_part.lower()
                        if (
                            next_word_lower in self.BE_VERBS
                            or next_word_lower in self.PREPOSITIONS
                            or last_word_type is WordType.PREPOSITION
                            or next_word_lower in self.CONJUNCTIONS
                        ):
                            # 空白を追加しない
                            pass
                        else:
                            result.append(part)
                    else:
                        result.append(part)
                        chars_since_break += 1
                else:
                    result.append(part)
                    chars_since_break += len(part)
                    last_was_katakana = False
                    last_word_type = None

        return "".join(result)

    def _is_english_word(self, part: str) -> bool:
        """文字列が変換対象の英単語かどうかを判定します。"""
        if not part:
            return False

        return bool(
            part.lower() in self.CONVERSION_OVERRIDE
            or len(part) >= 2
            and re.match(r"^[A-Za-z]+$", part)
            and (
                not re.match(r"^[A-Z]+$", part)
                or (len(part) >= 4 and is_romaji_readable(part))
            )
        )

    def _process_english_word(
        self,
        part: str,
        next_part: str,
        next_is_english: bool,
        converter: e2k.C2K,
        result: List[str],
        chars_since_break: int,
        last_was_katakana: bool,
        next_word_no_space: bool,
    ) -> None:
        """英単語をカタカナに変換し、適切な空白制御を行います。"""
        # 小文字に変換して比較
        word_lower = part.lower()

        # 単語のタイプを判定
        is_be_verb = word_lower in self.BE_VERBS
        is_preposition = word_lower in self.PREPOSITIONS
        is_conjunction = word_lower in self.CONJUNCTIONS

        # カタカナに変換（オーバーライドがあれば使用）
        katakana_part = self.CONVERSION_OVERRIDE.get(word_lower)
        if katakana_part is None:
            katakana_part = converter(part)

        # 息継ぎ（空白）を入れるかどうかの判定
        add_space = True

        # 前置詞の後、次の単語の前には空白を入れない
        if next_word_no_space:
            add_space = False
        # be動詞の前には空白を入れない
        elif next_is_english and next_part.lower() in self.BE_VERBS:
            add_space = False
        # 前置詞の前にも空白を入れない
        elif next_is_english and next_part.lower() in self.PREPOSITIONS:
            add_space = False
        # 接続詞の前にも空白を入れない場合が多い
        elif next_is_english and next_part.lower() in self.CONJUNCTIONS:
            add_space = False

        # 最後の息継ぎから30文字以上経過し、自然な区切りの場合は息継ぎを入れる
        if (
            chars_since_break > 30
            and not is_be_verb
            and not is_preposition
            and not is_conjunction
        ):
            add_space = True

        # 前の要素もカタカナだった場合、判定に従って空白を追加または削除
        if last_was_katakana and result and result[-1].isspace():
            if not add_space:
                result.pop()  # 空白を削除
        elif last_was_katakana and add_space:
            result.append(" ")  # 空白を追加

        result.append(katakana_part)

    def generate_character_conversation(self, podcast_text: str) -> Optional[str]:
        """
        Generate audio for a character conversation from podcast text.

        Args:
            podcast_text (str): Podcast text with character dialogue lines

        Returns:
            str: Path to the generated audio file or None if failed
        """
        if not VOICEVOX_CORE_AVAILABLE or not self.core_initialized:
            logger.error("VOICEVOX Core is not available or not properly initialized.")
            return None

        if not podcast_text or podcast_text.strip() == "":
            logger.error("Podcast text is empty")
            return None

        try:
            # 英語をカタカナに変換
            podcast_text = self._convert_english_to_katakana(podcast_text)
            logger.info("Converted English words in podcast text to katakana")

            # Split the podcast text into lines
            lines = podcast_text.strip().split("\n")
            conversation_parts = []

            # サポートされるキャラクター名とそのパターン
            # TODO: 自動的にこれらのパターンに対応
            character_patterns = {
                "ずんだもん": ["ずんだもん:", "ずんだもん："],
                "四国めたん": ["四国めたん:", "四国めたん："],
                "九州そら": ["九州そら:", "九州そら："],
                "中国うさぎ": ["中国うさぎ:", "中国うさぎ："],
                "中部つるぎ": ["中部つるぎ:", "中部つるぎ："],
            }

            # 複数行のセリフを処理するために現在の話者と発言を記録
            current_speaker = None
            current_speech = ""

            # Process each line of the text
            logger.info(f"Processing {len(lines)} lines of text")
            for line in lines:
                line = line.strip()

                # 新しい話者の行かチェック
                found_new_speaker = False
                for character, patterns in character_patterns.items():
                    for pattern in patterns:
                        if line.startswith(pattern):
                            # 前の話者の発言があれば追加
                            if current_speaker and current_speech:
                                conversation_parts.append(
                                    (current_speaker, current_speech)
                                )

                            # 新しい話者と発言を設定
                            current_speaker = character
                            current_speech = line.replace(pattern, "", 1).strip()
                            found_new_speaker = True
                            break
                    if found_new_speaker:
                        break

                # 話者の切り替えがなく、現在の話者が存在する場合、行を現在の発言に追加
                if not found_new_speaker and current_speaker:
                    if line:  # 行に内容がある場合
                        # すでに発言内容があれば改行を追加
                        if current_speech:
                            current_speech += "\n" + line
                        else:
                            current_speech = line
                    else:  # 空行の場合
                        # 空行も保持（改行として追加）
                        if current_speech:
                            current_speech += "\n"

            # 最後の話者の発言があれば追加
            if current_speaker and current_speech:
                conversation_parts.append((current_speaker, current_speech))

            logger.info(f"Identified {len(conversation_parts)} conversation parts")

            # If no valid parts were found, try to fix the format
            if not conversation_parts:
                logger.warning(
                    "No valid conversation parts found. Attempting to reformat..."
                )
                fixed_text = self._fix_conversation_format(podcast_text)
                # Try again with fixed text
                if fixed_text != podcast_text:
                    return self.generate_character_conversation(fixed_text)
                else:
                    logger.error("Could not parse any valid conversation parts")
                    return None

            # Generate audio for each conversation part
            wav_data_list = []  # メモリ上に直接音声データを保持するリスト
            total_conversation_parts = len(conversation_parts)
            logger.info(f"キャラクター会話の音声生成開始: 会話部分数 {total_conversation_parts}")

            for i, (speaker, text) in enumerate(conversation_parts):
                # 進捗状況を表示
                part_progress = int(((i + 1) / total_conversation_parts) * 100)
                logger.info(
                    f"キャラクター会話進捗: {i+1}/{total_conversation_parts} ({part_progress}%)"
                )

                style_id = self.core_style_ids.get(
                    speaker, 3
                )  # Default to Zundamon if not found
                logger.info(f"Generating audio for {speaker} (style_id: {style_id})")

                # テキストが空でなければ一括で音声生成を行う
                if text.strip():
                    logger.info(f"{speaker}のセリフを生成中...")
                    part_wav_data = self._text_to_speech(text, style_id)

                    if part_wav_data:
                        logger.debug(f"{speaker}のセリフを生成し、メモリに保存しました")
                        wav_data_list.append(part_wav_data)

            # メモリ上で音声データを結合して最終的な音声ファイルを作成
            if wav_data_list:
                logger.info(f"メモリ上で {len(wav_data_list)} 個の音声パーツを結合中")

                # 結合された音声データをメモリ上で生成
                combined_wav_data = self._combine_wav_data_in_memory(wav_data_list)

                if combined_wav_data:
                    # 結合されたデータを最終的な出力ファイルに書き込む
                    # 日付付きの最終的な出力ファイル名を生成
                    now = datetime.datetime.now()
                    date_str = now.strftime("%Y%m%d_%H%M%S")
                    file_id = uuid.uuid4().hex[:8]

                    self.output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = str(
                        self.output_dir / f"audio_{date_str}_{file_id}.wav"
                    )

                    logger.info(f"最終出力ファイル: {os.path.basename(output_file)}")

                    with open(output_file, "wb") as f:
                        f.write(combined_wav_data)

                    logger.info("音声ファイルを生成しました")
                    return output_file
                else:
                    logger.error("音声データの結合に失敗しました")
                    return None
            else:
                logger.error("No audio parts were generated")
                return None

        except Exception as e:
            logger.error(f"Character conversation audio generation error: {e}")
            return None

    def _combine_wav_data_in_memory(self, wav_data_list: List[bytes]) -> bytes:
        """
        メモリ上でWAVデータを結合する

        Args:
            wav_data_list: 結合するWAVデータのバイト列リスト

        Returns:
            bytes: 結合されたWAVデータ
        """
        if not wav_data_list:
            return b""

        if len(wav_data_list) == 1:
            return wav_data_list[0]

        total_files = len(wav_data_list)
        logger.debug(f"音声ファイル結合開始: 合計{total_files}ファイル")

        # 全てのWAVファイルのパラメータとデータを読み込む
        wav_params_and_data: List[Tuple[wave._wave_params, bytes]] = []

        for i, wav_bytes in enumerate(wav_data_list):
            # 進捗をログに記録
            if total_files > 10 and (i % 5 == 0 or i == total_files - 1):
                progress_percent = int(((i + 1) / total_files) * 100)
                logger.debug(f"WAVデータ読み込み進捗: {i+1}/{total_files} ({progress_percent}%)")

            with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(wav_file.getnframes())
                wav_params_and_data.append((params, frames))

        # 最初のWAVファイルのパラメータを使用（全て同じフォーマットと仮定）
        first_params = wav_params_and_data[0][0]
        logger.debug("WAVデータ読み込み完了: WAVパラメータを設定中")

        # 結果を書き込むためのメモリバッファを作成
        output_buffer = io.BytesIO()

        with wave.open(output_buffer, "wb") as output_wav:
            # WAVパラメータを設定（最初のファイルと同じ）
            output_wav.setparams(first_params)

            # 全てのフレームデータを書き込む
            logger.debug(f"WAVデータ結合中: {total_files}ファイルのフレームデータを結合")
            for i, (_, frames) in enumerate(wav_params_and_data):
                # 大量のファイルの場合は定期的に進捗を表示
                if total_files > 10 and (i % 5 == 0 or i == total_files - 1):
                    progress_percent = int(((i + 1) / total_files) * 100)
                    logger.debug(
                        f"WAVデータ結合進捗: {i+1}/{total_files} ({progress_percent}%)"
                    )
                output_wav.writeframes(frames)

        logger.debug(f"WAVデータ結合完了: {total_files}ファイルを正常に結合")
        # 結合されたWAVデータを返す
        return output_buffer.getvalue()

    def _fix_conversation_format(self, text: str) -> str:
        """
        Attempt to fix common formatting issues in conversation text.

        Args:
            text (str): Original conversation text

        Returns:
            str: Fixed conversation text
        """
        import re

        # サポートされる全てのキャラクター名
        character_names = ["ずんだもん", "四国めたん", "九州そら", "中国うさぎ", "中部つるぎ"]

        # Fix missing colon after speaker names
        for name in character_names:
            text = re.sub(f"({name})(\\s+)(?=[^\\s:])", f"{name}:\\2", text)

        # カスタム名のキャラクターを検出し、標準名にマッピング
        lines = text.split("\n")
        fixed_lines = []

        # カスタム名の話者を検出するための正規表現
        speaker_pattern = re.compile(r"^([^:：]+)[：:]\s*(.*)")
        current_speaker = None
        current_speech = []

        for line in lines:
            line_stripped = line.strip()
            match = speaker_pattern.match(line_stripped) if line_stripped else None

            if match:
                # 新しい話者が検出された
                # 前の話者のセリフがあれば追加
                if current_speaker and current_speech:
                    fixed_lines.append(f"{current_speaker}: {' '.join(current_speech)}")
                    current_speech = []

                speaker, speech = match.groups()
                # 既知のキャラクター名に最も近いものを探す
                best_match = None
                for name in character_names:
                    if name in speaker:
                        best_match = name
                        break

                # 最適なマッチが見つからない場合、デフォルトをずんだもんにする
                current_speaker = best_match if best_match else "ずんだもん"
                if speech.strip():
                    current_speech.append(speech.strip())
            else:
                # 空行や話者が指定されていない行の処理
                if current_speaker:
                    if line_stripped:
                        # 内容のある行は現在の話者の続きとして追加
                        current_speech.append(line_stripped)
                    else:
                        # 空行は段落区切りとして改行を追加
                        if current_speech:
                            # 最後の要素が改行を含んでいない場合のみ追加
                            if not current_speech[-1].endswith("\n"):
                                current_speech[-1] += "\n"
                elif line_stripped:
                    # 話者が一度も検出されていない場合、デフォルトをずんだもんにする
                    current_speaker = "ずんだもん"
                    current_speech.append(line_stripped)

        # 最後の話者の発言を追加
        if current_speaker and current_speech:
            fixed_lines.append(f"{current_speaker}: {' '.join(current_speech)}")

        fixed_text = "\n".join(fixed_lines)

        # Try to identify speaker blocks in continuous text
        lines = fixed_text.split("\n")
        final_lines = []

        for line in lines:
            # 複数のキャラクターが一行に存在するかチェック
            fixed_line = line
            for name in character_names:
                if f"。{name}" in fixed_line:
                    parts = fixed_line.split(f"。{name}")
                    if len(parts) > 1:
                        if parts[0].strip():
                            final_lines.append(f"{parts[0].strip()}。")
                        fixed_line = f"{name}{parts[1]}"

            final_lines.append(fixed_line)

        # Join the fixed lines
        return "\n".join(final_lines)

    def update_log(self, message: str) -> None:
        """
        Update the system log with a new message.

        Args:
            message (str): The message to add to the system log
        """
        # Implementation of update_log method
        pass

    def system_log(self) -> str:
        """
        Get the system log as a string.

        Returns:
            str: The system log
        """
        # Implementation of system_log method
        return ""

    def _text_to_speech(self, text: str, style_id: int) -> bytes:
        """
        メモリ上でテキストから音声データを生成する

        Args:
            text: 音声に変換するテキスト
            style_id: VOICEVOXのスタイルID

        Returns:
            bytes: 生成されたWAVデータ
        """
        if not text.strip() or not self.core_synthesizer:
            return b""

        logger.info("音声生成開始: テキストを一括処理")

        try:
            # テキスト全体から一度に音声データを生成
            wav_data: bytes = self.core_synthesizer.tts(text, style_id)
            logger.info(f"音声生成完了: サイズ {len(wav_data) // 1024} KB")
            return wav_data
        except Exception as e:
            logger.error(f"音声生成エラー: {e}")
            return b""
