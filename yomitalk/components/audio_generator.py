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
from typing import Generator, List, Optional, Tuple

import e2k

from yomitalk.common.character import (
    DISPLAY_NAMES,
    REQUIRED_MODEL_FILES,
    STYLE_ID_BY_NAME,
    Character,
)
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


class VoicevoxCoreManager:
    """Global VOICEVOX Core manager shared across all users."""

    # VOICEVOX Core paths as constants (VOICEVOX version is managed in
    # VOICEVOX_VERSION in Makefile)
    VOICEVOX_BASE_PATH = Path("voicevox_core/voicevox_core")
    VOICEVOX_MODELS_PATH = VOICEVOX_BASE_PATH / "models/vvms"
    VOICEVOX_DICT_PATH = VOICEVOX_BASE_PATH / "dict/open_jtalk_dic_utf_8-1.11"
    VOICEVOX_LIB_PATH = VOICEVOX_BASE_PATH / "onnxruntime/lib"

    def __init__(self) -> None:
        """Initialize global VOICEVOX Core manager."""
        self.core_initialized = False
        self.core_synthesizer: Optional[Synthesizer] = None

        # Initialize VOICEVOX Core if available
        if VOICEVOX_CORE_AVAILABLE:
            self._init_voicevox_core()

    def _init_voicevox_core(self) -> None:
        """Initialize VOICEVOX Core if components are available."""
        # Initialize flag is set to False by default
        self.core_initialized = False

        # 1. Check existence of required directories
        if (
            not self.VOICEVOX_MODELS_PATH.exists()
            or not self.VOICEVOX_DICT_PATH.exists()
        ):
            logger.warning(
                "Required VOICEVOX directories not found. Please run 'make download-voicevox-core'"
            )
            return

        try:
            # 2. Initialize OpenJtalk
            open_jtalk = OpenJtalk(str(self.VOICEVOX_DICT_PATH))

            # 3. Initialize ONNX Runtime
            runtime_path = str(
                self.VOICEVOX_LIB_PATH / "libvoicevox_onnxruntime.so.1.17.3"
            )

            if os.path.exists(runtime_path):
                logger.info("Loading ONNX runtime from local path")
                ort = Onnxruntime.load_once(filename=runtime_path)
            else:
                logger.info("Loading default ONNX runtime")
                ort = Onnxruntime.load_once()

            # 4. Initialize Synthesizer
            self.core_synthesizer = Synthesizer(ort, open_jtalk)

            # 5. Load required voice models
            loaded_count = self._load_voice_models()

            if loaded_count > 0:
                logger.info(
                    f"Successfully loaded {loaded_count}/{len(REQUIRED_MODEL_FILES)} voice models"
                )
                self.core_initialized = True
            else:
                logger.error("No voice models could be loaded")

        except Exception as e:
            logger.error(f"Failed to initialize VOICEVOX Core: {e}")
            self.core_synthesizer = None

    def _load_voice_models(self) -> int:
        """
        Load required voice models for VOICEVOX.

        Returns:
            int: Number of successfully loaded models
        """
        if self.core_synthesizer is None:
            return 0

        loaded_count = 0

        for model_file in REQUIRED_MODEL_FILES:
            model_path = self.VOICEVOX_MODELS_PATH / model_file

            if not model_path.exists():
                logger.warning(f"Required model file not found: {model_file}")
                continue

            try:
                with VoiceModelFile.open(str(model_path)) as model:
                    self.core_synthesizer.load_voice_model(model)
                    loaded_count += 1
                    logger.debug(f"Loaded voice model: {model_file}")
            except Exception as e:
                logger.error(f"Failed to load model {model_file}: {e}")

        return loaded_count

    def text_to_speech(self, text: str, style_id: int) -> bytes:
        """
        Generate audio data from text using VOICEVOX Core.

        Args:
            text: Text to convert to speech
            style_id: VOICEVOX style ID

        Returns:
            bytes: Generated WAV data
        """
        if not text.strip() or not self.core_synthesizer:
            return b""

        try:
            # Generate audio data from text
            wav_data: bytes = self.core_synthesizer.tts(text, style_id)
            logger.debug(f"Audio generation completed: {len(wav_data) // 1024} KB")
            return wav_data
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return b""

    def is_available(self) -> bool:
        """Check if VOICEVOX Core is available and initialized."""
        return self.core_initialized


# Global VOICEVOX Core manager instance
# This will be initialized once when the application starts
_global_voicevox_manager: Optional[VoicevoxCoreManager] = None


def get_global_voicevox_manager() -> Optional[VoicevoxCoreManager]:
    """Get the global VOICEVOX Core manager instance."""
    return _global_voicevox_manager


def initialize_global_voicevox_manager() -> VoicevoxCoreManager:
    """Initialize the global VOICEVOX Core manager."""
    global _global_voicevox_manager
    if _global_voicevox_manager is None:
        logger.info("Initializing global VOICEVOX Core manager")
        _global_voicevox_manager = VoicevoxCoreManager()
    return _global_voicevox_manager


# 単語タイプを表すEnum
class WordType(Enum):
    """単語タイプを表す列挙型"""

    BE_VERB = auto()
    PREPOSITION = auto()
    CONJUNCTION = auto()
    OTHER = auto()


class AudioGenerator:
    """Class for generating audio from text using global VOICEVOX Core manager."""

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

    CONVERSION_OVERRIDE = {
        "python": "パイソン",
        "git": "ギット",
        "github": "ギットハブ",
        "i": "アイ",
        "this": "ディス",
        "to": "トゥ",
        "a": "ア",
        "is": "イズ",
        "your": "ユア",
        "phone": "フォン",
        "the": "ザ",
        "thought": "ソート",
        "learn": "ラン",
        "with": "ウィズ",
        "api": "API",
        "ai": "AI",
        "VAE": "VAE",
        "spatial": "スペイシャル",
        "yomitalk": "ヨミトーク",
        "lovot": "ラボット",
    }

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

        # Audio generation progress variables
        self.audio_generation_progress = 0.0
        self.final_audio_path: Optional[str] = None

    @property
    def core_initialized(self) -> bool:
        """Check if VOICEVOX Core is initialized via global manager."""
        manager = get_global_voicevox_manager()
        return manager is not None and manager.is_available()

    def _convert_english_to_katakana(self, text: str) -> str:
        """
        英単語をカタカナに変換し、自然な息継ぎのタイミングで空白を制御する

        以下のルールに基づいて空白を制御:
        1. カンマや空白は息継ぎとなる
        2. 英単語の間は基本的に空白を入れない
        3. 前の英単語がbe動詞の場合は前に空白を入れる
        4. 英単語が前置詞または接続詞の場合は前に空白を入れる
        5. 一定文字数経過したら前に空白を入れる

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 英単語がカタカナに変換され、自然な息継ぎを考慮して空白が制御されたテキスト
        """
        # 大文字で始まる部分を分割する
        split_parts = self._split_capitalized_parts(text)

        # 英単語をカタカナに変換し、自然な息継ぎのための空白を制御
        return self._convert_parts_to_katakana(parts=split_parts, converter=e2k.C2K())

    def _split_capitalized_parts(self, text: str) -> List[str]:
        """
        テキストを英単語、数字、空白、記号などに分割する
        キャメルケースや略語パターンも考慮する

        Args:
            text (str): 分割するテキスト

        Returns:
            List[str]: 分割された部分のリスト
        """
        # アルファベット、数字、空白、その他に分割
        word_parts = re.findall(r"([A-Za-z]+|\d+|\s+|[^A-Za-z0-9\s]+)", text)
        result = []

        for part in word_parts:
            if re.match(r"^[A-Za-z]+$", part):
                # 大文字が続いて最後が小文字の"s"1文字の場合（複数形）を特別処理
                if re.match(r"^[A-Z]{2,}s$", part):
                    # 大文字部分とsを分離し、sは「ズ」に変換
                    uppercase_part = part[:-1]
                    result.extend([uppercase_part, "ズ"])
                else:
                    # 英単語のパターンに基づいて分割（キャメルケース対応）
                    segments = re.findall(
                        r"([A-Z]{2,}(?=[A-Z][a-z]|$)|[A-Z][a-z]*|[a-z]+)", part
                    )
                    result.extend(segments)
            else:
                # 英単語以外はそのまま追加
                result.append(part)
        return result

    def _convert_parts_to_katakana(
        self,
        parts: List[str],
        converter: e2k.C2K,
    ) -> str:
        """
        分割された部分をカタカナに変換し、適切な空白を制御する

        Args:
            parts: 分割されたテキスト部分のリスト
            converter: 英語からカタカナへの変換器

        Returns:
            str: 変換されたテキスト
        """
        result = []
        word_count = 0  # 息継ぎからのワード数カウント
        last_part = ""  # 最後の部分を保持
        is_english_word = False  # 英語かどうか
        is_last_part_english = False  # 最後の部分が英語かどうか

        for part in parts:
            is_last_part_english = is_english_word

            # 空文字やハイフンはスキップ
            if not part or part == "-":
                continue

            # 息継ぎを意味する句読点があればカウントリセット
            if set(last_part) & {".", "。", ",", "、", " "}:
                word_count = 0

            # 今回が空白1文字で前回が英単語であれば無視
            if part == " " and is_last_part_english:
                continue

            word_count += 1
            is_english_word = bool(re.match(r"^[A-Za-z]+$", part))
            is_all_uppercase = bool(re.match(r"^[A-Z]+$", part))

            # 空白挿入条件の判定
            if is_last_part_english and is_english_word:
                # 息継ぎのための空白を入れる条件
                needs_space = word_count >= 6  # 6単語以上続く

                # 特定の品詞の前後で息継ぎ
                if (
                    last_part.lower() in self.BE_VERBS
                    or part.lower() in self.PREPOSITIONS
                    or part.lower() in self.CONJUNCTIONS
                ) and word_count >= 4:
                    needs_space = True

                if needs_space:
                    result.append(" ")
                    word_count = 0  # カウントリセット

            # 変換処理
            if converted_part := self.CONVERSION_OVERRIDE.get(part.lower()):
                # 特定の単語は事前定義した変換を使用
                part_to_add = converted_part
            elif not is_english_word:
                # 英単語でない場合はそのまま
                part_to_add = part
            elif is_all_uppercase and len(part) < 7 and not is_romaji_readable(part):
                # 大文字のみで構成され、字数が少なく、ローマ字読みできない場合はアルファベット読みして欲しいためそのまま
                part_to_add = part
            else:
                part_to_add = part.capitalize() if is_all_uppercase else part
                # 英単語をカタカナに変換
                part_to_add = converter(part_to_add)

            result.append(part_to_add)
            last_part = part_to_add

        return "".join(result)

    def generate_character_conversation(
        self, podcast_text: str
    ) -> Generator[Optional[str], None, None]:
        """
        Generate audio for a character conversation from podcast text with streaming support.

        Args:
            podcast_text (str): Podcast text with character dialogue lines

        Yields:
            Optional[str]: Path to temporary audio files for streaming playback, or None if failed

        Returns:
            None: This generator has no return value
        """
        self.reset_audio_generation_state()

        # 前提条件チェック
        if not self.core_initialized:
            logger.error("VOICEVOX Core is not properly initialized.")
            yield None
            return

        if not podcast_text or podcast_text.strip() == "":
            logger.error("Podcast text is empty")
            yield None
            return

        try:
            # 英語をカタカナに変換
            podcast_text = self._convert_english_to_katakana(podcast_text)
            logger.info("Converted English words in podcast text to katakana")

            # 会話部分の抽出
            conversation_parts = self._extract_conversation_parts(podcast_text)

            if not conversation_parts:
                logger.error("No valid conversation parts found")
                yield None
                return

            # 一時ディレクトリの作成
            temp_dir = self.temp_dir / f"stream_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 音声生成と結合処理
            yield from self._generate_and_combine_audio(conversation_parts, temp_dir)

        except Exception as e:
            logger.error(f"Character conversation audio generation error: {e}")
            yield None
            return

    def _extract_conversation_parts(self, podcast_text: str) -> List[Tuple[str, str]]:
        """
        Podcast textから会話部分を抽出する

        Args:
            podcast_text (str): 会話テキスト

        Returns:
            List[Tuple[str, str]]: (話者名, セリフ)のタプルリスト
        """
        # Split the podcast text into lines
        lines = podcast_text.strip().split("\n")
        conversation_parts = []

        # キャラクターパターンを取得
        character_patterns = {
            char.display_name: [f"{char.display_name}:", f"{char.display_name}："]
            for char in Character
        }

        # 複数行のセリフを処理するために現在の話者と発言を記録
        current_speaker = None
        current_speech = ""

        # Process each line of the text
        for line in lines:
            line = line.strip()

            # 新しい話者の行かチェック
            found_new_speaker = False
            for character, patterns in character_patterns.items():
                for pattern in patterns:
                    if line.startswith(pattern):
                        # 前の話者の発言があれば追加
                        if current_speaker and current_speech:
                            conversation_parts.append((current_speaker, current_speech))

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

        # 会話部分が見つからない場合はフォーマット修正を試みる
        if not conversation_parts:
            logger.warning(
                "No valid conversation parts found. Attempting to fix format..."
            )
            fixed_text = self._fix_conversation_format(podcast_text)
            if fixed_text != podcast_text:
                return self._extract_conversation_parts(fixed_text)

        logger.info(f"Extracted {len(conversation_parts)} conversation parts")
        return conversation_parts

    def _generate_and_combine_audio(
        self,
        conversation_parts: List[Tuple[str, str]],
        temp_dir: Path,
    ) -> Generator[str, None, None]:
        """
        会話部分から音声生成と結合を行う

        Args:
            conversation_parts: (話者, セリフ)のリスト
            temp_dir: 一時ファイル保存ディレクトリ

        Yields:
            str: 生成された音声ファイルパス
        """
        wav_data_list = []  # メモリ上に直接音声データを保持するリスト
        temp_files = []  # 一時ファイルのパスを保持するリスト
        total_parts = len(conversation_parts)

        for i, (speaker, text) in enumerate(conversation_parts):
            # 進捗状況の更新
            self.audio_generation_progress = (i + 1) / total_parts * 0.8

            if not text.strip():
                continue

            # 音声生成
            style_id = STYLE_ID_BY_NAME[speaker]
            part_wav_data = self._text_to_speech(text, style_id)

            if part_wav_data:
                wav_data_list.append(part_wav_data)

                # 一時ファイルに書き込み、ストリーミング再生用に提供
                temp_file_path = temp_dir / f"part_{i:03d}_{speaker}.wav"
                with open(temp_file_path, "wb") as f:
                    f.write(part_wav_data)

                temp_files.append(str(temp_file_path))

                # ストリーミング再生用に現在のパートをyield
                yield str(temp_file_path)

        # メモリ上で音声データを結合して最終的な音声ファイルを作成
        if wav_data_list:
            combined_wav_data = self._combine_wav_data_in_memory(wav_data_list)

            if combined_wav_data:
                # 日付付きの最終的な出力ファイル名を生成
                now = datetime.datetime.now()
                date_str = now.strftime("%Y%m%d_%H%M%S")
                file_id = uuid.uuid4().hex[:8]

                self.output_dir.mkdir(parents=True, exist_ok=True)
                output_file = str(self.output_dir / f"audio_{date_str}_{file_id}.wav")

                try:
                    with open(output_file, "wb") as f:
                        f.write(combined_wav_data)

                    # クラス変数に最終的なファイルパスを保存
                    self.final_audio_path = output_file
                    self.audio_generation_progress = 1.0

                    yield output_file

                except Exception as e:
                    logger.error(f"音声ファイルの書き込みエラー: {str(e)}")
            else:
                logger.error("音声データの結合に失敗しました")

    def reset_audio_generation_state(self) -> None:
        """音声生成に関連する状態をリセットする"""
        self.audio_generation_progress = 0.0
        self.final_audio_path = None

    def _fix_conversation_format(self, text: str) -> str:
        """
        会話テキストのフォーマット問題を修正する

        Args:
            text (str): 元の会話テキスト

        Returns:
            str: 修正された会話テキスト
        """
        import re

        # 話者名の後にコロンがない場合修正
        for name in DISPLAY_NAMES:
            text = re.sub(f"({name})(\\s+)(?=[^\\s:])", f"{name}:\\2", text)

        # カスタム名のキャラクターを検出し、標準名にマッピング
        lines = text.split("\n")
        fixed_lines = []
        speaker_pattern = re.compile(r"^([^:：]+)[：:]\s*(.*)")

        current_speaker = None
        current_speech = []

        for line in lines:
            line_stripped = line.strip()
            match = speaker_pattern.match(line_stripped) if line_stripped else None

            if match:
                # 新しい話者が検出された場合、前の話者のセリフを追加
                if current_speaker and current_speech:
                    fixed_lines.append(f"{current_speaker}: {' '.join(current_speech)}")
                    current_speech = []

                speaker, speech = match.groups()

                # 既知のキャラクター名に最も近いものを探す
                best_match = None
                for name in DISPLAY_NAMES:
                    if name in speaker:
                        best_match = name
                        break

                # 最適なマッチが見つからない場合、デフォルトを設定
                current_speaker = best_match or Character.ZUNDAMON.display_name

                if speech.strip():
                    current_speech.append(speech.strip())
            elif current_speaker:
                # 現在の話者の発言として処理
                if line_stripped:
                    current_speech.append(line_stripped)
                elif current_speech:
                    # 段落区切りの空行
                    if not current_speech[-1].endswith("\n"):
                        current_speech[-1] += "\n"
            elif line_stripped:
                # 話者が一度も検出されていない場合はデフォルト設定
                current_speaker = Character.ZUNDAMON.display_name
                current_speech.append(line_stripped)

        # 最後の話者の発言を追加
        if current_speaker and current_speech:
            fixed_lines.append(f"{current_speaker}: {' '.join(current_speech)}")

        # 複数の話者が一行に存在する場合を分割
        result = []
        for line in fixed_lines:
            modified_line = line
            for name in DISPLAY_NAMES:
                if f"。{name}" in modified_line:
                    parts = modified_line.split(f"。{name}")
                    if len(parts) > 1:
                        if parts[0].strip():
                            result.append(f"{parts[0].strip()}。")
                        modified_line = f"{name}{parts[1]}"
            result.append(modified_line)

        return "\n".join(result)

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
        logger.debug(f"音声ファイル結合: {total_files}ファイル")

        # 全てのWAVファイルのパラメータとデータを読み込む
        wav_params_and_data: List[Tuple[wave._wave_params, bytes]] = []

        for wav_bytes in wav_data_list:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(wav_file.getnframes())
                wav_params_and_data.append((params, frames))

        # 結果を書き込むためのメモリバッファを作成
        output_buffer = io.BytesIO()

        with wave.open(output_buffer, "wb") as output_wav:
            # WAVパラメータを設定（最初のファイルと同じ）
            output_wav.setparams(wav_params_and_data[0][0])

            # 全てのフレームデータを書き込む
            for _, frames in wav_params_and_data:
                output_wav.writeframes(frames)

        # 結合されたWAVデータを返す
        return output_buffer.getvalue()

    def _text_to_speech(self, text: str, style_id: int) -> bytes:
        """
        Generate audio data from text using global VOICEVOX Core manager.

        Args:
            text: Text to convert to speech
            style_id: VOICEVOX style ID

        Returns:
            bytes: Generated WAV data
        """
        manager = get_global_voicevox_manager()
        if manager is None:
            logger.error("Global VOICEVOX manager is not available")
            return b""

        return manager.text_to_speech(text, style_id)
