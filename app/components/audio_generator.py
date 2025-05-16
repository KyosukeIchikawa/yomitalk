"""Module providing audio generation functionality.

Provides functionality for generating audio from text using VOICEVOX Core.
"""

import datetime
import os
import re
import shutil
import subprocess
import uuid
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional

import e2k

from app.utils.logger import logger
from app.utils.text_utils import is_romaji_readable

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

    def __init__(self) -> None:
        """Initialize AudioGenerator."""
        self.output_dir = Path("data/output")
        self.temp_dir = Path("data/temp/talks")

        # VOICEVOX Core
        self.core_initialized = False
        self.core_synthesizer: Optional[Synthesizer] = None
        self.core_style_ids = {
            "ずんだもん": 3,  # Zundamon (sweet)
            "四国めたん": 2,  # Shikoku Metan (normal)
            "九州そら": 16,  # Kyushu Sora (normal)
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
        c2k = e2k.C2K()
        return self._process_text_conversion(text, c2k)

    def _process_text_conversion(self, text: str, converter: e2k.C2K) -> str:
        """
        テキスト変換処理の主要部分を担当します。

        Args:
            text (str): 変換するテキスト
            converter: カタカナ変換ユーティリティ

        Returns:
            str: 処理されたテキスト
        """
        # 変換オーバーライド（指定された単語は固定の変換を使用）
        conversion_override = {"this": "ディス", "to": "トゥ", "a": "ア"}

        # 英単語と非英単語を分割するための正規表現パターン
        pattern = r"([A-Za-z]+|[^A-Za-z]+)"
        parts = re.findall(pattern, text)

        # 大文字で始まる部分を分割する
        split_parts = self._split_capitalized_parts(parts)

        # 英単語をカタカナに変換し、自然な息継ぎのための空白を制御
        return self._convert_parts_to_katakana(
            split_parts, conversion_override, converter
        )

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
        conversion_override: dict,
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
            is_english_word = self._is_english_word(part, conversion_override)

            # 次の部分を確認（あれば）
            next_part = parts[i + 1] if i + 1 < len(parts) else ""
            next_is_english = (
                self._is_english_word(next_part, conversion_override)
                if next_part
                else False
            )

            # 英単語の場合の処理
            if is_english_word:
                self._process_english_word(
                    part,
                    next_part,
                    next_is_english,
                    conversion_override,
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

    def _is_english_word(self, part: str, conversion_override: dict) -> bool:
        """文字列が変換対象の英単語かどうかを判定します。"""
        if not part:
            return False

        return bool(
            part.lower() in conversion_override
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
        conversion_override: dict,
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
        if word_lower in conversion_override:
            katakana_part = conversion_override[word_lower]
        else:
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

    def _create_final_audio_file(self, temp_wav_files: List[str]) -> str:
        """
        Create the final audio file by combining temporary audio files.

        Args:
            temp_wav_files (List[str]): List of temporary audio file paths

        Returns:
            str: Path to the final audio file
        """
        if not temp_wav_files:
            return ""

        # 日付付きの最終的な出力ファイル名を生成
        now = datetime.datetime.now()
        # セキュリティのため、一意のIDを使用する（日時とUUIDを組み合わせる）
        date_str = now.strftime("%Y%m%d_%H%M%S")
        file_id = uuid.uuid4().hex[:8]

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = str(self.output_dir / f"audio_{date_str}_{file_id}.wav")

        # 単一ファイルならそのまま使用
        if len(temp_wav_files) == 1:
            os.rename(temp_wav_files[0], output_file)
            return output_file

        # 複数ファイルなら結合
        try:
            # ファイルリストを生成
            list_file = str(self.temp_dir / f"filelist_{uuid.uuid4()}.txt")
            with open(list_file, "w") as f:
                for file in temp_wav_files:
                    f.write(f"file '{os.path.abspath(file)}'\n")

            # ffmpegでファイルを結合
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file,
                    "-c",
                    "copy",
                    output_file,
                ],
                check=True,
            )

            # 一時ファイルの後片付け
            if os.path.exists(list_file):
                os.remove(list_file)

            # 元のWAVファイルも削除
            for file in temp_wav_files:
                if os.path.exists(file):
                    os.remove(file)

            return output_file

        except Exception as e:
            logger.error(f"Error combining audio files: {e}")
            # エラー時は先頭のファイルを返す（少なくとも何かが再生できるように）
            if temp_wav_files and os.path.exists(temp_wav_files[0]):
                return temp_wav_files[0]
            return ""

    def _split_text(self, text: str, max_length: int = 100) -> List[str]:
        """
        Split text into appropriate lengths.

        Args:
            text (str): Text to split
            max_length (int): Maximum characters per chunk

        Returns:
            list: List of split text
        """
        if not text:
            return []

        chunks: List[str] = []
        current_chunk = ""

        # Split by paragraphs
        paragraphs = text.split("\n")

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                continue

            # Handle long paragraphs
            if len(paragraph) > max_length:
                current_chunk = self._process_long_paragraph(
                    paragraph, chunks, current_chunk, max_length
                )
            else:
                # Add paragraph to current chunk or start a new one
                current_chunk = self._add_paragraph_to_chunk(
                    paragraph, chunks, current_chunk, max_length
                )

        # Add the last chunk if it exists
        if current_chunk and current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _process_long_paragraph(
        self, paragraph: str, chunks: List[str], current_chunk: str, max_length: int
    ) -> str:
        """
        Process long paragraphs.

        Args:
            paragraph (str): Paragraph to process
            chunks (list): List of existing chunks
            current_chunk (str): Current chunk
            max_length (int): Maximum chunk length

        Returns:
            str: Updated current_chunk
        """
        sentences = paragraph.replace("。", "。|").split("|")

        for sentence in sentences:
            if not sentence.strip():
                continue

            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        return current_chunk

    def _add_paragraph_to_chunk(
        self, paragraph: str, chunks: List[str], current_chunk: str, max_length: int
    ) -> str:
        """
        Add paragraph to chunk.

        Args:
            paragraph (str): Paragraph to add
            chunks (list): List of chunks
            current_chunk (str): Current chunk
            max_length (int): Maximum chunk length

        Returns:
            str: Updated current_chunk
        """
        # Check if paragraph can be added to current_chunk
        if len(current_chunk) + len(paragraph) <= max_length:
            current_chunk += paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph

        return current_chunk

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

        # 一時ファイルディレクトリが存在する場合は削除
        if self.temp_dir.exists():
            try:
                # ディレクトリが空でない場合でも再帰的に削除
                shutil.rmtree(self.temp_dir)
                logger.debug("一時ディレクトリを削除しました")
            except Exception:
                # セキュリティのためファイルパスやスタックトレースは記録しない
                logger.error("一時ファイル削除中にエラーが発生しました")
                # エラーが発生してもディレクトリを作成して処理を続行する
        # 一時ファイルディレクトリを作成
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 英語をカタカナに変換
            podcast_text = self._convert_english_to_katakana(podcast_text)
            logger.info("Converted English words in podcast text to katakana")

            # Split the podcast text into lines
            lines = podcast_text.strip().split("\n")
            conversation_parts = []

            # サポートされるキャラクター名とそのパターン
            character_patterns = {
                "ずんだもん": ["ずんだもん:", "ずんだもん："],
                "四国めたん": ["四国めたん:", "四国めたん："],
                "九州そら": ["九州そら:", "九州そら："],
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
            temp_wav_files = []
            for i, (speaker, text) in enumerate(conversation_parts):
                style_id = self.core_style_ids.get(
                    speaker, 3
                )  # Default to Zundamon if not found
                logger.info(f"Generating audio for {speaker} (style_id: {style_id})")

                # Split text into chunks if it's too long
                text_chunks = self._split_text(text, max_length=100)
                chunk_wavs = []
                logger.info(f"Split into {len(text_chunks)} chunks")

                # Generate audio for each chunk
                for j, chunk in enumerate(text_chunks):
                    if not chunk.strip():
                        logger.warning(
                            f"Empty chunk detected (part {i}, chunk {j}), skipping..."
                        )
                        continue

                    # Generate audio using core
                    if self.core_synthesizer is not None:  # Type check for mypy
                        wav_data = self.core_synthesizer.tts(chunk, style_id)

                        # Save to temporary file
                        temp_file = str(self.temp_dir / f"part_{i}_chunk_{j}.wav")
                        with open(temp_file, "wb") as f:
                            f.write(wav_data)
                        chunk_wavs.append(temp_file)
                        # セキュリティのため詳細なパスを記録しない
                        logger.debug(f"チャンク {j} を保存しました")

                # Combine chunks for this part
                if chunk_wavs:
                    if len(chunk_wavs) > 1:
                        part_file = str(self.temp_dir / f"part_{i}.wav")
                        self._combine_audio_files(chunk_wavs, part_file)
                        # セキュリティのためファイルパスを記録しない
                        logger.debug(f"{len(chunk_wavs)}個のチャンクを結合しました")
                        temp_wav_files.append(part_file)

                        # Clean up chunk files
                        for chunk_wav in chunk_wavs:
                            os.unlink(chunk_wav)
                    else:
                        # Only one chunk, no need to combine
                        # logger.debug(f"Using single chunk file: {chunk_wavs[0]}")
                        # セキュリティのためファイルパスをログに記録しない
                        logger.debug("単一チャンクファイルを使用します")
                        temp_wav_files.append(chunk_wavs[0])

            # Combine all parts to create the final audio file
            if temp_wav_files:
                logger.info(
                    f"Combining {len(temp_wav_files)} audio parts into final file"
                )
                final_path = self._create_final_audio_file(temp_wav_files)
                logger.info("音声ファイルを生成しました")
                return final_path
            else:
                logger.error("No audio parts were generated")
                return None

        except Exception as e:
            logger.error(f"Character conversation audio generation error: {e}")
            return None

    def _combine_audio_files(self, input_files: List[str], output_file: str) -> None:
        """
        Combine multiple audio files into one using FFmpeg.

        Args:
            input_files: List of input audio file paths
            output_file: Path for the output combined file
        """
        if not input_files:
            return

        if len(input_files) == 1:
            # If there's only one file, just copy it
            os.rename(input_files[0], output_file)
            return

        # Create a file list for FFmpeg
        list_file = str(self.temp_dir / f"filelist_{uuid.uuid4()}.txt")
        with open(list_file, "w") as f:
            for file in input_files:
                f.write(f"file '{os.path.abspath(file)}'\n")

        # Concatenate files with FFmpeg
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            output_file,
        ]

        subprocess.run(cmd, check=True)

        # Delete the list file
        if os.path.exists(list_file):
            os.remove(list_file)

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
        character_names = ["ずんだもん", "四国めたん", "九州そら"]

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

    def generate_audio(self, podcast_text: str) -> Optional[str]:
        """
        Generate audio for a podcast from podcast text.

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

        # 一時ファイルディレクトリが存在する場合は削除
        if self.temp_dir.exists():
            try:
                # ディレクトリが空でない場合でも再帰的に削除
                shutil.rmtree(self.temp_dir)
                logger.debug("一時ディレクトリを削除しました")
            except Exception:
                # セキュリティのためファイルパスやスタックトレースは記録しない
                logger.error("一時ファイル削除中にエラーが発生しました")
                # エラーが発生してもディレクトリを作成して処理を続行する
        # 一時ファイルディレクトリを作成
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 英語をカタカナに変換
            podcast_text = self._convert_english_to_katakana(podcast_text)
            logger.info("Converted English words in podcast text to katakana")

            # Split the podcast text into lines
            lines = podcast_text.strip().split("\n")
            conversation_parts = []

            # サポートされるキャラクター名とそのパターン
            character_patterns = {
                "ずんだもん": ["ずんだもん:", "ずんだもん："],
                "四国めたん": ["四国めたん:", "四国めたん："],
                "九州そら": ["九州そら:", "九州そら："],
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
                    return self.generate_audio(fixed_text)
                else:
                    logger.error("Could not parse any valid conversation parts")
                    return None

            # Generate audio for each conversation part
            temp_wav_files = []
            for i, (speaker, text) in enumerate(conversation_parts):
                style_id = self.core_style_ids.get(
                    speaker, 3
                )  # Default to Zundamon if not found
                logger.info(f"Generating audio for {speaker} (style_id: {style_id})")

                # Split text into chunks if it's too long
                text_chunks = self._split_text(text, max_length=100)
                chunk_wavs = []
                logger.info(f"Split into {len(text_chunks)} chunks")

                # Generate audio for each chunk
                for j, chunk in enumerate(text_chunks):
                    if not chunk.strip():
                        logger.warning(
                            f"Empty chunk detected (part {i}, chunk {j}), skipping..."
                        )
                        continue

                    # Generate audio using core
                    if self.core_synthesizer is not None:  # Type check for mypy
                        wav_data = self.core_synthesizer.tts(chunk, style_id)

                        # Save to temporary file
                        temp_file = str(self.temp_dir / f"part_{i}_chunk_{j}.wav")
                        with open(temp_file, "wb") as f:
                            f.write(wav_data)
                        chunk_wavs.append(temp_file)
                        # セキュリティのため詳細なパスを記録しない
                        logger.debug(f"チャンク {j} を保存しました")

                # Combine chunks for this part
                if chunk_wavs:
                    if len(chunk_wavs) > 1:
                        part_file = str(self.temp_dir / f"part_{i}.wav")
                        self._combine_audio_files(chunk_wavs, part_file)
                        # セキュリティのためファイルパスを記録しない
                        logger.debug(f"{len(chunk_wavs)}個のチャンクを結合しました")
                        temp_wav_files.append(part_file)

                        # Clean up chunk files
                        for chunk_wav in chunk_wavs:
                            os.unlink(chunk_wav)
                    else:
                        # Only one chunk, no need to combine
                        # logger.debug(f"Using single chunk file: {chunk_wavs[0]}")
                        # セキュリティのためファイルパスをログに記録しない
                        logger.debug("単一チャンクファイルを使用します")
                        temp_wav_files.append(chunk_wavs[0])

            # Combine all parts to create the final audio file
            if temp_wav_files:
                logger.info(
                    f"Combining {len(temp_wav_files)} audio parts into final file"
                )
                final_path = self._create_final_audio_file(temp_wav_files)
                logger.info("音声ファイルを生成しました")
                return final_path
            else:
                logger.error("No audio parts were generated")
                return None

        except Exception as e:
            logger.error(f"Podcast audio generation error: {e}")
            return None
