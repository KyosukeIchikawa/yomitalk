"""Module providing audio generation functionality.

Provides functionality for generating audio from text using VOICEVOX Core.
"""

import os
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional

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
    print(f"VOICEVOX import error: {e}")
    print("VOICEVOX Core installation is required for audio generation.")
    print("Run 'make download-voicevox-core' to set up VOICEVOX.")
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
                print("VOICEVOX models or dictionary not found")
                return

            # Initialize OpenJTalk and ONNX Runtime
            try:
                # Initialize OpenJtalk with dictionary
                open_jtalk = OpenJtalk(str(self.VOICEVOX_DICT_PATH))

                # Load ONNX Runtime without specifying a file path
                # This will use the ONNX runtime that comes with the voicevox-core
                # package
                runtime_path = str(
                    self.VOICEVOX_LIB_PATH / "libvoicevox_onnxruntime.so.1.17.3"
                )
                if os.path.exists(runtime_path):
                    ort = Onnxruntime.load_once(filename=runtime_path)
                else:
                    # Fallback to default loader
                    ort = Onnxruntime.load_once()

                # Initialize the synthesizer
                self.core_synthesizer = Synthesizer(ort, open_jtalk)

                # Load voice models
                for model_file in self.VOICEVOX_MODELS_PATH.glob("*.vvm"):
                    if self.core_synthesizer is not None:  # Type check for mypy
                        with VoiceModelFile.open(str(model_file)) as model:
                            self.core_synthesizer.load_voice_model(model)

                self.core_initialized = True
                print("VOICEVOX Core initialization completed")
            except Exception as e:
                print(f"Failed to load ONNX runtime: {e}")
                raise
        except Exception as e:
            print(f"Failed to initialize VOICEVOX Core: {e}")
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
                print(error_message)
                return None

            # Convert English name to Japanese name
            ja_voice_type = self.voice_name_mapping.get(voice_type, "ずんだもん")

            # Generate audio using VOICEVOX Core
            return self._generate_audio_with_core(text, ja_voice_type)

        except Exception as e:
            print(f"Audio generation error: {e}")
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
            print(f"Audio generation error with VOICEVOX Core: {e}")
            raise

    def _create_final_audio_file(self, temp_wav_files: List[str]) -> str:
        """
        Create the final audio file by combining temporary audio files.

        Args:
            temp_wav_files (list): List of temporary WAV file paths

        Returns:
            str: Path to the final audio file
        """
        output_file = str(self.output_dir / f"podcast_{uuid.uuid4()}.wav")

        if len(temp_wav_files) == 1:
            # If there's only one file, simply rename it
            os.rename(temp_wav_files[0], output_file)
        else:
            # If there are multiple files, concatenate with FFmpeg
            # Create file list
            list_file = str(self.output_dir / "filelist.txt")
            with open(list_file, "w") as f:
                for file in temp_wav_files:
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

            # Delete list file
            os.remove(list_file)

            # Delete temporary files
            for temp_file in temp_wav_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        return output_file

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
        Generate audio for a conversation between Zundamon and Shikoku Metan.

        Args:
            podcast_text (str): Podcast text in conversation format with speaker prefixes

        Returns:
            Optional[str]: Path to the generated audio file
        """
        if not VOICEVOX_CORE_AVAILABLE or not self.core_initialized:
            print("VOICEVOX Core is not available or not properly initialized.")
            return None

        if not podcast_text or podcast_text.strip() == "":
            print("Podcast text is empty")
            return None

        try:
            # Parse the conversation text into lines with speaker identification
            conversation_parts = []
            temp_wav_files = []

            # Process each line to identify the speaker and text
            lines = podcast_text.split("\n")
            print(f"Processing {len(lines)} lines of text")

            import re

            zundamon_pattern = re.compile(r"^(ずんだもん|ずんだもん:|ずんだもん：)\s*(.+)$")
            metan_pattern = re.compile(r"^(四国めたん|四国めたん:|四国めたん：)\s*(.+)$")

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Check if line starts with a speaker name using regex
                zundamon_match = zundamon_pattern.match(line)
                metan_match = metan_pattern.match(line)

                if zundamon_match:
                    speaker = "ずんだもん"
                    text = zundamon_match.group(2).strip()
                    conversation_parts.append({"speaker": speaker, "text": text})
                    print(f"Found Zundamon line: {text[:30]}...")
                elif metan_match:
                    speaker = "四国めたん"
                    text = metan_match.group(2).strip()
                    conversation_parts.append({"speaker": speaker, "text": text})
                    print(f"Found Shikoku Metan line: {text[:30]}...")
                else:
                    print(f"Unrecognized line format: {line[:50]}...")

            print(f"Identified {len(conversation_parts)} conversation parts")

            # If no valid conversation parts found, try to reformat the text
            if not conversation_parts and podcast_text.strip():
                print("No valid conversation parts found. Attempting to reformat...")
                # Try to handle potential formatting issues
                fixed_text = self._fix_conversation_format(podcast_text)
                if fixed_text != podcast_text:
                    # Recursive call with fixed text
                    return self.generate_character_conversation(fixed_text)

            if not conversation_parts:
                print("Could not parse any valid conversation parts")
                return None

            # Generate audio for each conversation part
            for i, part in enumerate(conversation_parts):
                speaker = part["speaker"]
                text = part["text"]

                # Get the style ID for the current speaker
                style_id = self.core_style_ids.get(
                    speaker, 3
                )  # Default to Zundamon if unknown
                print(f"Generating audio for {speaker} (style_id: {style_id})")

                # Generate audio
                if self.core_synthesizer is not None:  # Type check for mypy
                    # Split text into manageable chunks if needed
                    text_chunks = self._split_text(text)
                    print(f"Split into {len(text_chunks)} chunks")

                    # Generate audio for each chunk
                    chunk_wavs = []
                    for j, chunk in enumerate(text_chunks):
                        print(
                            f"Processing chunk {j+1}/{len(text_chunks)}: {chunk[:20]}..."
                        )
                        wav_data = self.core_synthesizer.tts(chunk, style_id)

                        # Save to temporary file
                        temp_file = str(self.output_dir / f"part_{i}_chunk_{j}.wav")
                        with open(temp_file, "wb") as f:
                            f.write(wav_data)

                        print(f"Saved chunk to {temp_file}")
                        chunk_wavs.append(temp_file)

                    # Combine chunks for this part if needed
                    if len(chunk_wavs) > 1:
                        part_file = str(self.output_dir / f"part_{i}.wav")
                        print(f"Combining {len(chunk_wavs)} chunks into {part_file}")
                        self._combine_audio_files(chunk_wavs, part_file)
                        temp_wav_files.append(part_file)

                        # Delete chunk files
                        for chunk_file in chunk_wavs:
                            if os.path.exists(chunk_file):
                                os.remove(chunk_file)
                    elif len(chunk_wavs) == 1:
                        print(f"Using single chunk file: {chunk_wavs[0]}")
                        temp_wav_files.append(chunk_wavs[0])

            # Combine all parts to create the final audio file
            if temp_wav_files:
                print(f"Combining {len(temp_wav_files)} audio parts into final file")
                output_file = self._create_final_audio_file(temp_wav_files)
                print(f"Final audio saved to: {output_file}")
                return output_file
            else:
                print("No audio parts were generated")

            return None

        except Exception as e:
            print(f"Character conversation audio generation error: {e}")
            import traceback

            traceback.print_exc()
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

        # Fix missing colon after speaker names
        text = re.sub(r"(ずんだもん)(\s+)(?=[^\s:])", r"ずんだもん:\2", text)
        text = re.sub(r"(四国めたん)(\s+)(?=[^\s:])", r"四国めたん:\2", text)

        # Try to identify speaker blocks in continuous text
        lines = text.split("\n")
        fixed_lines = []

        for line in lines:
            # Check for multiple speakers in one line
            if "。ずんだもん" in line:
                parts = line.split("。ずんだもん")
                if parts[0]:
                    fixed_lines.append(f"{parts[0]}。")
                if len(parts) > 1:
                    fixed_lines.append(f"ずんだもん{parts[1]}")
            elif "。四国めたん" in line:
                parts = line.split("。四国めたん")
                if parts[0]:
                    fixed_lines.append(f"{parts[0]}。")
                if len(parts) > 1:
                    fixed_lines.append(f"四国めたん{parts[1]}")
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)
