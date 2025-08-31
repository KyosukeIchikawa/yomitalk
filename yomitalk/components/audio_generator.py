"""Module providing audio generation functionality.

Provides functionality for generating audio from text using VOICEVOX Core.
"""

import datetime
import io
import os
import re
import unicodedata
import uuid
import wave
from enum import Enum, auto
from pathlib import Path
from typing import Generator, List, Optional, Tuple

import e2k

from voicevox_core.blocking import (
    Onnxruntime,
    OpenJtalk,
    Synthesizer,
    UserDict,
    VoiceModelFile,
)
from yomitalk.common.character import (
    DISPLAY_NAMES,
    REQUIRED_MODEL_FILES,
    STYLE_ID_BY_NAME,
    CHARACTER_BY_STYLE_ID,
    Character,
)
from yomitalk.utils.logger import logger
from yomitalk.utils.text_utils import (
    is_romaji_readable,
    calculate_text_similarity,
)


class VoicevoxCoreManager:
    """Global VOICEVOX Core manager shared across all users."""

    # VOICEVOX Core paths as constants (VOICEVOX version is managed in
    # VOICEVOX_VERSION in Makefile)
    VOICEVOX_BASE_PATH = Path("voicevox_core/voicevox_core")
    VOICEVOX_MODELS_PATH = VOICEVOX_BASE_PATH / "models/vvms"
    VOICEVOX_DICT_PATH = VOICEVOX_BASE_PATH / "dict/open_jtalk_dic_utf_8-1.11"
    VOICEVOX_LIB_PATH = VOICEVOX_BASE_PATH / "onnxruntime/lib"
    USER_DICT_PATH = Path("assets/dictionaries/user_dictionary.json")

    def __init__(self) -> None:
        """Initialize global VOICEVOX Core manager."""
        self.core_initialized = False
        self.core_synthesizer: Optional[Synthesizer] = None
        self.user_dict_words: set = set()

        # Initialize VOICEVOX Core
        self._init_voicevox_core()

    def _init_voicevox_core(self) -> None:
        """Initialize VOICEVOX Core if components are available."""
        # Initialize flag is set to False by default
        self.core_initialized = False

        # 1. Check existence of required directories
        if not self.VOICEVOX_MODELS_PATH.exists() or not self.VOICEVOX_DICT_PATH.exists():
            logger.warning("Required VOICEVOX directories not found. Please run 'make download-voicevox-core'")
            return

        try:
            # 2. Initialize OpenJtalk with user dictionary if available
            open_jtalk = self._initialize_openjtalk()

            # 3. Initialize ONNX Runtime
            runtime_path = str(self.VOICEVOX_LIB_PATH / "libvoicevox_onnxruntime.so.1.17.3")

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
                logger.info(f"Successfully loaded {loaded_count}/{len(REQUIRED_MODEL_FILES)} voice models")
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

    def _initialize_openjtalk(self) -> "OpenJtalk":
        """
        Initialize OpenJtalk with user dictionary if available.

        Returns:
            OpenJtalk: Initialized OpenJtalk instance
        """
        # Initialize OpenJtalk with system dictionary
        open_jtalk = OpenJtalk(str(self.VOICEVOX_DICT_PATH))

        # Load user dictionary if it exists
        if self.USER_DICT_PATH.exists():
            try:
                user_dict = UserDict()
                user_dict.load(str(self.USER_DICT_PATH))

                # Use the user dictionary with OpenJtalk
                open_jtalk.use_user_dict(user_dict)
                logger.info(f"Loaded user dictionary: {self.USER_DICT_PATH}")

                # Log dictionary contents for debugging
                words = user_dict.to_dict()
                logger.info(f"User dictionary contains {len(words)} words")
                for word in words.values():
                    logger.debug(f"  {word.surface} -> {word.pronunciation}")

                # Load user dictionary words for conversion checking
                self._load_user_dict_words_from_dict(user_dict)

            except Exception as e:
                logger.warning(f"Failed to load user dictionary: {e}")
                logger.info("Continuing with system dictionary only")
        else:
            logger.info(f"User dictionary not found: {self.USER_DICT_PATH}")
            logger.info("Using system dictionary only")

        return open_jtalk

    def text_to_speech(self, text: str, style_id: int) -> bytes:
        """
        Generate audio data from text using VOICEVOX Core with character-specific pitch adjustment.

        Args:
            text: Text to convert to speech
            style_id: VOICEVOX style ID

        Returns:
            bytes: Generated WAV data
        """
        if not text.strip() or not self.core_synthesizer:
            return b""

        try:
            # Get character-specific speed scale
            character = CHARACTER_BY_STYLE_ID.get(style_id)
            speed_scale = character.speed_scale if character else 1.0

            wav_data: bytes
            if speed_scale != 1.0:
                # Use create_audio_query + synthesis for speed adjustment
                audio_query = self.core_synthesizer.create_audio_query(text, style_id)
                audio_query.speed_scale = speed_scale
                wav_data = self.core_synthesizer.synthesis(audio_query, style_id)
            else:
                # Use standard tts method for no speed adjustment
                wav_data = self.core_synthesizer.tts(text, style_id)

            logger.debug(f"Audio generation completed: {len(wav_data) // 1024} KB (speed_scale: {speed_scale})")
            return wav_data
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return b""

    def is_available(self) -> bool:
        """Check if VOICEVOX Core is available and initialized."""
        return self.core_initialized

    def _load_user_dict_words_from_dict(self, user_dict: UserDict) -> None:
        """
        Load user dictionary words from UserDict for conversion checking.

        Args:
            user_dict: UserDict instance to load words from
        """
        self.user_dict_words = set()

        try:
            # Get all words from dictionary
            dict_words = user_dict.to_dict()
            for word in dict_words.values():
                # Add both the full-width surface form and potential original form
                self.user_dict_words.add(word.surface)

                # Convert full-width to half-width characters
                original_surface = unicodedata.normalize("NFKC", word.surface)

                if original_surface != word.surface:
                    self.user_dict_words.add(original_surface)

                logger.debug(f"Loaded user dict word: {word.surface} (original: {original_surface})")

        except Exception as e:
            logger.warning(f"Failed to load user dictionary words: {e}")

        logger.info(f"Loaded {len(self.user_dict_words)} user dictionary surface forms for conversion checking")

    def is_word_in_user_dict(self, word: str) -> bool:
        """
        Check if a word is in the user dictionary.

        Args:
            word: Word to check

        Returns:
            bool: True if word is in user dictionary
        """
        return word in self.user_dict_words


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
        "is": "イズ",
        "your": "ユア",
        "phone": "フォン",
        "the": "ザ",
        "thought": "ソート",
        "learn": "ラン",
        "with": "ウィズ",
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
        self.output_dir = session_output_dir if session_output_dir else Path("data/output")
        self.temp_dir = session_temp_dir if session_temp_dir else Path("data/temp/talks")

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
                    segments = re.findall(r"([A-Z]{2,}(?=[A-Z][a-z]|$)|[A-Z][a-z]*|[a-z]+)", part)
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

        for i, part in enumerate(parts):
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
                if (last_part.lower() in self.BE_VERBS or part.lower() in self.PREPOSITIONS or part.lower() in self.CONJUNCTIONS) and word_count >= 4:
                    needs_space = True

                if needs_space:
                    result.append(" ")
                    word_count = 0  # カウントリセット

            # 変換処理
            # "A"の特別な処理: 文脈に応じて変換を決定
            if part.lower() == "a":
                part_to_add = self._convert_a_contextually(part, parts, i)
            elif converted_part := self.CONVERSION_OVERRIDE.get(part.lower()):
                # 特定の単語は事前定義した変換を使用（ただし"a"は上で処理済み）
                part_to_add = converted_part
            elif self._is_in_user_dict(part):
                # ユーザー辞書に登録済みの単語はそのまま使用（VOICEVOXが変換する）
                part_to_add = part
            elif not is_english_word:
                # 英単語でない場合はそのまま
                part_to_add = part
            elif is_all_uppercase and (len(part) <= 3 or (len(part) <= 6 and not is_romaji_readable(part))):
                # 大文字のみで構成され、字数が少なくてローマ字読みできない場合はアルファベット読みして欲しいためそのまま
                # （字数が3文字以下なら基本的にアルファベット読みで良く, 駄目であればCONVERSION_OVERRIDEなどで変換する）
                part_to_add = part
            else:
                part_to_add = part.capitalize() if is_all_uppercase else part
                # 英単語をカタカナに変換
                part_to_add = converter(part_to_add)

            result.append(part_to_add)
            last_part = part_to_add

        return "".join(result)

    def _convert_a_contextually(self, part: str, parts: List[str], current_index: int) -> str:
        """
        "A"/"a"を文脈に応じて変換する

        Args:
            part: 現在の部分 ("A" または "a")
            parts: 全体の分割された部分のリスト
            current_index: 現在の部分のインデックス

        Returns:
            str: 変換された文字列
        """
        # 冠詞として使われている場合のみ"ア"に変換
        # 次に空白があり、その後に英単語がある場合（例: "a pen" -> ['a', ' ', 'pen']）
        if current_index + 1 < len(parts) and parts[current_index + 1] == " ":
            # 空白の後に英単語を探す
            next_word_index = current_index + 2
            if next_word_index < len(parts):
                next_word = parts[next_word_index]
                # 次が英単語の場合は冠詞として"ア"
                if re.match(r"^[A-Za-z]+$", next_word):
                    return "ア"

        # それ以外の場合は技術用語として"A"のまま
        return part

    def generate_character_conversation(self, podcast_text: str, resume_from_part: int = 0, existing_parts: Optional[List[str]] = None) -> Generator[Optional[str], None, None]:
        """
        Generate audio for a character conversation from podcast text with streaming support and resume capability.

        Args:
            podcast_text (str): Podcast text with character dialogue lines
            resume_from_part (int): Part number to resume from (0 = start from beginning)
            existing_parts (List[str], optional): List of existing audio part file paths

        Yields:
            Optional[str]: Path to temporary audio files for streaming playback, or None if failed

        Returns:
            None: This generator has no return value
        """
        logger.info("Audio generation started")
        logger.debug(f"Resume from part: {resume_from_part}")
        logger.debug(f"Existing parts: {len(existing_parts) if existing_parts else 0}")
        if existing_parts:
            logger.debug(f"Existing part files: {[os.path.basename(p) for p in existing_parts]}")

        if resume_from_part == 0 and not existing_parts:
            logger.debug("Resetting audio generation state (new generation)")
            self.reset_audio_generation_state()
        else:
            logger.debug("NOT resetting state (resume mode)")

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

            logger.debug(f"Extracted {len(conversation_parts)} conversation parts")
            for i, (speaker, text) in enumerate(conversation_parts):
                logger.debug(f"Part {i}: {speaker} - {len(text)} chars")

            if not conversation_parts:
                logger.error("No valid conversation parts found")
                yield None
                return

            # 一時ディレクトリの作成（再開時は既存ディレクトリを利用）
            if resume_from_part > 0 and existing_parts:
                # 再開時：既存ファイルのディレクトリを使用
                existing_dir = Path(existing_parts[0]).parent
                temp_dir = existing_dir
                logger.debug(f"Reusing existing directory for resume: {temp_dir.name}")
            else:
                # 新規生成：新しいディレクトリを作成
                temp_dir = self.temp_dir / f"stream_{uuid.uuid4().hex[:8]}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created new directory for fresh generation: {temp_dir.name}")

            # 音声生成と結合処理（部分再開対応）
            yield from self._generate_and_combine_audio_with_resume(conversation_parts, temp_dir, resume_from_part, existing_parts or [])

        except Exception as e:
            logger.error(f"Character conversation audio generation error: {e}")
            yield None
            return

    def _find_best_character_match(self, input_name: str) -> str:
        """
        入力された名前に最も近いキャラクター名を見つける（ファジーマッチング）

        Args:
            input_name (str): 入力された名前（表記ゆれの可能性あり）

        Returns:
            str: 最も近いキャラクター名（正式名称）
        """
        if not input_name:
            return Character.ZUNDAMON.display_name

        # まず完全一致をチェック
        for character_name in DISPLAY_NAMES:
            if input_name == character_name:
                return character_name

        # 類似度計算
        best_match = Character.ZUNDAMON.display_name
        best_similarity = 0.0

        for character_name in DISPLAY_NAMES:
            similarity = calculate_text_similarity(input_name, character_name)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = character_name

        # 最低閾値をチェック（類似度が低すぎる場合はデフォルト）
        similarity_threshold = 0.3
        if best_similarity < similarity_threshold:
            logger.debug(f"Character name '{input_name}' similarity too low ({best_similarity:.2f}), using default")
            return Character.ZUNDAMON.display_name

        logger.debug(f"Character name '{input_name}' matched to '{best_match}' (similarity: {best_similarity:.2f})")
        return best_match

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
        character_patterns = {char.display_name: [f"{char.display_name}:", f"{char.display_name}："] for char in Character}

        # 複数行のセリフを処理するために現在の話者と発言を記録
        current_speaker = None
        current_speech = ""

        # Process each line of the text
        for line in lines:
            line = line.strip()

            # 新しい話者の行かチェック（曖昧マッチング対応）
            found_new_speaker = False
            matched_speaker = None
            matched_speech = ""

            # まず完全一致をチェック
            for character, patterns in character_patterns.items():
                for pattern in patterns:
                    if line.startswith(pattern):
                        matched_speaker = character
                        matched_speech = line.replace(pattern, "", 1).strip()
                        found_new_speaker = True
                        break
                if found_new_speaker:
                    break

            # 完全一致しない場合、曖昧マッチングを試行
            if not found_new_speaker:
                # 行が "話者名:" または "話者名：" のパターンかチェック
                speaker_pattern = re.match(r"^([^:：]+)[：:]\s*(.*)", line)
                if speaker_pattern:
                    potential_speaker, speech = speaker_pattern.groups()
                    potential_speaker = potential_speaker.strip()

                    # 曖昧マッチングで最適なキャラクターを探す
                    best_character = self._find_best_character_match(potential_speaker)

                    # マッチした場合
                    if best_character:
                        matched_speaker = best_character
                        matched_speech = speech.strip()
                        found_new_speaker = True
                        logger.debug(f"Fuzzy matched '{potential_speaker}' to '{best_character}'")

            # 新しい話者が見つかった場合
            if found_new_speaker and matched_speaker:
                # 前の話者の発言があれば追加
                if current_speaker and current_speech:
                    conversation_parts.append((current_speaker, current_speech))

                # 新しい話者と発言を設定
                current_speaker = matched_speaker
                current_speech = matched_speech
            # 話者の切り替えがなく、現在の話者が存在する場合、行を現在の発言に追加
            elif not found_new_speaker and current_speaker:
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
            logger.warning("No valid conversation parts found. Attempting to fix format...")
            fixed_text = self._fix_conversation_format(podcast_text)
            if fixed_text != podcast_text:
                return self._extract_conversation_parts(fixed_text)

        logger.info(f"Extracted {len(conversation_parts)} conversation parts")
        return conversation_parts

    def _generate_and_combine_audio_with_resume(
        self, conversation_parts: List[Tuple[str, str]], temp_dir: Path, resume_from_part: int = 0, existing_parts: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """
        会話部分から音声生成と結合を行う（部分再開対応）

        Args:
            conversation_parts: (話者, セリフ)のリスト
            temp_dir: 一時ファイル保存ディレクトリ
            resume_from_part: 再開する部分のインデックス
            existing_parts: 既存の音声パートファイルのリスト

        Yields:
            str: 生成された音声ファイルパス
        """
        logger.info("Starting audio generation and combination")
        logger.debug(f"Conversation parts count: {len(conversation_parts)}")
        logger.debug(f"Resume from part: {resume_from_part}")
        logger.debug(f"Existing parts count: {len(existing_parts or [])}")

        wav_data_list = []  # メモリ上に直接音声データを保持するリスト
        temp_files = []  # 一時ファイルのパスを保持するリスト
        total_parts = len(conversation_parts)

        logger.info(f"Starting audio generation: total_parts={total_parts}, resume_from_part={resume_from_part}, existing_parts={len(existing_parts or [])}")

        # 既存のパートがある場合、それらをまず yield し、wav_data_list に追加
        if existing_parts and resume_from_part > 0:
            logger.info(f"PROCESSING {len(existing_parts)} existing parts...")
            for i, existing_part_path in enumerate(existing_parts):
                if existing_part_path and os.path.exists(existing_part_path):
                    logger.debug(f"Restoring existing part {i}: {os.path.basename(existing_part_path)}")
                    # 既存パートの音声データを読み込んで wav_data_list に追加
                    try:
                        with open(existing_part_path, "rb") as f:
                            existing_wav_data = f.read()
                        wav_data_list.append(existing_wav_data)
                        temp_files.append(existing_part_path)

                        # 既存パートを yield（ストリーミング再生用）
                        logger.debug(f"Yielding existing part {i} for streaming")
                        yield existing_part_path
                    except Exception as e:
                        logger.error(f"Failed to load existing part {existing_part_path}: {e}")
                else:
                    logger.warning(f"Existing part {i} does not exist: {os.path.basename(existing_part_path) if existing_part_path else 'None'}")

        # resume_from_part から新しい音声生成を開始
        logger.info(f"Starting NEW generation from part {resume_from_part} to {total_parts - 1}")
        for i in range(resume_from_part, total_parts):
            speaker, text = conversation_parts[i]

            # 進捗状況の更新
            self.audio_generation_progress = (i + 1) / total_parts * 0.8

            if not text.strip():
                logger.debug(f"Skipping empty text for part {i}")
                continue

            logger.debug(f"Generating NEW part {i}: {speaker} - {len(text)} chars")

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
                logger.debug(f"Generated and yielding NEW part {i}: {temp_file_path.name}")
                yield str(temp_file_path)
            else:
                logger.error(f"Failed to generate audio for part {i}")

        # メモリ上で音声データを結合して最終的な音声ファイルを作成
        if wav_data_list:
            logger.info(f"Combining {len(wav_data_list)} audio parts into final file")
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

                    logger.info(f"Final combined audio created: {output_file}")
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

                # 曖昧マッチングで最適なキャラクター名を探す
                best_match = self._find_best_character_match(speaker)

                # 曖昧マッチングの結果を使用
                current_speaker = best_match

                if speech.strip():
                    current_speech.append(speech.strip())
            elif current_speaker:
                # 現在の話者の発言として処理
                if line_stripped:
                    current_speech.append(line_stripped)
                elif current_speech and not current_speech[-1].endswith("\n"):
                    # 段落区切りの空行
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

    def _is_in_user_dict(self, word: str) -> bool:
        """
        Check if a word is in the user dictionary.

        Args:
            word: Word to check

        Returns:
            bool: True if word is in user dictionary
        """
        manager = get_global_voicevox_manager()
        if manager is None:
            return False
        return manager.is_word_in_user_dict(word)
