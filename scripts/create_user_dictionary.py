#!/usr/bin/env python3
"""
VOICEVOX user dictionary creation script.
Creates and saves a user dictionary with custom word pronunciations.
"""

import sys
from pathlib import Path

# Add the project root to sys.path to import yomitalk modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from voicevox_core import UserDictWord  # type: ignore  # noqa: E402
from voicevox_core.blocking import UserDict  # type: ignore  # noqa: E402
from yomitalk.utils.logger import logger  # noqa: E402


def create_user_dictionary():
    """Create a user dictionary with custom word pronunciations."""

    # VOICEVOX Core paths (matching audio_generator.py)
    VOICEVOX_BASE_PATH = Path("voicevox_core/voicevox_core")
    VOICEVOX_DICT_PATH = VOICEVOX_BASE_PATH / "dict/open_jtalk_dic_utf_8-1.11"

    # Check if dictionary path exists
    if not VOICEVOX_DICT_PATH.exists():
        logger.error(f"VOICEVOX dictionary path not found: {VOICEVOX_DICT_PATH}")
        logger.error("Please run 'make download-voicevox-core' to set up VOICEVOX.")
        return False

    try:
        # Create user dictionary
        logger.info("Creating user dictionary...")
        user_dict = UserDict()

        # Dictionary entries to add
        # Format: (surface, pronunciation, accent_type, word_type, priority)
        entries = [
            ("RAG", "ラグ", 1, "PROPER_NOUN", 8),
            ("yomitalk", "ヨミトーク", 3, "PROPER_NOUN", 8),
            ("Claude", "クロード", 2, "PROPER_NOUN", 8),
            ("AI", "エーアイ", 1, "COMMON_NOUN", 7),
            ("API", "エーピーアイ", 1, "COMMON_NOUN", 7),
            ("NVIDIA", "エヌビディア", 4, "PROPER_NOUN", 8),
            ("GITHUB", "ギットハブ", 3, "PROPER_NOUN", 8),
            ("GAFA", "ガーファ", 2, "PROPER_NOUN", 8),
            ("速度場", "ソクドバ", 3, "COMMON_NOUN", 7),
            ("DAPO", "ディーエーピーオー", 7, "PROPER_NOUN", 8),
            ("LiDAR", "ライダー", 3, "PROPER_NOUN", 8),
            ("方", "カタ", 1, "COMMON_NOUN", 7),
        ]

        # Add words to dictionary
        logger.info("Adding dictionary entries...")
        for surface, pronunciation, accent_type, word_type, priority in entries:
            try:
                user_dict_word = UserDictWord(
                    surface=surface,
                    pronunciation=pronunciation,
                    accent_type=accent_type,
                    word_type=word_type,  # type: ignore
                    priority=priority,
                )
                word_uuid = user_dict.add_word(user_dict_word)
                logger.info(f"Added: '{surface}' -> '{pronunciation}' (accent: {accent_type}, type: {word_type}, priority: {priority}) UUID: {word_uuid}")
            except Exception as e:
                logger.error(f"Failed to add word '{surface}': {e}")

        # Create assets/dictionaries directory if it doesn't exist
        dict_dir = Path("assets/dictionaries")
        dict_dir.mkdir(parents=True, exist_ok=True)

        # Save user dictionary
        dict_file_path = dict_dir / "user_dictionary.json"
        logger.info(f"Saving user dictionary to: {dict_file_path}")

        user_dict.save(str(dict_file_path))

        logger.info(f"User dictionary saved successfully to {dict_file_path}")
        logger.info(f"Dictionary contains {len(entries)} entries")

        return True

    except Exception as e:
        logger.error(f"Error creating user dictionary: {e}")
        return False


if __name__ == "__main__":
    logger.info("VOICEVOX User Dictionary Creator")
    logger.info("=" * 40)

    success = create_user_dictionary()

    if success:
        logger.info("✅ User dictionary created successfully!")
        logger.info("The dictionary file is saved in assets/dictionaries/user_dictionary.json")
    else:
        logger.error("❌ Failed to create user dictionary")
        sys.exit(1)
