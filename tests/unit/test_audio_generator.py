#!/usr/bin/env python3
"""Test script for audio generation functionality."""

import os
import re

import pytest

from app.components.audio_generator import AudioGenerator


@pytest.fixture
def test_conversation():
    """Fixture providing a test conversation string."""
    return """
ずんだもん: こんにちは！今日はどんな論文について話すのだ？
四国めたん: 今日は深層学習による自然言語処理の最新研究について解説します。
ずんだもん: わお！それって難しそうなのだ。私には理解できるのかな？
四国めたん: 大丈夫ですよ。順を追って説明しますね。まずは基本的な概念から。
ずんだもん: うん！頑張って聞くのだ！
"""


@pytest.fixture
def audio_generator():
    """Fixture providing an AudioGenerator instance."""
    return AudioGenerator()


def test_conversation_parsing(test_conversation, audio_generator):
    """Test that a conversation can be parsed correctly."""
    # Skip test if VOICEVOX is not initialized
    if not audio_generator.core_initialized:
        pytest.skip(
            "VOICEVOX Core is not initialized. Run 'make download-voicevox-core' to set up VOICEVOX."
        )

    # Parse conversation
    lines = test_conversation.strip().split("\n")
    parsed_lines = []

    # Create the same patterns used in AudioGenerator
    zundamon_pattern = re.compile(r"^(ずんだもん|ずんだもん:|ずんだもん：)\s*(.+)$")
    metan_pattern = re.compile(r"^(四国めたん|四国めたん:|四国めたん：)\s*(.+)$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        zundamon_match = zundamon_pattern.match(line)
        metan_match = metan_pattern.match(line)

        if zundamon_match:
            parsed_lines.append(("ずんだもん", zundamon_match.group(2)))
        elif metan_match:
            parsed_lines.append(("四国めたん", metan_match.group(2)))

    # Verify parsing results
    assert len(parsed_lines) > 0, "No conversation lines were parsed"
    assert any(
        speaker == "ずんだもん" for speaker, _ in parsed_lines
    ), "ずんだもん lines not found"
    assert any(
        speaker == "四国めたん" for speaker, _ in parsed_lines
    ), "四国めたん lines not found"


def test_audio_generation(test_conversation, audio_generator):
    """Test that an audio file can be generated from a conversation."""
    # Skip test if VOICEVOX is not initialized
    if not audio_generator.core_initialized:
        pytest.skip(
            "VOICEVOX Core is not initialized. Run 'make download-voicevox-core' to set up VOICEVOX."
        )

    # Generate audio from conversation
    output_path = audio_generator.generate_character_conversation(test_conversation)

    # Assert that output was generated
    assert output_path is not None
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

    # Clean up the generated file
    if os.path.exists(output_path):
        os.remove(output_path)
