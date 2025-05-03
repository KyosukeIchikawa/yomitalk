"""Tests for parsing LLM output and generating audio from conversation text.

This module contains tests for the conversation parsing and audio generation functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest import mock

from app.components.audio_generator import AudioGenerator
from app.models.openai_model import OpenAIModel


class TestConversationParser:
    """Test conversation parser functionality."""

    def test_conversation_format_fixing(self):
        """Test the conversation format fixing functionality."""
        audio_gen = AudioGenerator()

        # Test cases for _fix_conversation_format
        test_cases = [
            # Missing colon test
            {
                "input": "ずんだもん こんにちは！\n四国めたん はい、こんにちは！",
                "expected": "ずんだもん: こんにちは！\n四国めたん: はい、こんにちは！",
            },
            # Multiple speakers in one line test
            {
                "input": "ずんだもん: こんにちは！。四国めたん: はい、こんにちは！",
                "expected": "ずんだもん: こんにちは！。\n四国めたん: はい、こんにちは！",
            },
        ]

        for tc in test_cases:
            result = audio_gen._fix_conversation_format(tc["input"])
            assert (
                result.strip() == tc["expected"].strip()
            ), f"Failed to fix: {tc['input']}"

    @mock.patch("app.components.audio_generator.Synthesizer")
    def test_character_conversation_parsing(self, mock_synthesizer):
        """Test that character conversation parsing works correctly."""
        # Setup mock
        mock_instance = mock_synthesizer.return_value
        mock_instance.tts.return_value = b"mock_audio_data"

        # Setup temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output directory
            audio_gen = AudioGenerator()
            audio_gen.output_dir = Path(temp_dir)
            audio_gen.core_initialized = True
            audio_gen.core_synthesizer = mock_instance

            # Test conversation text
            conversation = (
                "ずんだもん: こんにちは！今日も頑張るのだ！\n"
                "四国めたん: はい、今日も論文について解説しますね。\n"
                "ずんだもん: わくわくするのだ！\n"
            )

            # 音声ファイル生成のパッチを追加
            with mock.patch.object(
                audio_gen, "_create_final_audio_file"
            ) as mock_create, mock.patch(
                "os.path.exists", return_value=True
            ), mock.patch(
                "builtins.open", mock.mock_open()
            ), mock.patch(
                "os.makedirs", return_value=None
            ):
                # 音声生成成功を模擬
                mock_output_path = os.path.join(temp_dir, "final_output.wav")
                mock_create.return_value = mock_output_path

                # Run the function
                result = audio_gen.generate_character_conversation(conversation)

                # Verify results
                assert result is not None
                assert result == mock_output_path
                assert mock_create.called

                # Check that synthesizer was called for each line
                assert mock_instance.tts.call_count == 3

                # Verify the correct style IDs were used
                call_args_list = mock_instance.tts.call_args_list
                assert call_args_list[0][0][1] == audio_gen.core_style_ids["ずんだもん"]
                assert call_args_list[1][0][1] == audio_gen.core_style_ids["四国めたん"]
                assert call_args_list[2][0][1] == audio_gen.core_style_ids["ずんだもん"]

    @mock.patch("app.models.openai_model.OpenAIModel.generate_text")
    def test_openai_conversation_format(self, mock_generate_text):
        """Test that the OpenAI model generates correctly formatted conversation."""
        # Setup mock response
        mock_response = (
            "ずんだもん: こんにちは！今日はどんな論文を解説するのだ？\n"
            "四国めたん: 今日は機械学習の最新研究について解説します。\n"
            "ずんだもん: わくわくするのだ！"
        )
        mock_generate_text.return_value = mock_response

        # Create OpenAI model
        model = OpenAIModel()

        # Generate conversation
        result = model.generate_podcast_conversation(
            "This is a test paper about machine learning."
        )

        # Verify result
        assert result == mock_response

        # Split the response into lines and check formatting
        lines = result.split("\n")
        for line in lines:
            assert line.startswith("ずんだもん:") or line.startswith(
                "四国めたん:"
            ), f"Invalid line format: {line}"

    @mock.patch("app.models.openai_model.OpenAIModel.generate_text")
    def test_openai_incorrect_format_handling(self, mock_generate_text):
        """Test that the OpenAI model handles incorrectly formatted conversation."""
        # Setup mock response with incorrect format
        mock_response = (
            "ずんだもん こんにちは！今日はどんな論文を解説するのだ？\n"
            "四国めたん 今日は機械学習の最新研究について解説します。\n"
            "ずんだもん わくわくするのだ！"
        )
        mock_generate_text.return_value = mock_response

        # Create OpenAI model
        model = OpenAIModel()

        # Generate conversation
        result = model.generate_podcast_conversation(
            "This is a test paper about machine learning."
        )

        # Verify result has been fixed
        lines = result.split("\n")
        for line in lines:
            assert line.startswith("ずんだもん:") or line.startswith(
                "四国めたん:"
            ), f"Line not fixed: {line}"
