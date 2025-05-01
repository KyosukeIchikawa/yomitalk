"""Module providing audio generation functionality.

Provides functionality for generating audio from text using VOICEVOX Core.
"""

import os
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional

from app.utils.logger import logger

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


class AudioGenerator:
    """Class for generating audio from text."""

    # VOICEVOX Core paths as constants (VOICEVOX version is managed in
    # VOICEVOX_VERSION in Makefile)
    VOICEVOX_BASE_PATH = Path("voicevox_core/voicevox_core")
    VOICEVOX_MODELS_PATH = VOICEVOX_BASE_PATH / "models/vvms"
    VOICEVOX_DICT_PATH = VOICEVOX_BASE_PATH / "dict/open_jtalk_dic_utf_8-1.11"
    VOICEVOX_LIB_PATH = VOICEVOX_BASE_PATH / "onnxruntime/lib"

    def __init__(self) -> None:
        """Initialize AudioGenerator."""
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # VOICEVOX Core
        self.core_initialized = False
        self.core_synthesizer: Optional[Synthesizer] = None
        self.core_style_ids = {
            "ずんだもん": 3,  # Zundamon (sweet)
            "四国めたん": 2,  # Shikoku Metan (normal)
            "九州そら": 16,  # Kyushu Sora (normal)
        }

        # English to Japanese name mapping
        self.voice_name_mapping = {
            "Zundamon": "ずんだもん",
            "Shikoku Metan": "四国めたん",
            "Kyushu Sora": "九州そら",
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

    def generate_audio(
        self,
        text: str,
        voice_type: str = "Zundamon",
    ) -> Optional[str]:
        """
        Generate audio from text.

        Args:
            text (str): Text to convert to audio
            voice_type (str): Voice type (one of 'Zundamon', 'Shikoku Metan', 'Kyushu Sora')

        Returns:
            str: Path to the generated audio file
        """
        if not text or text.strip() == "":
            return None

        try:
            # Check if VOICEVOX Core is available
            if not VOICEVOX_CORE_AVAILABLE or not self.core_initialized:
                error_message = (
                    "VOICEVOX Core is not available or not properly initialized."
                )
                if not VOICEVOX_CORE_AVAILABLE:
                    error_message += " VOICEVOX module is not installed."
                elif not self.core_initialized:
                    error_message += " Failed to initialize VOICEVOX."
                error_message += (
                    "\nRun 'make download-voicevox-core' to set up VOICEVOX."
                )
                logger.error(error_message)
                return None

            # Convert English name to Japanese name
            ja_voice_type = self.voice_name_mapping.get(voice_type, "ずんだもん")

            # Generate audio using VOICEVOX Core
            return self._generate_audio_with_core(text, ja_voice_type)

        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return None

    def _generate_audio_with_core(self, text: str, voice_type: str) -> str:
        """
        Generate audio using VOICEVOX Core.

        Args:
            text (str): Text to convert to audio
            voice_type (str): Voice type

        Returns:
            str: Path to the generated audio file
        """
        try:
            # Get style ID for the selected voice
            style_id = self.core_style_ids.get(voice_type, 3)

            # Split text into chunks
            text_chunks = self._split_text(text)
            temp_wav_files = []

            # Process each chunk
            for i, chunk in enumerate(text_chunks):
                # Generate audio data using core
                if self.core_synthesizer is not None:  # Type check for mypy
                    wav_data = self.core_synthesizer.tts(chunk, style_id)

                    # Save to temporary file
                    temp_file = str(self.output_dir / f"chunk_{i}.wav")
                    with open(temp_file, "wb") as f:
                        f.write(wav_data)

                    temp_wav_files.append(temp_file)

            # Combine all chunks to create the final audio file
            output_file = self._create_final_audio_file(temp_wav_files)

            return output_file
        except Exception as e:
            logger.error(f"Audio generation error with VOICEVOX Core: {e}")
            raise

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

        # 最終的な出力ファイル名
        output_file = str(self.output_dir / f"podcast_{uuid.uuid4().hex[:8]}.wav")

        # 単一ファイルならそのまま使用
        if len(temp_wav_files) == 1:
            os.rename(temp_wav_files[0], output_file)
            return output_file

        # 複数ファイルなら結合
        try:
            # ファイルリストを生成
            list_file = str(self.output_dir / f"filelist_{uuid.uuid4()}.txt")
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

        try:
            # Split the podcast text into lines
            lines = podcast_text.strip().split("\n")
            conversation_parts = []

            # すべてのキャラクターをチェック
            character_patterns = {
                "ずんだもん": ["ずんだもん:", "ずんだもん："],
                "四国めたん": ["四国めたん:", "四国めたん："],
                "九州そら": ["九州そら:", "九州そら："],
            }

            # Process each line of the text
            logger.info(f"Processing {len(lines)} lines of text")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # すべてのキャラクターパターンをチェック
                found_character = False
                for character, patterns in character_patterns.items():
                    for pattern in patterns:
                        if line.startswith(pattern):
                            text = line.replace(pattern, "", 1).strip()
                            if text:
                                logger.debug(f"Found {character} line: {text[:30]}...")
                                conversation_parts.append((character, text))
                                found_character = True
                                break
                    if found_character:
                        break

                if not found_character:
                    logger.warning(f"Unrecognized line format: {line[:50]}...")

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
                        temp_file = str(self.output_dir / f"part_{i}_chunk_{j}.wav")
                        with open(temp_file, "wb") as f:
                            f.write(wav_data)
                        chunk_wavs.append(temp_file)
                        logger.debug(f"Saved chunk to {temp_file}")

                # Combine chunks for this part
                if chunk_wavs:
                    if len(chunk_wavs) > 1:
                        part_file = str(self.output_dir / f"part_{i}.wav")
                        self._combine_audio_files(chunk_wavs, part_file)
                        logger.debug(
                            f"Combining {len(chunk_wavs)} chunks into {part_file}"
                        )
                        temp_wav_files.append(part_file)

                        # Clean up chunk files
                        for chunk_wav in chunk_wavs:
                            os.unlink(chunk_wav)
                    else:
                        # Only one chunk, no need to combine
                        logger.debug(f"Using single chunk file: {chunk_wavs[0]}")
                        temp_wav_files.append(chunk_wavs[0])

            # Combine all parts to create the final audio file
            if temp_wav_files:
                logger.info(
                    f"Combining {len(temp_wav_files)} audio parts into final file"
                )
                final_path = self._create_final_audio_file(temp_wav_files)
                logger.info(f"Final audio saved to: {final_path}")
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
        list_file = str(self.output_dir / f"filelist_{uuid.uuid4()}.txt")
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

        # Try to identify speaker blocks in continuous text
        lines = text.split("\n")
        fixed_lines = []

        for line in lines:
            # 複数のキャラクターが一行に存在するかチェック
            fixed_line = line
            for name in character_names:
                if f"。{name}" in fixed_line:
                    parts = fixed_line.split(f"。{name}")
                    if len(parts) > 1:
                        if parts[0].strip():
                            fixed_lines.append(f"{parts[0].strip()}。")
                        fixed_line = f"{name}{parts[1]}"

            fixed_lines.append(fixed_line)

        # Join the fixed lines
        return "\n".join(fixed_lines)
