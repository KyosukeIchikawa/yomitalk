#!/usr/bin/env python3

"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""

import math
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from yomitalk.common import APIType
from yomitalk.common.character import DISPLAY_NAMES
from yomitalk.components.audio_generator import (
    initialize_global_voicevox_manager,
)
from yomitalk.components.content_extractor import ContentExtractor
from yomitalk.models.gemini_model import GeminiModel
from yomitalk.models.openai_model import OpenAIModel
from yomitalk.prompt_manager import DocumentType, PodcastMode, PromptManager
from yomitalk.user_session import UserSession
from yomitalk.utils.logger import logger

# Initialize global VOICEVOX Core manager once for all users
# This is done at application startup, outside of any function
logger.info("Initializing global VOICEVOX Core manager for all users")
global_voicevox_manager = initialize_global_voicevox_manager()

# E2E test mode for faster startup
E2E_TEST_MODE = os.environ.get("E2E_TEST_MODE", "false").lower() == "true"

# Default port
DEFAULT_PORT = 7860


# Application class
class PaperPodcastApp:
    """Main class for the Paper Podcast Generator application."""

    def __init__(self):
        """Initialize the PaperPodcastApp."""
        logger.info("Initializing PaperPodcastApp for multi-user support")

        # Cleanup old sessions on startup using dummy session instance
        dummy_session = UserSession("dummy")
        dummy_session.cleanup_old_sessions()

    def create_user_session(self, request: gr.Request) -> UserSession:
        """Create a new user session with unique session ID or restore from saved state."""
        session_id = request.session_hash

        # Try to load existing session state first
        existing_session = UserSession.load_from_file(session_id)
        if existing_session:
            logger.info(f"Restored existing session: {session_id}")
            return existing_session

        # Create new session if no saved state found
        logger.info(f"Created new session: {session_id}")
        new_session = UserSession(session_id)
        new_session.auto_save()  # Save initial state
        return new_session

    def create_user_session_with_browser_state(self, request: gr.Request, browser_state: Dict[str, Any]) -> Tuple[UserSession, Dict[str, Any]]:
        """Create user session with simplified BrowserState-based session management."""

        # Check if we have an existing app session ID from browser state
        stored_app_session_id = browser_state.get("app_session_id", "") if browser_state else ""

        if stored_app_session_id:
            # Use existing app session ID - no need to copy files since it's persistent
            logger.info(f"Using existing app session ID: {stored_app_session_id}")
            user_session = UserSession(stored_app_session_id)

            # Restore settings from browser state
            user_session.update_settings_from_browser_state(browser_state)

            # Return browser state as-is since it contains all needed state
            return user_session, browser_state
        else:
            # Create new session with UUID-based ID
            logger.info("Creating new app session with UUID")
            user_session = UserSession()  # Will generate new UUID

            # Initialize browser state with new session ID
            browser_state["app_session_id"] = user_session.session_id

            # Sync current settings to browser state
            browser_state = user_session.sync_settings_to_browser_state(browser_state)

            return user_session, browser_state

    def update_browser_state_audio_status(self, user_session: UserSession, browser_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update BrowserState with current audio generation status."""
        if user_session is None:
            return browser_state.copy()

        audio_status = user_session.get_audio_generation_status(browser_state)

        # Create a copy of browser state and update audio generation section
        updated_state = browser_state.copy()
        updated_state["audio_generation_state"] = browser_state["audio_generation_state"].copy()
        updated_state["audio_generation_state"].update(audio_status)

        return updated_state

    def update_browser_state_ui_content(self, browser_state: Dict[str, Any], podcast_text: str, terms_agreed: bool, extracted_text: str = "") -> Dict[str, Any]:
        """Update BrowserState with UI content for recovery."""
        updated_state = browser_state.copy()

        # Update ui_state section in the new BrowserState structure
        if "ui_state" not in updated_state:
            updated_state["ui_state"] = {}

        updated_state["ui_state"].update(
            {
                "podcast_text": podcast_text or "",
                "terms_agreed": bool(terms_agreed),
                "extracted_text": extracted_text or "",
            }
        )

        return updated_state

    def extract_url_text_with_debug(self, url: str, existing_text: str, add_separator: bool, user_session: UserSession) -> Tuple[str, UserSession]:
        """Debug wrapper for URL text extraction."""
        logger.info(
            f"[DEBUG] extract_url_text_with_debug called - URL: {url}, "
            f"existing_text_len: {len(existing_text) if existing_text else 0}, "
            f"add_separator: {add_separator}, "
            f"user_session: {user_session.session_id if user_session else 'None'}"
        )

        try:
            result_text, result_session = self.extract_url_text(url, existing_text, add_separator, user_session)
            logger.info(f"[DEBUG] extract_url_text result - text_len: {len(result_text) if result_text else 0}, session: {result_session.session_id if result_session else 'None'}")
            return result_text, result_session
        except Exception as e:
            logger.error(f"[DEBUG] extract_url_text exception: {str(e)}")
            raise

    def extract_url_text_with_debug_and_browser_state(
        self, url: str, existing_text: str, add_separator: bool, user_session: UserSession, browser_state: Dict[str, Any]
    ) -> Tuple[str, UserSession, Dict[str, Any]]:
        """Debug wrapper for URL text extraction with browser state update."""
        result_text, result_session = self.extract_url_text_with_debug(url, existing_text, add_separator, user_session)

        # Update browser state with extracted text
        updated_browser_state = self.update_browser_state_ui_content(browser_state, "", False, result_text)

        return result_text, result_session, updated_browser_state

    def generate_podcast_audio_streaming_with_browser_state(self, text: str, user_session: UserSession, browser_state: Dict[str, Any], progress=None):
        """Generate streaming audio with BrowserState synchronization for network recovery."""
        if not text:
            logger.warning("Streaming audio generation: Text is empty")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            error_html = self._create_error_html("テキストが空のため音声生成できません")
            yield None, user_session, error_html, None, browser_state
            return

        # Check if VOICEVOX Core is available
        if not user_session.audio_generator.core_initialized:
            logger.error("Streaming audio generation: VOICEVOX Core is not available")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            error_html = self._create_error_html("VOICEVOX Coreが利用できません")
            yield None, user_session, error_html, None, browser_state
            return

        try:
            # Initialize progress if not provided
            if progress is None:
                progress = gr.Progress()

            # スクリプトからパーツ数を推定
            estimated_total_parts = self._estimate_audio_parts_count(text)
            logger.info(f"Estimated total audio parts: {estimated_total_parts}")

            # 音声生成状態をブラウザ状態に初期化
            generation_id = str(uuid.uuid4())
            browser_state["audio_generation_state"].update(
                {
                    "is_generating": True,
                    "status": "generating",
                    "current_script": text,
                    "generation_id": generation_id,
                    "start_time": time.time(),
                    "progress": 0.0,
                    "generated_parts": [],
                    "streaming_parts": [],
                    "final_audio_path": None,
                    "estimated_total_parts": estimated_total_parts,
                }
            )

            # 初回のyieldを行って、Gradioのストリーミングモードを確実に有効化
            logger.debug(f"Initializing streaming audio generation (ID: {generation_id})")
            start_html = self._create_progress_html(
                0,
                estimated_total_parts,
                "音声生成を開始しています...",
                start_time=time.time(),
            )
            yield None, user_session, start_html, None, browser_state

            # gr.Progressも使用（Gradio標準の進捗バー）
            progress(0, desc="🎤 音声生成を開始しています...")

            # ストリーミング用の各パートのパスを保存
            parts_paths = []
            final_combined_path = None
            current_part_count = 0  # ローカルカウンターを使用

            # 個別の音声パートを生成・ストリーミング
            for audio_path in user_session.audio_generator.generate_character_conversation(text, 0, []):
                if not audio_path:
                    continue

                filename = os.path.basename(audio_path)

                # 'part_'を含むものは部分音声ファイル、'audio_'から始まるものは最終結合ファイル
                if "part_" in filename:
                    parts_paths.append(audio_path)
                    current_part_count += 1  # ローカルカウンターをインクリメント
                    progress_ratio = min(0.95, current_part_count / estimated_total_parts)

                    # 進捗状況をログに記録
                    logger.info(f"Audio part {current_part_count}/{estimated_total_parts} completed")

                    logger.debug(f"ストリーム音声パーツ ({current_part_count}/{estimated_total_parts}): {audio_path}")

                    # ブラウザ状態にストリーミングパーツを追加
                    browser_state["audio_generation_state"]["streaming_parts"].append(audio_path)
                    browser_state["audio_generation_state"]["progress"] = progress_ratio

                    # 進捗情報を生成してyield（新しい詳細進捗表示）
                    start_time = browser_state["audio_generation_state"]["start_time"]

                    # パートが完了した場合の適切なメッセージ
                    if current_part_count < estimated_total_parts:
                        status_message = f"音声パート {current_part_count} が完了..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了..."
                    else:
                        status_message = f"音声パート {current_part_count} が完了、最終処理中..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了、最終処理中..."

                    progress_html = self._create_progress_html(
                        current_part_count,
                        estimated_total_parts,
                        status_message,
                        start_time=start_time,
                    )

                    # gr.Progressも更新
                    progress(
                        progress_ratio,
                        desc=progress_desc,
                    )

                    yield (
                        audio_path,
                        user_session,
                        progress_html,
                        None,
                        browser_state,
                    )  # ストリーミング再生用にyield
                    time.sleep(0.05)  # 連続再生のタイミング調整
                elif filename.startswith("audio_"):
                    # 最終結合ファイルの場合
                    final_combined_path = audio_path
                    browser_state["audio_generation_state"]["final_audio_path"] = audio_path
                    browser_state["audio_generation_state"]["progress"] = 1.0
                    logger.info(f"結合済み最終音声ファイルを受信: {final_combined_path}")

                    # 最終音声完成の進捗を表示
                    start_time = browser_state["audio_generation_state"]["start_time"]
                    complete_html = self._create_progress_html(
                        estimated_total_parts,
                        estimated_total_parts,
                        "音声生成完了！",
                        is_completed=True,
                        start_time=start_time,
                    )

                    # gr.Progressも完了状態に
                    progress(1.0, desc="✅ 音声生成完了！")

                    yield None, user_session, complete_html, final_combined_path, browser_state

            # 音声生成の完了処理
            self._finalize_audio_generation_with_browser_state(final_combined_path, parts_paths, user_session, browser_state)

        except Exception as e:
            logger.error(f"Streaming audio generation exception: {str(e)}")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            browser_state["audio_generation_state"]["progress"] = 0.0
            error_html = self._create_error_html(f"音声生成でエラーが発生しました: {str(e)}")
            progress(0, desc="❌ 音声生成エラー")
            yield None, user_session, error_html, None, browser_state

    def generate_podcast_audio_streaming_with_browser_state_and_resume(
        self, text: str, user_session: UserSession, browser_state: Dict[str, Any], resume_from_part: int = 0, existing_parts: Optional[List[str]] = None, progress=None
    ):
        """Generate streaming audio with BrowserState synchronization and true resume capability."""
        if not text:
            logger.warning("Streaming audio generation: Text is empty")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            error_html = self._create_error_html("テキストが空のため音声生成できません")
            yield None, user_session, error_html, None, browser_state
            return

        # Check if VOICEVOX Core is available
        if not user_session.audio_generator.core_initialized:
            logger.error("Streaming audio generation: VOICEVOX Core is not available")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            error_html = self._create_error_html("VOICEVOX Coreが利用できません")
            yield None, user_session, error_html, None, browser_state
            return

        try:
            # Initialize progress if not provided
            if progress is None:
                progress = gr.Progress()

            # スクリプトからパーツ数を推定
            estimated_total_parts = self._estimate_audio_parts_count(text)
            logger.info(f"Estimated total audio parts: {estimated_total_parts}")

            # 音声生成状態をブラウザ状態に初期化（再開の場合は一部保持）
            generation_id = str(uuid.uuid4())
            if resume_from_part == 0:
                # 新規生成の場合
                browser_state["audio_generation_state"].update(
                    {
                        "is_generating": True,
                        "status": "generating",
                        "current_script": text,
                        "generation_id": generation_id,
                        "start_time": time.time(),
                        "progress": 0.0,
                        "generated_parts": [],
                        "streaming_parts": [],
                        "final_audio_path": None,
                        "estimated_total_parts": estimated_total_parts,
                    }
                )
            else:
                # 再開の場合、必要な状態のみ更新
                browser_state["audio_generation_state"].update(
                    {
                        "is_generating": True,
                        "status": "generating",
                        "generation_id": generation_id,
                    }
                )

            # 初回のyieldを行って、Gradioのストリーミングモードを確実に有効化
            logger.debug(f"Initializing streaming audio generation (ID: {generation_id}, resume_from_part: {resume_from_part})")
            if resume_from_part == 0:
                start_html = self._create_progress_html(
                    0,
                    estimated_total_parts,
                    "音声生成を開始しています...",
                    start_time=time.time(),
                )
                yield None, user_session, start_html, None, browser_state
            else:
                resume_html = self._create_progress_html(
                    resume_from_part,
                    estimated_total_parts,
                    f"音声生成を再開しています... (パート{resume_from_part + 1}から)",
                    start_time=browser_state["audio_generation_state"].get("start_time", time.time()),
                    resume_from_part=resume_from_part,
                )
                yield None, user_session, resume_html, None, browser_state

            # gr.Progressも使用（Gradio標準の進捗バー）
            if resume_from_part == 0:
                progress(0, desc="🎤 音声生成を開始しています...")
            else:
                progress(resume_from_part / estimated_total_parts, desc=f"🔄 音声生成を再開中... (パート{resume_from_part + 1}から)")

            # ストリーミング用の各パートのパスを保存
            parts_paths = existing_parts.copy() if existing_parts else []
            final_combined_path = None
            current_part_count = 0  # 常に0から開始

            # 真の部分再開対応の音声生成
            for audio_path in user_session.audio_generator.generate_character_conversation(text, resume_from_part, existing_parts):
                if not audio_path:
                    continue

                filename = os.path.basename(audio_path)

                # 'part_'を含むものは部分音声ファイル、'audio_'から始まるものは最終結合ファイル
                if "part_" in filename:
                    # 既存パートかどうかをチェック
                    is_existing_part = audio_path in (existing_parts or [])

                    # パートカウンターを常にインクリメント
                    current_part_count += 1

                    if not is_existing_part:
                        # 新しく生成されたパート
                        parts_paths.append(audio_path)

                        # ブラウザ状態にストリーミングパーツを追加
                        browser_state["audio_generation_state"]["streaming_parts"].append(audio_path)

                        logger.info(f"New audio part {current_part_count}/{estimated_total_parts} completed")
                    else:
                        # 既存パートの復元（既にparts_pathsにある）
                        logger.info(f"Restored existing audio part {current_part_count}: {audio_path}")

                    progress_ratio = min(0.95, current_part_count / estimated_total_parts)
                    browser_state["audio_generation_state"]["progress"] = progress_ratio

                    # 進捗情報を生成してyield
                    start_time = browser_state["audio_generation_state"]["start_time"]

                    if is_existing_part:
                        status_message = f"音声パート {current_part_count} を復元..."
                        progress_desc = f"🔄 音声パート {current_part_count}/{estimated_total_parts} 復元..."
                    elif current_part_count < estimated_total_parts:
                        status_message = f"音声パート {current_part_count} が完了..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了..."
                    else:
                        status_message = f"音声パート {current_part_count} が完了、最終処理中..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了、最終処理中..."

                    progress_html = self._create_progress_html(
                        current_part_count,
                        estimated_total_parts,
                        status_message,
                        start_time=start_time,
                        resume_from_part=resume_from_part if resume_from_part > 0 else None,
                    )

                    # gr.Progressも更新
                    progress(
                        progress_ratio,
                        desc=progress_desc,
                    )

                    yield (
                        audio_path,
                        user_session,
                        progress_html,
                        None,
                        browser_state,
                    )
                    time.sleep(0.05)
                elif filename.startswith("audio_"):
                    # 最終結合ファイルの場合
                    final_combined_path = audio_path
                    browser_state["audio_generation_state"]["final_audio_path"] = audio_path
                    browser_state["audio_generation_state"]["progress"] = 1.0
                    logger.info(f"結合済み最終音声ファイルを受信: {final_combined_path}")

                    # 最終音声完成の進捗を表示
                    start_time = browser_state["audio_generation_state"]["start_time"]
                    complete_html = self._create_progress_html(
                        estimated_total_parts,
                        estimated_total_parts,
                        "音声生成完了！",
                        is_completed=True,
                        start_time=start_time,
                    )

                    # gr.Progressも完了状態に
                    progress(1.0, desc="✅ 音声生成完了！")

                    yield None, user_session, complete_html, final_combined_path, browser_state

            # 音声生成の完了処理
            self._finalize_audio_generation_with_browser_state(final_combined_path, parts_paths, user_session, browser_state)

        except Exception as e:
            logger.error(f"Streaming audio generation exception: {str(e)}")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            browser_state["audio_generation_state"]["progress"] = 0.0
            error_html = self._create_error_html(f"音声生成でエラーが発生しました: {str(e)}")
            progress(0, desc="❌ 音声生成エラー")
            yield None, user_session, error_html, None, browser_state

    def _finalize_audio_generation_with_browser_state(self, final_combined_path, parts_paths, user_session: UserSession, browser_state: Dict[str, Any]):
        """
        音声生成の最終処理をブラウザ状態と同期して行う

        Args:
            final_combined_path (str): 結合された最終音声ファイルのパス
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
            user_session (UserSession): ユーザーセッションインスタンス
            browser_state (Dict[str, Any]): ブラウザ状態

        Returns:
            str: 最終的な音声ファイルの情報、またはNone
        """
        # 最終結合ファイルのパスが取得できた場合
        if final_combined_path and os.path.exists(final_combined_path):
            # 進捗を更新
            browser_state["audio_generation_state"]["progress"] = 0.9
            logger.info(f"最終結合音声ファイル: {final_combined_path}")

            # 最終的な音声ファイルのパスを保存
            user_session.audio_generator.final_audio_path = final_combined_path

            # ファイルの書き込みを確実にするため少し待機
            time.sleep(0.2)

            if os.path.exists(final_combined_path):
                filesize = os.path.getsize(final_combined_path)
                # 進捗を完了状態に更新
                browser_state["audio_generation_state"]["progress"] = 1.0
                browser_state["audio_generation_state"]["status"] = "completed"
                browser_state["audio_generation_state"]["is_generating"] = False
                browser_state["audio_generation_state"]["final_audio_path"] = final_combined_path
                logger.info(f"音声生成完了: {final_combined_path} (ファイルサイズ: {filesize} bytes)")
                return final_combined_path  # 最終的な音声ファイルパスを返す
            else:
                logger.error(f"ファイルが存在しなくなりました: {final_combined_path}")
                return self._use_fallback_audio_with_browser_state(parts_paths, user_session, browser_state)

        # 最終結合ファイルがない場合はフォールバック処理
        else:
            return self._use_fallback_audio_with_browser_state(parts_paths, user_session, browser_state)

    def _use_fallback_audio_with_browser_state(self, parts_paths, user_session: UserSession, browser_state: Dict[str, Any]):
        """
        結合ファイルが取得できない場合のフォールバック処理（ブラウザ状態対応）

        Args:
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
            user_session (UserSession): ユーザーセッションインスタンス
            browser_state (Dict[str, Any]): ブラウザ状態

        Returns:
            str: フォールバックで使用する音声ファイルパス、またはNone
        """
        # 部分音声ファイルがある場合は最後のパートを使用
        if parts_paths:
            logger.warning("結合音声ファイルを取得できなかったため、最後のパートを使用します")
            user_session.audio_generator.final_audio_path = parts_paths[-1]
            user_session.audio_generator.audio_generation_progress = 1.0
            browser_state["audio_generation_state"]["status"] = "completed"
            browser_state["audio_generation_state"]["is_generating"] = False
            browser_state["audio_generation_state"]["progress"] = 1.0
            browser_state["audio_generation_state"]["final_audio_path"] = parts_paths[-1]

            if os.path.exists(parts_paths[-1]):
                filesize = os.path.getsize(parts_paths[-1])
                logger.info(f"部分音声ファイル使用: {parts_paths[-1]} (ファイルサイズ: {filesize} bytes)")
                return parts_paths[-1]  # フォールバック音声ファイルパスを返す
            else:
                logger.error(f"フォールバックファイルも存在しません: {parts_paths[-1]}")
                browser_state["audio_generation_state"]["status"] = "failed"
                browser_state["audio_generation_state"]["is_generating"] = False
                browser_state["audio_generation_state"]["progress"] = 0.0
        else:
            logger.warning("音声ファイルが生成されませんでした")
            browser_state["audio_generation_state"]["status"] = "failed"
            browser_state["audio_generation_state"]["is_generating"] = False
            browser_state["audio_generation_state"]["progress"] = 0.0
        return None  # エラー時はNoneを返す

    def restore_streaming_audio_from_browser_state(self, browser_state: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """Restore streaming audio playback from browser state after page reload."""
        audio_state = browser_state.get("audio_generation_state", {})
        streaming_parts = audio_state.get("streaming_parts", [])
        final_audio_path = audio_state.get("final_audio_path")

        # Check if we have a session ID to look for existing part files on disk
        session_id = browser_state.get("app_session_id")
        existing_parts_on_disk = []
        if session_id:
            from yomitalk.user_session import UserSession

            temp_session = UserSession(session_id)
            temp_dir = temp_session.get_temp_dir()
            talks_dir = temp_dir / "talks"
            if talks_dir.exists():
                for stream_dir in talks_dir.iterdir():
                    if stream_dir.is_dir() and stream_dir.name.startswith("stream_"):
                        for part_file in stream_dir.glob("part_*.wav"):
                            if part_file.exists():
                                existing_parts_on_disk.append(str(part_file))

        # If there's a final audio file, return that for immediate playback
        if final_audio_path and os.path.exists(final_audio_path):
            estimated_total_parts = audio_state.get("estimated_total_parts", len(streaming_parts))
            progress_html = self._create_progress_html(estimated_total_parts, estimated_total_parts, "音声生成完了！ (復元済み)", is_completed=True, start_time=audio_state.get("start_time"))
            logger.info(f"Restored final audio from browser state: {final_audio_path}")
            return final_audio_path, progress_html

        # If there are streaming parts but no final audio, show the latest part
        all_parts = streaming_parts + existing_parts_on_disk
        if all_parts:
            # Find the most recent valid audio file
            latest_audio = None
            for audio_path in reversed(all_parts):
                if audio_path and os.path.exists(audio_path):
                    latest_audio = audio_path
                    break

            if latest_audio:
                # Calculate resumable part information
                # Use the total count of unique existing parts
                unique_parts = list(set(all_parts))
                current_parts = len([p for p in unique_parts if p and os.path.exists(p)])
                estimated_total_parts = audio_state.get("estimated_total_parts", current_parts)
                resume_from_part = current_parts  # Next part to generate

                # Determine status message based on source
                status_msg = f"音声生成途中 ({current_parts}パート復元済み)" if existing_parts_on_disk and not streaming_parts else f"音声生成途中 ({current_parts}パート復元済み)"

                progress_html = self._create_progress_html(
                    current_parts,
                    estimated_total_parts,
                    status_msg,
                    start_time=audio_state.get("start_time"),
                    resume_from_part=resume_from_part,
                )
                logger.info(f"Found partial audio generation ({current_parts} parts, {len(existing_parts_on_disk)} from disk) - not showing preview until resume")
                # Return None for audio to avoid showing partial audio in preview
                return None, progress_html

        # No audio to restore - check if we should show a "ready to generate" state
        audio_state = browser_state.get("audio_generation_state", {})
        status = audio_state.get("status", "")

        # If there's any indication of previous audio generation activity, show appropriate state
        if status in ["preparing", "generating", "failed"] or audio_state.get("current_script"):
            estimated_total_parts = audio_state.get("estimated_total_parts", 1)
            if status == "failed":
                progress_html = self._create_progress_html(0, estimated_total_parts, "音声生成が中断されました", is_completed=False)
            elif status == "preparing":
                progress_html = self._create_progress_html(0, estimated_total_parts, "音声生成準備中...", is_completed=False)
            else:
                progress_html = self._create_progress_html(0, estimated_total_parts, "音声生成待機中", is_completed=False)
            return None, progress_html

        # Completely no audio state
        return None, ""

    def resume_or_generate_podcast_audio_streaming_with_browser_state(self, text: str, user_session: UserSession, browser_state: Dict[str, Any], progress=None):
        """Resume or start new audio generation with browser state synchronization."""
        logger.info("Resume or generate audio function called")
        logger.debug(f"Text length: {len(text) if text else 0}")
        logger.debug(f"Session ID: {user_session.session_id}")

        audio_state = browser_state.get("audio_generation_state", {})
        current_script = audio_state.get("current_script", "")
        has_streaming_parts = len(audio_state.get("streaming_parts", [])) > 0
        has_final_audio = audio_state.get("final_audio_path") is not None

        logger.debug(f"Current script length: {len(current_script)}")
        logger.info(f"Has streaming parts: {has_streaming_parts}")
        logger.info(f"Has final audio: {has_final_audio}")

        # Check for existing audio parts on disk FIRST (browser_state might not have them due to reload)
        temp_dir = user_session.get_talk_temp_dir()
        existing_part_files_on_disk = []

        logger.debug(f"Checking temp directory: {temp_dir.name}")
        logger.debug(f"Temp dir exists: {temp_dir.exists()}")

        if temp_dir.exists():
            stream_dirs = list(temp_dir.glob("stream_*"))
            logger.debug(f"Found {len(stream_dirs)} stream directories")

            # Find all part_*.wav files in temp directories
            for temp_subdir in stream_dirs:
                if temp_subdir.is_dir():
                    part_files = list(temp_subdir.glob("part_*.wav"))
                    logger.debug(f"In {temp_subdir.name}, found {len(part_files)} part files")
                    for part_file in sorted(part_files):
                        if part_file.exists():
                            existing_part_files_on_disk.append(str(part_file))
                            logger.debug(f"Valid part file: {part_file.name}")
        else:
            logger.debug("Temp directory does not exist")

        has_existing_parts_on_disk = len(existing_part_files_on_disk) > 0
        logger.debug(f"Has existing parts on disk: {has_existing_parts_on_disk} ({len(existing_part_files_on_disk)} files)")

        # Check if script was changed (flag set in prepare phase)
        script_changed = audio_state.get("script_changed", False)
        if script_changed:
            logger.info("Script changed detected (from prepare phase) - will start from part 1")

            # CRITICAL: Clear existing part files on disk when script changes
            if temp_dir.exists():
                logger.info(f"Script changed - cleaning up existing part files in {temp_dir}")
                for temp_subdir in temp_dir.glob("stream_*"):
                    if temp_subdir.is_dir():
                        for part_file in temp_subdir.glob("part_*.wav"):
                            try:
                                part_file.unlink()
                                logger.info(f"Deleted old part file: {part_file.name}")
                            except Exception as e:
                                logger.warning(f"Failed to delete {part_file}: {e}")
                # Re-scan after cleanup
                existing_part_files_on_disk = []
                has_existing_parts_on_disk = False
                logger.info("Cleared all existing part files due to script change")

        # Check if we can resume (script unchanged and has previous audio in browser_state OR on disk)
        can_resume = not script_changed and (has_streaming_parts or has_final_audio or has_existing_parts_on_disk)
        logger.info(f"Can resume: {can_resume} (script_unchanged={not script_changed}, browser_parts={has_streaming_parts}, final_audio={has_final_audio}, disk_parts={has_existing_parts_on_disk})")

        if can_resume and has_final_audio:
            # Audio generation already completed, just restore the final result
            final_audio_path = audio_state.get("final_audio_path")
            if final_audio_path and os.path.exists(final_audio_path):
                progress_html = self._create_progress_html(
                    audio_state.get("estimated_total_parts", 1), audio_state.get("estimated_total_parts", 1), "音声生成完了！ (復元済み)", is_completed=True, start_time=audio_state.get("start_time")
                )
                # Update browser state to ensure consistency
                browser_state["audio_generation_state"]["status"] = "completed"
                browser_state["audio_generation_state"]["is_generating"] = False
                browser_state["audio_generation_state"]["progress"] = 1.0

                yield None, user_session, progress_html, final_audio_path, browser_state
                return

        # If resuming is possible but not completed, check for final audio first
        if can_resume and (has_streaming_parts or has_existing_parts_on_disk):
            logger.info(f"Resuming audio generation with {len(audio_state.get('streaming_parts', []))} browser parts + {len(existing_part_files_on_disk)} disk parts")

            # Check if final audio exists (generation might have completed)
            output_dir = user_session.get_output_dir()
            final_audio_found = None
            for audio_file in output_dir.glob("audio_*.wav"):
                if audio_file.exists():
                    final_audio_found = str(audio_file)
                    break

            if final_audio_found:
                # Generation was actually complete
                browser_state["audio_generation_state"]["final_audio_path"] = final_audio_found
                browser_state["audio_generation_state"]["status"] = "completed"
                browser_state["audio_generation_state"]["progress"] = 1.0

                estimated_parts = audio_state.get("estimated_total_parts", len(existing_part_files_on_disk))
                complete_html = self._create_progress_html(estimated_parts, estimated_parts, "音声生成完了！ (復元済み)", is_completed=True, start_time=audio_state.get("start_time"))
                logger.info(f"Resume: Found completed final audio: {final_audio_found}")
                yield None, user_session, complete_html, final_audio_found, browser_state
                return

            # Combine streaming_parts from browser_state with discovered files on disk
            streaming_parts = audio_state.get("streaming_parts", [])
            all_potential_parts = streaming_parts + existing_part_files_on_disk

            # Remove duplicates and filter valid existing parts
            valid_existing_parts = []
            seen_parts = set()
            for part_path in all_potential_parts:
                if part_path and os.path.exists(part_path) and part_path not in seen_parts:
                    valid_existing_parts.append(part_path)
                    seen_parts.add(part_path)

            # Sort by part number to ensure correct order
            def extract_part_number(path):
                import re

                match = re.search(r"part_(\d+)", os.path.basename(path))
                return int(match.group(1)) if match else 0

            valid_existing_parts.sort(key=extract_part_number)

            if valid_existing_parts:
                resume_from_part = len(valid_existing_parts)
                estimated_parts = audio_state.get("estimated_total_parts", resume_from_part + 1)

                logger.info(f"Resume: Found {len(valid_existing_parts)} existing parts total")
                logger.info(f"Resume: Implementing true resume from part {resume_from_part}")
                logger.info(f"Resume: Existing parts: {[os.path.basename(p) for p in valid_existing_parts]}")

                # Use true resume functionality
                yield from self.generate_podcast_audio_streaming_with_browser_state_and_resume(text, user_session, browser_state, resume_from_part, valid_existing_parts, progress)
                return

            logger.info("Resume: No valid existing parts found, starting from beginning")

        # Start new generation from beginning
        yield from self.generate_podcast_audio_streaming_with_browser_state_and_resume(text, user_session, browser_state, 0, [], progress)

    def set_openai_api_key(self, api_key: str, user_session: UserSession):
        """Set the OpenAI API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.debug("OpenAI API key is empty")
            return user_session

        success = user_session.text_processor.set_openai_api_key(api_key)
        logger.debug(f"OpenAI API key set for session {user_session.session_id}: {success}")
        user_session.auto_save()  # Save session state after API key change
        return user_session

    def set_gemini_api_key(self, api_key: str, user_session: UserSession):
        """Set the Google Gemini API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.debug("Gemini API key is empty")
            return user_session

        success = user_session.text_processor.set_gemini_api_key(api_key)
        logger.debug(f"Gemini API key set for session {user_session.session_id}: {success}")
        user_session.auto_save()  # Save session state after API key change
        return user_session

    def switch_llm_type(self, api_type: APIType, user_session: UserSession) -> UserSession:
        """Switch LLM type for the specific user session."""
        success = user_session.text_processor.set_api_type(api_type)
        if success:
            logger.debug(f"LLM type switched to {api_type.display_name} for session {user_session.session_id}")
        else:
            logger.debug(f"{api_type.display_name} API key not set for session {user_session.session_id}")
        user_session.auto_save()  # Save session state after API type change
        return user_session

    def extract_file_text(
        self,
        file_obj,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[None, str, UserSession]:
        """Extract text from a file and append to existing text for the specific user session."""

        if user_session is None:
            logger.warning("File extraction called with None user_session - creating temporary session")
            # Create a temporary session for this operation
            import uuid

            user_session = UserSession(f"temp_{uuid.uuid4().hex[:8]}")
            logger.info(f"Created temporary session: {user_session.session_id}")

        if file_obj is None:
            logger.debug("No file selected for extraction")
            return None, existing_text, user_session

        # Extract new text from file
        new_text = ContentExtractor.extract_text(file_obj)

        # Get source name from file
        source_name = ContentExtractor.get_source_name_from_file(file_obj)

        # Append to existing text with source information
        combined_text = ContentExtractor.append_text_with_source(existing_text, new_text, source_name, add_separator)

        logger.debug(f"File text extraction completed for session {user_session.session_id}")
        return (
            None,
            combined_text,
            user_session,
        )  # Return None for file_input to clear it

    def extract_url_text(
        self,
        url: str,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[str, UserSession]:
        """Extract text from a URL and append to existing text for the specific user session."""

        try:
            if user_session is None:
                logger.warning("URL extraction called with None user_session - creating temporary session")
                # Create a temporary session for this operation
                import uuid

                user_session = UserSession(f"temp_{uuid.uuid4().hex[:8]}")
                logger.info(f"Created temporary session: {user_session.session_id}")

            logger.info(f"URL extraction request - URL: {url}, add_separator: {add_separator}, session: {user_session.session_id}")

            if not url or not url.strip():
                logger.warning("No URL provided for extraction")
                # Return error message for empty URL input
                error_message = "Please enter a valid URL"
                if existing_text.strip():
                    # If there's existing text, append error message with separator
                    combined_text = existing_text.rstrip() + "\n\n---\n**Error**\n\n" + error_message if add_separator else existing_text.rstrip() + "\n\n" + error_message
                else:
                    # If no existing text, just show error message
                    combined_text = error_message
                return combined_text, user_session

            # Extract new text from URL
            logger.info(f"Extracting text from URL: {url.strip()}")
            new_text = ContentExtractor.extract_from_url(url.strip())
            logger.info(f"Extracted {len(new_text) if new_text else 0} characters from URL")

            # Use URL as source name
            source_name = url.strip()

            # Append to existing text with source information
            combined_text = ContentExtractor.append_text_with_source(existing_text, new_text, source_name, add_separator)
            logger.info(f"URL text extraction completed for session {user_session.session_id} - final text length: {len(combined_text)}")
            return combined_text, user_session

        except Exception as e:
            logger.error(f"Error in URL text extraction: {str(e)}")
            error_message = f"Error extracting from URL: {str(e)}"
            if existing_text.strip():
                combined_text = existing_text.rstrip() + "\n\n---\n**Error**\n\n" + error_message if add_separator else existing_text.rstrip() + "\n\n" + error_message
            else:
                combined_text = error_message
            return combined_text, user_session

    def generate_podcast_text(self, text: str, user_session: UserSession) -> Tuple[str, UserSession]:
        """Generate podcast-style text from input text for the specific user session."""

        if user_session is None:
            logger.warning("Podcast text generation called with None user_session - creating temporary session")
            import uuid

            user_session = UserSession(f"temp_{uuid.uuid4().hex[:8]}")
            logger.info(f"Created temporary session: {user_session.session_id}")

        if not text:
            logger.warning("Podcast text generation: Input text is empty")
            return "Please upload a file and extract text first.", user_session

        # Check if API key is set
        current_llm_type = user_session.text_processor.get_current_api_type()

        if current_llm_type == APIType.OPENAI and not user_session.text_processor.openai_model.has_api_key():
            logger.warning(f"Podcast text generation: OpenAI API key not set for session {user_session.session_id}")
            return (
                "OpenAI API key is not set. Please configure it in the Settings tab.",
                user_session,
            )
        elif current_llm_type == APIType.GEMINI and not user_session.text_processor.gemini_model.has_api_key():
            logger.warning(f"Podcast text generation: Gemini API key not set for session {user_session.session_id}")
            return (
                "Google Gemini API key is not set. Please configure it in the Settings tab.",
                user_session,
            )

        try:
            podcast_text = user_session.text_processor.process_text(text)

            token_usage = user_session.text_processor.get_token_usage()
            if token_usage:
                usage_msg = f"Token usage: input {token_usage.get('prompt_tokens', 0)}, output {token_usage.get('completion_tokens', 0)}, total {token_usage.get('total_tokens', 0)}"
                logger.debug(usage_msg)

            logger.debug(f"Podcast text generation completed for session {user_session.session_id}")
            return podcast_text, user_session
        except Exception as e:
            error_msg = f"Podcast text generation error: {str(e)}"
            logger.error(error_msg)
            return f"Error: {str(e)}", user_session

    def generate_podcast_text_with_browser_state(self, text: str, user_session: UserSession, browser_state: Dict[str, Any]) -> Tuple[str, UserSession, Dict[str, Any]]:
        """Generate podcast text with browser state update."""
        podcast_text, updated_user_session = self.generate_podcast_text(text, user_session)

        # Update browser state with generated podcast text
        updated_browser_state = self.update_browser_state_ui_content(browser_state, podcast_text, browser_state.get("terms_agreed", False), text)

        return podcast_text, updated_user_session, updated_browser_state

    def extract_file_text_auto(
        self,
        file_obj,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[str, UserSession]:
        """Extract text from uploaded file automatically (for file upload mode)."""
        if user_session is None:
            logger.warning("Auto file extraction called with None user_session - creating temporary session")
            import uuid

            user_session = UserSession(f"temp_{uuid.uuid4().hex[:8]}")
            logger.info(f"Created temporary session: {user_session.session_id}")

        if file_obj is None:
            logger.debug("No file provided for automatic extraction")
            return existing_text, user_session

        # Extract new text from file
        new_text = ContentExtractor.extract_text(file_obj)

        # Get source name from file
        source_name = ContentExtractor.get_source_name_from_file(file_obj)

        # Append to existing text with source information
        combined_text = ContentExtractor.append_text_with_source(existing_text, new_text, source_name, add_separator)

        logger.debug(f"Auto file text extraction completed for session {user_session.session_id}")
        return combined_text, user_session

    def extract_file_text_auto_with_browser_state(
        self,
        file_obj,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
        browser_state: Dict[str, Any],
    ) -> Tuple[str, UserSession, Dict[str, Any]]:
        """Extract text from uploaded file automatically with browser state update."""
        combined_text, updated_user_session = self.extract_file_text_auto(file_obj, existing_text, add_separator, user_session)

        # Update browser state with extracted text
        updated_browser_state = self.update_browser_state_ui_content(browser_state, "", False, combined_text)

        return combined_text, updated_user_session, updated_browser_state

    def _estimate_audio_parts_count(self, text: str) -> int:
        """
        Estimate the number of audio parts that will be generated based on the script.

        Args:
            text (str): The podcast script text

        Returns:
            int: Estimated number of audio parts
        """
        import re

        # Count the number of character dialogue lines (四国めたん:, ずんだもん:, etc.)
        character_lines = re.findall(r"^[^:]+:", text, re.MULTILINE)
        estimated_parts = len(character_lines)

        # Minimum 1 part, and add some buffer for safety
        return max(1, estimated_parts)

    def _create_progress_html(
        self,
        current_part: int,
        total_parts: int,
        status_message: str,
        is_completed: bool = False,
        start_time: Optional[float] = None,
        resume_from_part: Optional[int] = None,
    ) -> str:
        """
        Create comprehensive progress display with progress bar, elapsed time, and estimated remaining time.

        Args:
            current_part (int): Current part number
            total_parts (int): Total number of parts
            status_message (str): Status message to display
            is_completed (bool): Whether the generation is completed
            start_time (float): Start time timestamp for calculating elapsed time
            resume_from_part (int): Part number to resume from (for resumable generation)

        Returns:
            str: HTML string for progress display
        """
        import time

        if is_completed:
            progress_percent = 100
            emoji = "✅"
        else:
            progress_percent = int(min(95, (current_part / total_parts) * 100) if total_parts > 0 else 0)
            emoji = "🎵"

        # 経過時間と推定残り時間を計算
        time_info = ""
        if start_time is not None:
            elapsed_time = time.time() - start_time
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)

            if is_completed:
                time_info = f" | 完了時間: {elapsed_minutes:02d}:{elapsed_seconds:02d}"
            elif current_part > 0 and not is_completed:
                # 推定残り時間を計算（現在のペースに基づく）
                avg_time_per_part = elapsed_time / current_part
                remaining_parts = total_parts - current_part
                estimated_remaining = avg_time_per_part * remaining_parts
                remaining_minutes = int(estimated_remaining // 60)
                remaining_seconds = int(estimated_remaining % 60)

                time_info = f" | 経過: {elapsed_minutes:02d}:{elapsed_seconds:02d} | 推定残り: {remaining_minutes:02d}:{remaining_seconds:02d}"
            else:
                time_info = f" | 経過: {elapsed_minutes:02d}:{elapsed_seconds:02d}"

        # プログレスバーのCSS（余分な枠線なし）
        progress_bar_html = f"""
        <div style="width: 100%; background-color: var(--neutral-100, #f3f4f6);
                    border-radius: 8px; height: 6px; margin: 4px 0; overflow: hidden;
                    border: none; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">
            <div style="width: {progress_percent}%; background: linear-gradient(90deg,
                        var(--color-accent, #2563eb) 0%, var(--color-accent-soft, #3b82f6) 100%);
                        height: 100%; border-radius: 8px; transition: width 0.3s ease;">
            </div>
        </div>
        """

        # Gradio Softテーマに合わせたクリーンな進捗表示（余分な枠線なし）
        return f"""
        <div style="padding: 12px 8px; margin: 8px 0; font-family: var(--font, 'Source Sans Pro', sans-serif);
                    color: var(--body-text-color, #111827);
                    background: var(--background-fill-secondary, #f8f9fa);
                    border-radius: var(--radius-sm, 4px);
                    border: none;
                    box-shadow: none;">
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <span style="margin-right: 8px; font-size: 16px;">{emoji}</span>
                <span style="font-weight: 500; flex-grow: 1;">{status_message}</span>
                <span style="color: var(--body-text-color-subdued, #6b7280); font-size: 13px;">
                    パート {current_part}/{total_parts} ({progress_percent:.1f}%){time_info}
                    {" | パート" + str(resume_from_part + 1) + "から再開可能" if resume_from_part is not None and resume_from_part > 0 else ""}
                </span>
            </div>
            {progress_bar_html}
        </div>
        """

    def _create_error_html(self, error_message: str) -> str:
        """
        Create simple error display compatible with Gradio Soft theme.

        Args:
            error_message (str): Error message to display

        Returns:
            str: HTML string for error display
        """
        return f"""
        <div style="padding: 12px; margin: 4px 0; font-family: var(--font, 'Source Sans Pro', sans-serif);
                    background: var(--error-background-fill, #fef2f2);
                    border-radius: var(--radius-md, 6px);
                    border: 1px solid var(--error-border-color, #fecaca);">
            <span style="margin-right: 8px;">❌</span>
            <span style="font-weight: 500; color: var(--error-text-color, #dc2626);">{error_message}</span>
        </div>
        """

    def _create_recovery_progress_html(self, user_session: UserSession, status_message: str, is_active: bool = False) -> str:
        """
        Create progress HTML for connection recovery scenarios using new UserSession recovery methods.

        Args:
            user_session (UserSession): User session instance
            status_message (str): Status message to display
            is_active (bool): Whether generation is currently active

        Returns:
            str: HTML string for recovery progress display
        """
        if not status_message:
            return ""

        # Use new recovery progress info method
        recovery_info = user_session.get_recovery_progress_info()

        current_part_count = recovery_info["streaming_parts_count"]
        estimated_total_parts = recovery_info["estimated_total_parts"]
        start_time = recovery_info["start_time"]

        # Adjust estimated parts if actual parts exceed estimate
        if current_part_count > estimated_total_parts:
            estimated_total_parts = current_part_count

        if is_active:
            # Active generation case
            return self._create_progress_html(
                current_part_count,
                estimated_total_parts,
                status_message,
                start_time=start_time,
            )
        else:
            # Completed/failed case
            # For completed status, show full progress
            display_parts = estimated_total_parts if recovery_info["status"] == "completed" else current_part_count
            return self._create_progress_html(
                display_parts,
                estimated_total_parts,
                status_message,
                is_completed=(recovery_info["status"] == "completed"),
                start_time=start_time,
            )

    def generate_podcast_audio_streaming(self, text: str, user_session: UserSession, progress=None):
        """
        Generate streaming audio from podcast text with progress tracking.
        Saves intermediate results to user_session and displays progress.

        Args:
            text (str): Generated podcast text
            user_session (UserSession): User session instance
            progress (gr.Progress): Gradio Progress object

        Yields:
            Tuple[str, UserSession, str, str]: (streaming_audio_path, updated_user_session, progress_html, final_audio_path)
        """
        if not text:
            logger.warning("Streaming audio generation: Text is empty")
            user_session.update_audio_generation_state(status="failed", is_generating=False)
            error_html = self._create_error_html("テキストが空のため音声生成できません")
            yield None, user_session, error_html, None
            return

        # Check if VOICEVOX Core is available
        if not user_session.audio_generator.core_initialized:
            logger.error("Streaming audio generation: VOICEVOX Core is not available")
            user_session.update_audio_generation_state(status="failed", is_generating=False)
            error_html = self._create_error_html("VOICEVOX Coreが利用できません")
            yield None, user_session, error_html, None
            return

        try:
            # Initialize progress if not provided
            if progress is None:
                progress = gr.Progress()

            # スクリプトからパーツ数を推定
            estimated_total_parts = self._estimate_audio_parts_count(text)
            logger.info(f"Estimated total audio parts: {estimated_total_parts}")

            # 音声生成状態を初期化
            generation_id = str(uuid.uuid4())
            user_session.update_audio_generation_state(
                is_generating=True,
                status="generating",
                current_script=text,
                generation_id=generation_id,
                start_time=time.time(),
                progress=0.0,
                generated_parts=[],
                streaming_parts=[],
                final_audio_path=None,
                estimated_total_parts=estimated_total_parts,  # 推定パーツ数を保存
            )

            # 初回のyieldを行って、Gradioのストリーミングモードを確実に有効化
            logger.debug(f"Initializing streaming audio generation (ID: {generation_id})")
            start_html = self._create_progress_html(
                0,
                estimated_total_parts,
                "音声生成を開始しています...",
                start_time=time.time(),
            )
            yield None, user_session, start_html, None

            # gr.Progressも使用（Gradio標準の進捗バー）
            progress(0, desc="🎤 音声生成を開始しています...")

            # ストリーミング用の各パートのパスを保存
            parts_paths = []
            final_combined_path = None
            current_part_count = 0  # ローカルカウンターを使用

            # 個別の音声パートを生成・ストリーミング
            for audio_path in user_session.audio_generator.generate_character_conversation(text, 0, []):
                if not audio_path:
                    continue

                filename = os.path.basename(audio_path)

                # 'part_'を含むものは部分音声ファイル、'audio_'から始まるものは最終結合ファイル
                if "part_" in filename:
                    parts_paths.append(audio_path)
                    current_part_count += 1  # ローカルカウンターをインクリメント
                    progress_ratio = min(0.95, current_part_count / estimated_total_parts)

                    # 進捗状況をログに記録
                    logger.info(f"Audio part {current_part_count}/{estimated_total_parts} completed")

                    logger.debug(f"ストリーム音声パーツ ({current_part_count}/{estimated_total_parts}): {audio_path}")

                    # 進捗情報を生成してyield（新しい詳細進捗表示）
                    start_time = user_session.audio_generation_state.get("start_time")

                    # パートが完了した場合の適切なメッセージ
                    if current_part_count < estimated_total_parts:
                        status_message = f"音声パート {current_part_count} が完了..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了..."
                    else:
                        status_message = f"音声パート {current_part_count} が完了、最終処理中..."
                        progress_desc = f"🎵 音声パート {current_part_count}/{estimated_total_parts} 完了、最終処理中..."

                    progress_html = self._create_progress_html(
                        current_part_count,
                        estimated_total_parts,
                        status_message,
                        start_time=start_time,
                    )

                    # gr.Progressも更新
                    progress(
                        progress_ratio,
                        desc=progress_desc,
                    )

                    yield (
                        audio_path,
                        user_session,
                        progress_html,
                        None,
                    )  # ストリーミング再生用にyield
                    time.sleep(0.05)  # 連続再生のタイミング調整
                elif filename.startswith("audio_"):
                    # 最終結合ファイルの場合
                    final_combined_path = audio_path
                    user_session.update_audio_generation_state(final_audio_path=audio_path, progress=1.0)
                    logger.info(f"結合済み最終音声ファイルを受信: {final_combined_path}")

                    # 最終音声完成の進捗を表示
                    start_time = user_session.audio_generation_state.get("start_time")
                    complete_html = self._create_progress_html(
                        estimated_total_parts,
                        estimated_total_parts,
                        "音声生成完了！",
                        is_completed=True,
                        start_time=start_time,
                    )

                    # gr.Progressも完了状態に
                    progress(1.0, desc="✅ 音声生成完了！")

                    yield None, user_session, complete_html, final_combined_path

            # 音声生成の完了処理
            self._finalize_audio_generation(final_combined_path, parts_paths, user_session)

        except Exception as e:
            logger.error(f"Streaming audio generation exception: {str(e)}")
            user_session.update_audio_generation_state(status="failed", is_generating=False, progress=0.0)
            error_html = self._create_error_html(f"音声生成でエラーが発生しました: {str(e)}")
            progress(0, desc="❌ 音声生成エラー")
            yield None, user_session, error_html, None

    def _finalize_audio_generation(self, final_combined_path, parts_paths, user_session: UserSession):
        """
        音声生成の最終処理を行う

        Args:
            final_combined_path (str): 結合された最終音声ファイルのパス
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
            user_session (UserSession): ユーザーセッションインスタンス

        Returns:
            str: 最終的な音声ファイルの情報、またはNone
        """
        # 最終結合ファイルのパスが取得できた場合
        if final_combined_path and os.path.exists(final_combined_path):
            # 進捗を更新
            user_session.audio_generator.audio_generation_progress = 0.9
            user_session.update_audio_generation_state(progress=0.9)
            logger.info(f"最終結合音声ファイル: {final_combined_path}")

            # 最終的な音声ファイルのパスを保存
            user_session.audio_generator.final_audio_path = final_combined_path

            # ファイルの書き込みを確実にするため少し待機
            time.sleep(0.2)

            if os.path.exists(final_combined_path):
                filesize = os.path.getsize(final_combined_path)
                # 進捗を完了状態に更新
                user_session.audio_generator.audio_generation_progress = 1.0
                user_session.update_audio_generation_state(
                    progress=1.0,
                    status="completed",
                    is_generating=False,
                    final_audio_path=final_combined_path,
                )
                logger.info(f"音声生成完了: {final_combined_path} (ファイルサイズ: {filesize} bytes)")
                return final_combined_path  # 最終的な音声ファイルパスを返す
            else:
                logger.error(f"ファイルが存在しなくなりました: {final_combined_path}")
                return self._use_fallback_audio(parts_paths, user_session)

        # 最終結合ファイルがない場合はフォールバック処理
        else:
            return self._use_fallback_audio(parts_paths, user_session)

    def _use_fallback_audio(self, parts_paths, user_session: UserSession):
        """
        結合ファイルが取得できない場合のフォールバック処理

        Args:
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
            user_session (UserSession): ユーザーセッションインスタンス

        Returns:
            str: フォールバックで使用する音声ファイルパス、またはNone
        """
        # 部分音声ファイルがある場合は最後のパートを使用
        if parts_paths:
            logger.warning("結合音声ファイルを取得できなかったため、最後のパートを使用します")
            user_session.audio_generator.final_audio_path = parts_paths[-1]
            user_session.audio_generator.audio_generation_progress = 1.0
            user_session.update_audio_generation_state(
                status="completed",
                is_generating=False,
                progress=1.0,
                final_audio_path=parts_paths[-1],
            )

            if os.path.exists(parts_paths[-1]):
                filesize = os.path.getsize(parts_paths[-1])
                logger.info(f"部分音声ファイル使用: {parts_paths[-1]} (ファイルサイズ: {filesize} bytes)")
                return parts_paths[-1]  # フォールバック音声ファイルパスを返す
            else:
                logger.error(f"フォールバックファイルも存在しません: {parts_paths[-1]}")
                user_session.audio_generator.audio_generation_progress = 0.0
                user_session.update_audio_generation_state(status="failed", is_generating=False, progress=0.0)
        else:
            logger.warning("音声ファイルが生成されませんでした")
            user_session.audio_generator.audio_generation_progress = 0.0
            user_session.update_audio_generation_state(status="failed", is_generating=False, progress=0.0)
        return None  # エラー時はNoneを返す

    def disable_generate_button(self):
        """音声生成ボタンを無効化します。"""
        return gr.update(interactive=False, value="音声生成中...")

    def enable_generate_button(self, terms_agreed: bool, podcast_text: str):
        """音声生成ボタンを再び有効化します。"""
        return self.update_audio_button_state(terms_agreed, podcast_text)

    def disable_process_button(self):
        """トーク原稿生成ボタンを無効化します。"""
        return gr.update(interactive=False, value="トーク原稿生成中...")

    def _check_process_button_conditions(self, extracted_text: str, user_session: UserSession) -> Tuple[bool, bool]:
        """Check conditions for process button state."""
        has_text = bool(extracted_text and extracted_text.strip() != "" and extracted_text not in ["Please upload a file.", "Failed to process the file."])

        current_llm_type = user_session.text_processor.get_current_api_type()
        if current_llm_type == APIType.OPENAI:
            has_api_key = user_session.text_processor.openai_model.has_api_key()
        elif current_llm_type == APIType.GEMINI:
            has_api_key = user_session.text_processor.gemini_model.has_api_key()
        else:
            has_api_key = False

        return has_text, has_api_key

    def enable_process_button(self, extracted_text: str, user_session: UserSession):
        """トーク原稿生成ボタンを再び有効化します。"""
        has_text, has_api_key = self._check_process_button_conditions(extracted_text, user_session)
        is_enabled = has_text and has_api_key

        return gr.update(
            interactive=is_enabled,
            value="トーク原稿を生成",
            variant="primary" if is_enabled else "secondary",
        )

    def ui(self) -> gr.Blocks:
        """
        Create the Gradio interface.

        Returns:
            gr.Blocks: Gradio Blocks instance
        """
        app = gr.Blocks(
            title="Yomitalk",
            css="footer {display: none !important;}",
            theme=gr.themes.Soft(),
        )

        # アプリケーション全体でキューイングを有効化
        # Hugging Face Spacesの無料CPUを効率的に使うため、同時実行数を1に制限
        app.queue(
            default_concurrency_limit=1,  # デフォルトの同時実行数を1に制限
            api_open=False,  # APIアクセスを制限
            max_size=5,  # キュー内の最大タスク数を制限
            status_update_rate=1,  # ステータス更新頻度（秒）
        )

        with app:
            # ヘッダー部分をロゴと免責事項を含むレイアウトに変更
            with gr.Row(equal_height=True, variant="panel", elem_classes="header-row"):
                with gr.Column(scale=1, min_width=200):
                    gr.Image(
                        "assets/images/logo.png",
                        show_label=False,
                        show_download_button=False,
                        show_fullscreen_button=False,
                        container=False,
                        scale=1,
                    )
                with gr.Column(scale=3, elem_classes="disclaimer-column"), gr.Row(elem_id="disclaimer-container"):
                    gr.Markdown(
                        """**ドキュメントからポッドキャスト風の解説音声を生成するアプリケーション**

                            **免責事項**: このアプリケーションはLLM（大規模言語モデル）を使用しています。生成される内容の正確性、完全性、適切性について保証することはできません。
                            また、秘密文書のアップロードは推奨されません。当アプリケーションの使用により生じた、いかなる損害についても責任を負いません。""",
                        elem_id="disclaimer-text",
                    )

            # カスタムCSSスタイルを追加
            css = """
            /* ロゴ画像のスタイル調整 */
            .gradio-image {
                margin: 0 !important;
                padding: 0 !important;
                display: flex !important;
                align-items: flex-end !important;
            }

            /* ロゴ画像コンテナの左余白を削除 */
            .gradio-column:has(> .gradio-image) {
                padding-left: 0 !important;
            }

            /* ヘッダー行のスタイル調整 */
            .header-row {
                display: flex !important;
                align-items: flex-end !important;
                min-height: 80px !important;
            }

            /* 免責事項の列のスタイル調整 */
            .disclaimer-column {
                display: flex !important;
                align-items: flex-end !important;
            }

            /* 免責事項のコンテナスタイル */
            #disclaimer-container {
                display: flex !important;
                align-items: flex-end !important;
                height: 100% !important;
                margin-bottom: 0 !important;
                padding: 5px 0 !important;
                width: 100% !important;
            }

            /* 免責事項のテキストスタイル */
            #disclaimer-text p {
                margin: 0 !important;
                padding-bottom: 5px !important;
                font-size: 0.9em !important;
                line-height: 1.4 !important;
                max-width: 100% !important;
            }

            /* 音声生成進捗表示のスタイル調整 - 完全にクリーンな表示 */
            #audio_progress {
                margin: 8px 0 !important;
                font-size: 14px !important;
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                padding: 0 !important;
            }

            /* Gradioのすべてのデフォルト装飾を除去 */
            #audio_progress,
            #audio_progress > *,
            #audio_progress .block,
            #audio_progress .prose,
            #audio_progress .gradio-html {
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 !important;
                outline: none !important;
            }

            /* コンテナの余白とボーダーを完全除去 */
            #audio_progress .gradio-container {
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            /* オーディオ出力のスタイル調整 */
            #audio_output {
                min-height: 180px !important;
                margin-bottom: 10px;
            }

            #audio_output.empty::before {
                content: "音声生成が完了すると、ここに波形と再生コントロールが表示されます";
                display: flex;
                justify-content: center;
                align-items: center;
                height: 140px;
                color: #555;
                font-style: italic;
                background-color: rgba(0,0,0,0.03);
                border-radius: 8px;
                text-align: center;
                padding: 10px;
            }

            #streaming_audio_output.empty::before {
                content: "音声生成が開始されると、ここでストリーミング再生できます";
                display: flex;
                justify-content: center;
                align-items: center;
                height: 80px;
                color: #555;
                font-style: italic;
                background-color: rgba(0,0,0,0.03);
                border-radius: 8px;
                text-align: center;
                padding: 10px;
            }

            /* Footer styling */
            #footer {
                text-align: center !important;
                margin: 15px 0 10px !important;
                font-size: 14px !important;
            }

            #footer a {
                color: #888 !important;
                text-decoration: none !important;
            }

            #footer a:hover {
                color: #555 !important;
            }
            """
            gr.HTML(f"<style>{css}</style>")

            with gr.Column():
                gr.Markdown("""## トーク原稿の生成""")
                with gr.Column(variant="panel"):
                    # サポートしているファイル形式の拡張子を取得
                    supported_extensions = ContentExtractor.SUPPORTED_EXTENSIONS

                    # Content extraction tabs
                    gr.Markdown("### 解説対象テキストの作成")

                    extraction_tabs = gr.Tabs()
                    with extraction_tabs:
                        with gr.TabItem("ファイルアップロード"):
                            file_input = gr.File(
                                file_types=supported_extensions,
                                type="filepath",
                                label=f"ファイルをアップロード（{', '.join(supported_extensions)}）",
                                height=120,
                                interactive=False,
                                file_count="single",  # 単一ファイルのみ
                            )

                        with gr.TabItem("Webページ抽出"):
                            url_input = gr.Textbox(
                                placeholder="初期化中です。少しお待ちください...",
                                label="WebページのURLを入力",
                                info="注: Hugging Face Spacesで利用する場合はYouTubeなどの一部サイトからの抽出ができません",
                                lines=2,
                                interactive=False,
                            )
                            url_extract_btn = gr.Button(
                                "初期化中...",
                                variant="secondary",
                                size="lg",
                                interactive=False,
                            )

                    # Auto separator checkbox and clear button in the same row
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3):
                            auto_separator_checkbox = gr.Checkbox(
                                label="テキスト抽出時に区切りを自動挿入",
                                value=True,
                                info="ファイル名やURLの情報を含む区切り線を自動挿入します",
                                interactive=False,
                            )
                        with gr.Column(scale=1):
                            clear_text_btn = gr.Button(
                                "初期化中...",
                                variant="secondary",
                                size="sm",
                                interactive=False,
                            )

                    # Extracted text display
                    extracted_text = gr.Textbox(
                        label="解説対象テキスト（トークの元ネタ）",
                        placeholder="ファイルをアップロードするか、URLを入力するか、直接ここにテキストを貼り付けてください...",
                        lines=10,
                        interactive=True,
                    )

                with gr.Column(variant="panel"):
                    gr.Markdown("### プロンプト設定")
                    document_type_radio = gr.Radio(
                        choices=DocumentType.get_all_label_names(),
                        value=PromptManager.DEFAULT_DOCUMENT_TYPE.label_name,  # 後でユーザーセッションの値で更新される
                        label="ドキュメントタイプ",
                        elem_id="document_type_radio_group",
                        interactive=False,
                    )

                    podcast_mode_radio = gr.Radio(
                        choices=PodcastMode.get_all_label_names(),
                        value=PromptManager.DEFAULT_MODE.label_name,  # 後でユーザーセッションの値で更新される
                        label="生成モード",
                        elem_id="podcast_mode_radio_group",
                        interactive=False,
                    )

                    # キャラクター設定
                    with gr.Accordion(label="キャラクター設定", open=False), gr.Row():
                        character1_dropdown = gr.Dropdown(
                            choices=DISPLAY_NAMES,
                            value=PromptManager.DEFAULT_CHARACTER1.display_name,  # 後でユーザーセッションの値で更新される
                            label="キャラクター1（専門家役）",
                            interactive=False,
                        )
                        character2_dropdown = gr.Dropdown(
                            choices=DISPLAY_NAMES,
                            value=PromptManager.DEFAULT_CHARACTER2.display_name,  # 後でユーザーセッションの値で更新される
                            label="キャラクター2（初学者役）",
                            interactive=False,
                        )

                with gr.Column(variant="panel"):
                    # LLM API設定タブ
                    llm_tabs = gr.Tabs()
                    with llm_tabs:
                        with gr.TabItem("Google Gemini") as gemini_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    gemini_api_key_input = gr.Textbox(
                                        placeholder="初期化中...",
                                        type="password",
                                        label="Google Gemini APIキー",
                                        info="APIキーの取得: https://aistudio.google.com/app/apikey",
                                        interactive=False,
                                    )
                                with gr.Column(scale=2):
                                    gemini_model_dropdown = gr.Dropdown(
                                        choices=GeminiModel.AVAILABLE_MODELS,
                                        value=GeminiModel.DEFAULT_MODEL,
                                        label="モデル",
                                        interactive=False,
                                    )
                            with gr.Row():
                                gemini_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=65536,
                                    value=GeminiModel.DEFAULT_MAX_TOKENS,
                                    step=100,
                                    label="最大トークン数",
                                    interactive=False,
                                )

                        with gr.TabItem("OpenAI") as openai_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    openai_api_key_input = gr.Textbox(
                                        placeholder="初期化中...",
                                        type="password",
                                        label="OpenAI APIキー",
                                        info="APIキーの取得: https://platform.openai.com/api-keys",
                                        interactive=False,
                                    )
                                with gr.Column(scale=2):
                                    openai_model_dropdown = gr.Dropdown(
                                        choices=OpenAIModel.AVAILABLE_MODELS,
                                        value=OpenAIModel.DEFAULT_MODEL,
                                        label="モデル",
                                        interactive=False,
                                    )
                            with gr.Row():
                                openai_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=32768,
                                    value=OpenAIModel.DEFAULT_MAX_TOKENS,
                                    step=100,
                                    label="最大トークン数",
                                    interactive=False,
                                )

                    # トーク原稿を生成ボタン
                    process_btn = gr.Button("初期化中...", variant="secondary", interactive=False)
                    podcast_text = gr.Textbox(
                        label="生成されたトーク原稿",
                        placeholder="初期化中です。少しお待ちください...",
                        lines=15,
                        interactive=False,
                    )

                    # トークン使用状況の表示
                    token_usage_info = gr.HTML(
                        "<div>トークン使用状況: まだ生成されていません</div>",
                        elem_id="token-usage-info",
                    )

            with gr.Column():
                gr.Markdown("## トーク音声の生成")
                with gr.Column(variant="panel"):
                    msg = """音声は下記の音源を使用して生成されます。
                    VOICEVOX:四国めたん、VOICEVOX:ずんだもん、VOICEVOX:九州そら、VOICEVOX:中国うさぎ、VOICEVOX:中部つるぎ
                    音声を生成するには[VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)への同意が必要です。
                    """
                    # VOICEVOX利用規約チェックボックスをここに配置
                    terms_checkbox = gr.Checkbox(
                        label="VOICEVOX 音源利用規約に同意する",
                        value=False,
                        info=msg,
                        interactive=False,
                    )
                    generate_btn = gr.Button("初期化中...", variant="secondary", interactive=False)

                    # 音声生成進捗表示
                    audio_progress = gr.HTML(
                        value="",
                        elem_id="audio_progress",
                        visible=True,
                        show_label=False,
                        container=False,
                    )

                    # ストリーミング再生用のオーディオコンポーネント
                    streaming_audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=False,
                        show_label=True,
                        label="プレビュー",
                        value=None,
                        elem_id="streaming_audio_output",
                        streaming=True,
                    )

                    # 最終的な音声ファイル用のオーディオコンポーネント
                    # NOTE: gradioの仕様上, ストリーミング用のAudioでは波形が表示できないため, このコンポーネントで波形を表示する
                    audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=True,
                        show_label=True,
                        label="完成音声",
                        value=None,
                        elem_id="audio_output",
                        waveform_options=gr.WaveformOptions(
                            show_recording_waveform=True,
                            waveform_color="#3498db",
                            waveform_progress_color="#27ae60",
                        ),
                        min_width=300,
                    )

            # Footer with repository link
            with gr.Row():
                gr.HTML(
                    """<div id="footer">
                        <a href="https://github.com/KyosukeIchikawa/yomitalk" target="_blank">GitHub</a>
                    </div>"""
                )

            # Initialize BrowserState for persistent session management - stores all session data in localStorage
            browser_state = gr.BrowserState(
                {
                    "app_session_id": "",  # App-generated persistent session ID
                    "audio_generation_state": {
                        "is_generating": False,
                        "progress": 0.0,
                        "status": "idle",
                        "current_script": "",
                        "final_audio_path": None,
                        "streaming_parts": [],
                        "generation_id": None,
                        "start_time": None,
                        "estimated_total_parts": 1,
                    },
                    "user_settings": {
                        "current_api_type": "gemini",
                        "document_type": "research_paper",
                        "podcast_mode": "academic",
                        "character1": "Zundamon",
                        "character2": "Shikoku Metan",
                        "openai_max_tokens": 4000,
                        "gemini_max_tokens": 8000,
                        "openai_model": "gpt-4o-mini",
                        "gemini_model": "gemini-1.5-flash",
                    },
                    "ui_state": {"podcast_text": "", "terms_agreed": False, "extracted_text": ""},
                }
            )
            # Initialize regular State for UserSession object (not serializable to localStorage)
            user_session = gr.State()

            app.load(
                fn=self.initialize_session_and_ui,
                inputs=[browser_state],  # Pass browser_state as input for restoration
                outputs=[
                    user_session,
                    browser_state,
                    document_type_radio,
                    podcast_mode_radio,
                    character1_dropdown,
                    character2_dropdown,
                    openai_max_tokens_slider,
                    gemini_max_tokens_slider,
                    file_input,
                    url_input,
                    url_extract_btn,
                    auto_separator_checkbox,
                    clear_text_btn,
                    extracted_text,
                    document_type_radio,
                    podcast_mode_radio,
                    character1_dropdown,
                    character2_dropdown,
                    gemini_api_key_input,
                    gemini_model_dropdown,
                    gemini_max_tokens_slider,
                    openai_api_key_input,
                    openai_model_dropdown,
                    openai_max_tokens_slider,
                    process_btn,
                    podcast_text,
                    terms_checkbox,
                    streaming_audio_output,
                    audio_progress,
                    audio_output,
                    generate_btn,
                ],
                queue=False,
            )

            # Set up event handlers
            # Clear text button
            clear_text_btn.click(
                fn=lambda browser_state: ("", self.update_browser_state_ui_content(browser_state, "", False, "")),
                inputs=[browser_state],
                outputs=[extracted_text, browser_state],
                queue=False,
            )

            # Auto file extraction when file is uploaded (file upload mode)
            # Use upload event instead of change to avoid duplicate triggers
            file_upload_event = file_input.upload(
                fn=self.extract_file_text_auto_with_browser_state,
                inputs=[
                    file_input,
                    extracted_text,
                    auto_separator_checkbox,
                    user_session,
                    browser_state,
                ],
                outputs=[extracted_text, user_session, browser_state],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="file_queue",  # ファイル処理用キューID
                trigger_mode="once",  # 処理中の重複実行を防止
            )

            # Clear file input after successful extraction
            file_upload_event.then(
                fn=lambda: None,
                outputs=[file_input],
            )

            # Enable process button after file extraction
            file_upload_event.then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # URL抽出ボタンのイベントハンドラー
            url_extract_btn.click(
                fn=self.extract_url_text_with_debug_and_browser_state,
                inputs=[
                    url_input,
                    extracted_text,
                    auto_separator_checkbox,
                    user_session,
                    browser_state,
                ],
                outputs=[extracted_text, user_session, browser_state],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="url_queue",  # URL処理用キューID
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # OpenAI API key - ユーザが入力したらすぐに保存
            openai_api_key_input.change(
                fn=self.set_openai_api_key,
                inputs=[openai_api_key_input, user_session],
                outputs=[user_session],
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # Gemini API key
            gemini_api_key_input.change(
                fn=self.set_gemini_api_key,
                inputs=[gemini_api_key_input, user_session],
                outputs=[user_session],
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # タブ切り替え時のLLMタイプ変更
            gemini_tab.select(
                fn=lambda user_session: self.switch_llm_type(APIType.GEMINI, user_session),
                inputs=[user_session],
                outputs=[user_session],
            )

            openai_tab.select(
                fn=lambda user_session: self.switch_llm_type(APIType.OPENAI, user_session),
                inputs=[user_session],
                outputs=[user_session],
            )

            # OpenAI Model selection
            openai_model_dropdown.change(
                fn=self.set_openai_model_name,
                inputs=[openai_model_dropdown, user_session],
                outputs=[user_session],
            )

            # Gemini Model selection
            gemini_model_dropdown.change(
                fn=self.set_gemini_model_name,
                inputs=[gemini_model_dropdown, user_session],
                outputs=[user_session],
            )

            # OpenAI Max tokens selection
            openai_max_tokens_slider.change(
                fn=self.set_openai_max_tokens,
                inputs=[openai_max_tokens_slider, user_session],
                outputs=[user_session],
            )

            # Gemini Max tokens selection
            gemini_max_tokens_slider.change(
                fn=self.set_gemini_max_tokens,
                inputs=[gemini_max_tokens_slider, user_session],
                outputs=[user_session],
            )

            character1_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown, user_session],
                outputs=[user_session],
            )

            character2_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown, user_session],
                outputs=[user_session],
            )

            # VOICEVOX Terms checkbox - 音声生成ボタンに対してイベントハンドラを更新
            terms_checkbox.change(
                fn=self.update_audio_button_state_with_resume_check_and_browser_state,
                inputs=[terms_checkbox, podcast_text, user_session, browser_state],
                outputs=[generate_btn, browser_state],
            )

            # トーク原稿の生成処理（時間のかかるLLM処理なのでキューイングを適用）
            # 1. まずボタンを無効化
            process_events = process_btn.click(
                fn=self.disable_process_button,
                inputs=[],
                outputs=[process_btn],
                queue=False,  # 即時実行
                api_name="disable_process_button",
            )

            # 2. トーク原稿の生成処理
            process_events.then(
                fn=self.generate_podcast_text_with_browser_state,
                inputs=[extracted_text, user_session, browser_state],
                outputs=[podcast_text, user_session, browser_state],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="llm_queue",  # LLM関連のリクエスト用キューID
            ).then(
                # トークン使用状況をUIに反映
                fn=self.update_token_usage_display,
                inputs=[user_session],
                outputs=[token_usage_info],
            ).then(
                # トーク原稿生成後に音声生成ボタンの状態を更新（再開機能付き）
                fn=self.update_audio_button_state_with_resume_check,
                inputs=[terms_checkbox, podcast_text, user_session],
                outputs=[generate_btn],
            ).then(
                # 3. 最後にトーク原稿生成ボタンを再度有効化
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
                queue=False,  # 即時実行
                api_name="enable_process_button",
            )

            # 音声生成ボタンのイベントハンドラ（ストリーミング再生と最終波形表示を並列処理）

            # ボタンを無効化する（クリック時）
            disable_btn_event = generate_btn.click(
                fn=self.disable_generate_button,
                inputs=[],
                outputs=[generate_btn],
                queue=False,  # 即時実行
                api_name="disable_generate_button",
            )

            # 0. 音声生成準備: current_scriptをbrowser_stateに保存してからUIコンポーネントをクリア
            audio_events = disable_btn_event.then(
                fn=self.prepare_audio_generation_with_browser_state,
                inputs=[podcast_text, user_session, browser_state],
                outputs=[streaming_audio_output, audio_progress, audio_output, browser_state],
                concurrency_id="audio_prepare",
                concurrency_limit=1,  # 同時実行数を1に制限
                api_name="prepare_audio_generation",
            )

            # 1. ストリーミング再生開始 (音声パーツ生成とストリーミング再生、または再開)
            streaming_event = audio_events.then(
                fn=self.resume_or_generate_podcast_audio_streaming_with_browser_state,
                inputs=[podcast_text, user_session, browser_state],
                outputs=[
                    streaming_audio_output,
                    user_session,
                    audio_progress,
                    audio_output,
                    browser_state,
                ],
                concurrency_limit=1,  # 音声生成は1つずつ実行
                concurrency_id="audio_queue",  # 音声生成用キューID
                show_progress="hidden",  # ストリーミング表示では独自の進捗バーを表示しない
                api_name="generate_streaming_audio",  # APIエンドポイント名（デバッグ用）
            )

            # 2. 処理完了後にボタンを再度有効化（再開機能付き）
            # Note: audio_outputはgenerate_podcast_audio_streamingで直接更新される
            streaming_event.then(
                fn=self.update_audio_button_state_with_resume_check_and_browser_state,
                inputs=[terms_checkbox, podcast_text, user_session, browser_state],
                outputs=[generate_btn, browser_state],
                queue=False,  # 即時実行
                api_name="enable_generate_button",
            )

            # ドキュメントタイプ選択のイベントハンドラ
            document_type_radio.change(
                fn=self.set_document_type,
                inputs=[document_type_radio, user_session, browser_state],
                outputs=[user_session, browser_state],
            )

            # ポッドキャストモード選択のイベントハンドラ
            podcast_mode_radio.change(
                fn=self.set_podcast_mode,
                inputs=[podcast_mode_radio, user_session, browser_state],
                outputs=[user_session, browser_state],
            )

            # podcast_textの変更時にも音声生成ボタンの状態を更新（再開機能を含む）
            podcast_text.change(
                fn=self.update_audio_button_state_with_resume_check_and_browser_state,
                inputs=[terms_checkbox, podcast_text, user_session, browser_state],
                outputs=[generate_btn, browser_state],
            )

            # extracted_textの変更時にもbrowser_stateを更新
            extracted_text.change(
                fn=self.update_browser_state_extracted_text,
                inputs=[extracted_text, browser_state],
                outputs=[browser_state],
                queue=False,
            )

        return app

    def set_openai_model_name(self, model_name: str, user_session: UserSession) -> UserSession:
        """
        OpenAIモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = user_session.text_processor.openai_model.set_model_name(model_name)
        logger.debug(f"OpenAI model set to {model_name}: {success}")
        user_session.auto_save()  # Save session state after model name change
        return user_session

    def set_gemini_model_name(self, model_name: str, user_session: UserSession) -> UserSession:
        """
        Geminiモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = user_session.text_processor.gemini_model.set_model_name(model_name)
        logger.debug(f"Gemini model set to {model_name}: {success}")
        user_session.auto_save()  # Save session state after model name change
        return user_session

    def set_openai_max_tokens(self, max_tokens: int, user_session: UserSession) -> UserSession:
        """
        OpenAIの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = user_session.text_processor.openai_model.set_max_tokens(max_tokens)
        logger.debug(f"OpenAI max tokens set to {max_tokens}: {success}")
        user_session.auto_save()  # Save session state after max tokens change
        return user_session

    def set_gemini_max_tokens(self, max_tokens: int, user_session: UserSession) -> UserSession:
        """
        Geminiの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = user_session.text_processor.gemini_model.set_max_tokens(max_tokens)
        logger.debug(f"Gemini max tokens set to {max_tokens}: {success}")
        user_session.auto_save()  # Save session state after max tokens change
        return user_session

    def set_character_mapping(self, character1: str, character2: str, user_session: UserSession) -> UserSession:
        """キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクター名
            character2 (str): Character2に割り当てるキャラクター名
        """
        success = user_session.text_processor.set_character_mapping(character1, character2)
        logger.debug(f"Character mapping set: {character1}, {character2}: {success}")
        user_session.auto_save()  # Save session state after character mapping change
        return user_session

    def set_podcast_mode(self, mode: str, user_session: UserSession, browser_state: Dict[str, Any]) -> Tuple[UserSession, Dict[str, Any]]:
        """
        ポッドキャスト生成モードを設定します。

        Args:
            mode (str): ポッドキャストモードのラベル名
            user_session (UserSession): ユーザーセッション
            browser_state (Dict[str, Any]): ブラウザ状態

        Returns:
            Tuple[UserSession, Dict[str, Any]]: 更新されたユーザーセッションとブラウザ状態
        """
        try:
            # ラベル名からPodcastModeを取得
            podcast_mode = PodcastMode.from_label_name(mode)

            # TextProcessorを使ってPodcastModeのEnumを設定
            success = user_session.text_processor.set_podcast_mode(podcast_mode.value)

            if success:
                # browser_stateにポッドキャストモードを保存
                browser_state["user_settings"]["podcast_mode"] = podcast_mode.value
                logger.debug(f"Podcast mode set to {mode}: {success}, saved to browser_state")
            else:
                logger.warning(f"Failed to set podcast mode to {mode}")

            user_session.auto_save()  # Save session state after podcast mode change

        except ValueError as e:
            logger.error(f"Error setting podcast mode: {str(e)}")

        return user_session, browser_state

    def update_token_usage_display(self, user_session: UserSession) -> str:
        """
        トークン使用状況を表示用のHTMLとして返します。

        Returns:
            str: トークン使用状況のHTML
        """
        token_usage = user_session.text_processor.get_token_usage()
        if not token_usage:
            return "<div>トークン使用状況: データがありません</div>"

        prompt_tokens = token_usage.get("prompt_tokens", math.nan)
        completion_tokens = token_usage.get("completion_tokens", math.nan)
        total_tokens = token_usage.get("total_tokens", math.nan)

        # API名を取得
        api_name = f"{user_session.text_processor.current_api_type.display_name if user_session.text_processor.current_api_type else 'API'} API"

        html = f"""
        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px;">
            <h3 style="margin-top: 0; margin-bottom: 8px;">{api_name} Token Usage</h3>
            <div style="display: flex; justify-content: space-between;">
                <div><strong>Input Tokens:</strong> {prompt_tokens}</div>
                <div><strong>Output Tokens:</strong> {completion_tokens}</div>
                <div><strong>Total Tokens:</strong> {total_tokens}</div>
            </div>
        </div>
        """
        return html

    def update_audio_button_state(self, checked: bool, podcast_text: Optional[str] = None) -> Dict[str, Any]:
        """
        VOICEVOX利用規約チェックボックスの状態とトーク原稿の有無に基づいて音声生成ボタンの有効/無効を切り替えます。

        Args:
            checked (bool): チェックボックスの状態
            podcast_text (Optional[str], optional): 生成されたトーク原稿

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        has_text = bool(podcast_text and podcast_text.strip() != "")
        is_enabled = bool(checked and has_text)

        message = ""
        if not checked:
            message = "（VOICEVOX利用規約に同意が必要です）"
        elif not has_text:
            message = "（トーク原稿が必要です）"

        # Default button text
        button_text = "音声を生成"

        # gr.update()を使用して、既存のボタンを更新
        result: Dict[str, Any] = gr.update(
            value=f"{button_text}{message}",
            interactive=is_enabled,
            variant="primary" if is_enabled else "secondary",
        )
        return result

    def update_audio_button_state_with_browser_state(self, checked: bool, podcast_text: Optional[str], browser_state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Update audio button state and browser state."""
        button_update = self.update_audio_button_state(checked, podcast_text)

        # Update browser state with terms agreement and podcast text
        updated_browser_state = self.update_browser_state_ui_content(browser_state, podcast_text or "", checked)

        return button_update, updated_browser_state

    def update_audio_button_state_with_resume_check(self, checked: bool, podcast_text: Optional[str], user_session: UserSession, browser_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update audio button state with resume functionality check."""
        has_text = bool(podcast_text and podcast_text.strip() != "")
        is_enabled = bool(checked and has_text)

        message = ""
        button_text = "音声を生成"

        if not checked:
            message = "（VOICEVOX利用規約に同意が必要です）"
        elif not has_text:
            message = "（トーク原稿が必要です）"
        elif has_text and checked and user_session:
            # Check if we can resume (script unchanged)
            if browser_state:
                # Use browser_state for more reliable state management
                audio_state = browser_state.get("audio_generation_state", {})
                current_script = audio_state.get("current_script", "")
                has_streaming_parts = len(audio_state.get("streaming_parts", [])) > 0
                has_final_audio = audio_state.get("final_audio_path") is not None
                is_preparing = audio_state.get("status") == "preparing"

                # If script is unchanged, show appropriate state
                if current_script == podcast_text and current_script != "":
                    if has_final_audio:
                        # Audio generation is already completed - disable button
                        button_text = "音声生成完了済み"
                        is_enabled = False
                    elif has_streaming_parts or is_preparing:
                        button_text = "音声生成を再開"
                    else:
                        button_text = "音声生成を再開"
            else:
                # Fallback to legacy UserSession methods if browser_state not available
                audio_state = user_session.get_audio_generation_status()
                current_script = audio_state.get("current_script", "")

                # If script is unchanged and we have generated audio, show appropriate state
                if current_script == podcast_text and user_session.has_generated_audio():
                    # Check if audio generation is completed
                    if user_session.audio_generator.final_audio_path and os.path.exists(user_session.audio_generator.final_audio_path):
                        # Audio generation is already completed - disable button
                        button_text = "音声生成完了済み"
                        is_enabled = False
                    else:
                        button_text = "音声生成を再開"

        result: Dict[str, Any] = gr.update(
            value=f"{button_text}{message}",
            interactive=is_enabled,
            variant="primary" if is_enabled else "secondary",
        )
        return result

    def update_audio_button_state_with_resume_check_and_browser_state(
        self, checked: bool, podcast_text: Optional[str], user_session: UserSession, browser_state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Update audio button state with resume functionality check and browser state."""
        button_update = self.update_audio_button_state_with_resume_check(checked, podcast_text, user_session, browser_state)

        # Update browser state with terms agreement and podcast text
        updated_browser_state = self.update_browser_state_ui_content(browser_state, podcast_text or "", checked)

        return button_update, updated_browser_state

    def update_browser_state_extracted_text(self, extracted_text: str, browser_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update browser state with extracted text changes."""
        return self.update_browser_state_ui_content(browser_state, browser_state.get("podcast_text", ""), browser_state.get("terms_agreed", False), extracted_text)

    def set_document_type(self, doc_type: str, user_session: UserSession, browser_state: Dict[str, Any]) -> Tuple[UserSession, Dict[str, Any]]:
        """
        ドキュメントタイプを設定します。

        Args:
            doc_type (str): ドキュメントタイプのラベル名
            user_session (UserSession): ユーザーセッション
            browser_state (Dict[str, Any]): ブラウザ状態

        Returns:
            Tuple[UserSession, Dict[str, Any]]: 更新されたユーザーセッションとブラウザ状態
        """
        try:
            # ラベル名からDocumentTypeを取得
            document_type = DocumentType.from_label_name(doc_type)

            # TextProcessorを使ってドキュメントタイプを設定
            success = user_session.text_processor.set_document_type(document_type)

            if success:
                # browser_stateにドキュメントタイプを保存
                browser_state["user_settings"]["document_type"] = document_type.value
                logger.debug(f"Document type set to {doc_type}: {success}, saved to browser_state")
            else:
                logger.warning(f"Failed to set document type to {doc_type}")

            user_session.auto_save()  # Save session state after document type change

        except ValueError as e:
            logger.error(f"Error setting document type: {str(e)}")

        return user_session, browser_state

    def reset_audio_state_and_components(self, user_session: UserSession):
        """
        音声生成状態をリセットし、音声コンポーネントをクリアする

        Args:
            user_session: ユーザーセッション

        Returns:
            Tuple[None, str, None]: (streaming_audio_clear, progress_clear, audio_output_clear)
        """
        # 音声生成状態をリセット
        user_session.reset_audio_generation_state()
        logger.debug("Audio generation state and components reset")

        # 音声コンポーネントと進捗表示をクリア
        return None, "", None

    def reset_audio_state_and_components_with_browser_state(self, user_session: UserSession, browser_state: Dict[str, Any]) -> Tuple[None, str, None, Dict[str, Any]]:
        """Reset audio state and components with BrowserState synchronization."""
        # Preserve current_script for resume functionality
        current_script = browser_state["audio_generation_state"].get("current_script", "")

        # Reset audio state directly in browser state but preserve current_script
        browser_state["audio_generation_state"] = {
            "is_generating": False,
            "progress": 0.0,
            "status": "idle",
            "current_script": current_script,  # Preserve for resume detection
            "generated_parts": [],
            "final_audio_path": None,
            "streaming_parts": [],
            "generation_id": None,
            "start_time": None,
            "last_update": None,
            "estimated_total_parts": 1,
        }

        # Reset local user session state as well
        user_session.audio_generator.reset_audio_generation_state()

        logger.debug(f"Audio generation state reset in browser state and user session, preserved current_script: {current_script}")

        # Return clear values for UI components
        return None, "", None, browser_state

    def prepare_audio_generation_with_browser_state(self, podcast_text: str, user_session: UserSession, browser_state: Dict[str, Any]) -> Tuple[None, str, None, Dict[str, Any]]:
        """Prepare for audio generation by saving current script to browser state."""
        # Check if script has changed
        audio_state = browser_state.get("audio_generation_state", {})
        current_script = audio_state.get("current_script", "")
        script_changed = current_script != podcast_text

        if script_changed:
            logger.info("Script changed detected in prepare phase - will start from part 1")
            # Clear ALL audio generation state when script changes
            browser_state["audio_generation_state"]["streaming_parts"] = []
            browser_state["audio_generation_state"]["final_audio_path"] = None
            browser_state["audio_generation_state"]["generated_parts"] = []
            browser_state["audio_generation_state"]["estimated_total_parts"] = None
            # Set flag to indicate script changed (for use in resume function)
            browser_state["audio_generation_state"]["script_changed"] = True
        else:
            logger.info("Script unchanged - preserving existing state for potential resume")
            browser_state["audio_generation_state"]["script_changed"] = False

        # Save current script to browser state BEFORE starting generation
        # This ensures it's persisted to localStorage before streaming begins
        browser_state["audio_generation_state"]["current_script"] = podcast_text
        browser_state["audio_generation_state"]["status"] = "preparing"
        browser_state["audio_generation_state"]["is_generating"] = False
        browser_state["audio_generation_state"]["progress"] = 0.0
        browser_state["audio_generation_state"]["generation_id"] = None
        browser_state["audio_generation_state"]["start_time"] = None

        logger.debug(f"Audio generation prepared with script: {podcast_text[:50]}...")

        # Return clear values for UI components
        return None, "", None, browser_state

    def initialize_session_and_ui(
        self, request: gr.Request, browser_state: Dict[str, Any]
    ) -> Tuple[
        UserSession,  # user_session
        Dict[str, Any],  # browser_state
        str,
        str,
        str,
        str,
        int,
        int,  # UI sync values (document_type, podcast_mode, character1, character2, openai_max_tokens, gemini_max_tokens)
        Dict[str, Any],  # file_input
        Dict[str, Any],  # url_input
        Dict[str, Any],  # url_extract_btn
        Dict[str, Any],  # auto_separator_checkbox
        Dict[str, Any],  # clear_text_btn
        str,  # extracted_text (value)
        Dict[str, Any],  # document_type_radio
        Dict[str, Any],  # podcast_mode_radio
        Dict[str, Any],  # character1_dropdown
        Dict[str, Any],  # character2_dropdown
        Dict[str, Any],  # gemini_api_key_input
        Dict[str, Any],  # gemini_model_dropdown
        Dict[str, Any],  # gemini_max_tokens_slider
        Dict[str, Any],  # openai_api_key_input
        Dict[str, Any],  # openai_model_dropdown
        Dict[str, Any],  # openai_max_tokens_slider
        Dict[str, Any],  # process_btn
        str,  # podcast_text (value)
        bool,  # terms_checkbox (value)
        Optional[str],  # streaming_audio_output
        str,  # audio_progress
        Optional[str],  # audio_output
        Dict[str, Any],  # generate_btn
    ]:
        """Initialize user session and all UI components in one unified function.

        This replaces the complex .then() chain with a single function call.
        Includes session creation, UI synchronization, component enabling, and connection recovery.

        Args:
            request: Gradio request object
            browser_state: Browser state for session restoration

        Returns:
            Tuple containing user_session, browser_state, UI sync values, component updates, and recovery data
        """
        # Step 1: Create user session with browser state
        user_session, updated_browser_state = self.create_user_session_with_browser_state(request, browser_state)

        # Step 2: Get UI sync values from session
        document_type, podcast_mode, character1, character2, openai_max_tokens, gemini_max_tokens = user_session.get_ui_sync_values()

        # Step 3: Handle connection recovery and get UI restoration data from BrowserState
        ui_state = updated_browser_state.get("ui_state", {})
        restored_extracted_text = ui_state.get("extracted_text", "")
        restored_podcast_text = ui_state.get("podcast_text", "")
        restored_terms_agreed = ui_state.get("terms_agreed", False)

        # Restore streaming audio from browser state after page reload
        streaming_audio, progress_html = self.restore_streaming_audio_from_browser_state(updated_browser_state)

        # Update button state to include resume functionality with browser_state
        button_state = self.update_audio_button_state_with_resume_check(restored_terms_agreed, restored_podcast_text, user_session, updated_browser_state)

        # For final audio output, check browser state for the final audio path
        audio_state = updated_browser_state.get("audio_generation_state", {})
        final_audio = audio_state.get("final_audio_path")

        # Validate final audio file exists
        if final_audio and not os.path.exists(final_audio):
            logger.warning(f"Final audio file not found: {final_audio}")
            final_audio = None

        # If no final audio in browser state, search for completed audio files on disk
        if not final_audio:
            output_dir = user_session.get_output_dir()
            if output_dir.exists():
                # Look for audio_*.wav files (completed audio files)
                audio_files = list(output_dir.glob("audio_*.wav"))
                if audio_files:
                    # Get the most recent audio file
                    final_audio = str(max(audio_files, key=lambda p: p.stat().st_mtime))
                    logger.info(f"Found completed audio file on disk: {final_audio}")
                    # Update browser state with the found final audio
                    updated_browser_state["audio_generation_state"]["final_audio_path"] = final_audio
                    updated_browser_state["audio_generation_state"]["status"] = "completed"

        # Update BrowserState with current session status and UI content
        updated_browser_state = self.update_browser_state_audio_status(user_session, updated_browser_state)
        updated_browser_state = self.update_browser_state_ui_content(updated_browser_state, restored_podcast_text, restored_terms_agreed, restored_extracted_text)

        # Step 4: Create UI component updates (enable all components)
        logger.info(f"Enabling UI components for session {user_session.session_id}")
        logger.debug(f"UI sync values: document_type={document_type}, podcast_mode={podcast_mode}, character1={character1}, character2={character2}")
        logger.debug(f"Token values: openai_max_tokens={openai_max_tokens}, gemini_max_tokens={gemini_max_tokens}")

        # Enable file input
        file_input_update = gr.update(interactive=True)

        # Enable URL input - replace initialization placeholder
        url_input_update = gr.update(placeholder="https://example.com/page", interactive=True)

        # Enable URL extract button - replace initialization text
        url_extract_btn_update = gr.update(value="URLからテキストを抽出", variant="primary", interactive=True)

        # Enable auto separator checkbox
        auto_separator_checkbox_update = gr.update(interactive=True)

        # Enable clear text button
        clear_text_btn_update = gr.update(value="テキストをクリア", interactive=True)

        # Enable extracted text with restored value and interactive state
        # Set appropriate placeholder based on whether we have restored content
        extracted_placeholder = "" if restored_extracted_text and restored_extracted_text.strip() else "ファイルまたはURLから抽出されたテキストがここに表示されます。"
        extracted_text_update = gr.update(value=restored_extracted_text, placeholder=extracted_placeholder, interactive=True)

        # Enable document type radio with session value
        document_type_radio_update = gr.update(value=document_type, interactive=True)

        # Enable podcast mode radio with session value
        podcast_mode_radio_update = gr.update(value=podcast_mode, interactive=True)

        # Enable character dropdowns with session values
        character1_dropdown_update = gr.update(value=character1, interactive=True)
        character2_dropdown_update = gr.update(value=character2, interactive=True)

        # Enable API key inputs
        gemini_api_key_input_update = gr.update(placeholder="AIza...", interactive=True)
        openai_api_key_input_update = gr.update(placeholder="sk-...", interactive=True)

        # Enable model dropdowns
        gemini_model_dropdown_update = gr.update(interactive=True)
        openai_model_dropdown_update = gr.update(interactive=True)

        # Enable token sliders with session values
        gemini_max_tokens_slider_update = gr.update(value=gemini_max_tokens, interactive=True)
        openai_max_tokens_slider_update = gr.update(value=openai_max_tokens, interactive=True)

        # Enable process button - replace initialization text (but keep disabled until API key is set)
        process_btn_update = gr.update(interactive=False, variant="secondary", value="トーク原稿を生成")

        # Enable podcast text with restored value and interactive state
        # Set appropriate placeholder based on whether we have restored content
        podcast_placeholder = "" if restored_podcast_text and restored_podcast_text.strip() else "「トーク原稿を生成」ボタンを押すと、ここにトーク原稿が生成されます。直接編集することも可能です。"
        podcast_text_update = gr.update(value=restored_podcast_text, placeholder=podcast_placeholder, interactive=True)

        # Enable terms checkbox with restored value and interactive state
        terms_checkbox_update = gr.update(value=restored_terms_agreed, interactive=True)

        # Enable generate button with proper state
        generate_btn_update = gr.update(**button_state)

        return (
            user_session,
            updated_browser_state,
            document_type,
            podcast_mode,
            character1,
            character2,
            openai_max_tokens,
            gemini_max_tokens,
            file_input_update,
            url_input_update,
            url_extract_btn_update,
            auto_separator_checkbox_update,
            clear_text_btn_update,
            extracted_text_update,
            document_type_radio_update,
            podcast_mode_radio_update,
            character1_dropdown_update,
            character2_dropdown_update,
            gemini_api_key_input_update,
            gemini_model_dropdown_update,
            gemini_max_tokens_slider_update,
            openai_api_key_input_update,
            openai_model_dropdown_update,
            openai_max_tokens_slider_update,
            process_btn_update,
            podcast_text_update,
            terms_checkbox_update,
            streaming_audio,
            progress_html,
            final_audio,
            generate_btn_update,
        )

    def handle_connection_recovery(self, user_session: UserSession, terms_agreed: bool, podcast_text: str) -> Tuple[Optional[str], str, Optional[str], Dict[str, Any]]:
        """
        Handle connection recovery when page loads/reconnects with enhanced recovery support.
        Combines audio state restoration and button state management.

        Args:
            user_session: User session
            terms_agreed: Whether VOICEVOX terms are agreed
            podcast_text: Generated podcast text

        Returns:
            Tuple[Optional[str], str, Optional[str], Dict[str, Any]]:
                (streaming_audio, progress_html, final_audio, button_update)
        """
        logger.info("Enhanced connection recovery triggered - checking audio state")

        try:
            # Get recovery progress information from UserSession
            recovery_info = user_session.get_recovery_progress_info()

            # Check if there's any audio to restore
            if not recovery_info["is_active"] and not user_session.has_generated_audio():
                logger.debug("No audio to restore - setting normal button state")
                return (
                    None,
                    "",
                    None,
                    self.update_audio_button_state(terms_agreed, podcast_text),
                )

            # Determine status message based on recovery state (without emoji prefix to avoid duplication)
            status = recovery_info["status"]
            if status == "completed":
                status_message = "音声生成完了（復帰）"
            elif status == "partial":
                status_message = "音声生成部分完了（復帰）"
            elif status == "generating":
                progress_percent = int(recovery_info["progress"] * 100)
                status_message = f"音声生成中... {progress_percent}%（復帰）"
            elif status == "failed":
                status_message = "音声生成エラー（復帰）"
            else:
                status_message = "音声生成準備中...（復帰）"

            # Get audio file paths from session state
            audio_state = user_session.get_audio_generation_status()
            streaming_parts = audio_state.get("streaming_parts", [])
            final_audio_path = audio_state.get("final_audio_path")

            # For streaming UI, prioritize final audio over streaming parts to show complete audio
            # If final audio is available, use it for streaming playback to show complete result
            streaming_audio = final_audio_path if final_audio_path and os.path.exists(final_audio_path) else streaming_parts[-1] if streaming_parts else None

            # For final audio component, always use final audio path
            final_audio = final_audio_path

            logger.info(f"Audio state restored - Status: {status}, Streaming parts: {len(streaming_parts)}, Final audio: {bool(final_audio)}")

            # If audio generation is still active, show active progress
            if recovery_info["is_active"]:
                logger.debug("Audio generation active - showing active recovery state")
                progress_html = self._create_recovery_progress_html(user_session, status_message, is_active=True)
                return (
                    streaming_audio,
                    progress_html,
                    final_audio,
                    gr.update(interactive=False, value="音声生成中...（復帰）"),
                )
            else:
                # Audio generation completed or failed - restore final state
                button_state = self.update_audio_button_state(terms_agreed, podcast_text)
                progress_html = self._create_recovery_progress_html(user_session, status_message, is_active=False)
                return (streaming_audio, progress_html, final_audio, button_state)

        except Exception as e:
            logger.error(f"Error in BrowserState connection recovery: {e}")
            return (
                None,
                "",
                None,
                self.update_audio_button_state(terms_agreed, podcast_text),
            )


def main() -> None:
    """
    Main function to launch the Gradio app.

    This function creates an instance of PaperPodcastApp and launches
    the Gradio interface with appropriate configuration.
    """
    import argparse

    # Get port from environment variable if available
    env_port = os.environ.get("PORT")
    default_port = int(env_port) if env_port else DEFAULT_PORT

    parser = argparse.ArgumentParser(description="Yomitalk - Paper Podcast Generator")
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to run the server on (default: {default_port})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on (default: 0.0.0.0)",
    )
    parser.add_argument("--share", action="store_true", help="Create a public link via Gradio tunneling")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Initialize the application
    app_instance = PaperPodcastApp()
    gradio_app = app_instance.ui()

    # Launch configuration
    launch_kwargs = {
        "server_name": args.host,
        "server_port": args.port,
        "share": args.share,
        "debug": args.debug,
        "show_error": True,
        "quiet": not args.debug,
        "favicon_path": ("assets/favicon.ico" if Path("assets/favicon.ico").exists() else None),
    }

    # Add authentication for production environment
    if not args.debug and not E2E_TEST_MODE:
        # In production, you might want to add authentication
        # auth = ("username", "password")  # Set your credentials
        # launch_kwargs["auth"] = auth
        pass

    # Special handling for E2E test mode
    if E2E_TEST_MODE:
        logger.info("Running in E2E test mode - using special configuration")
        launch_kwargs.update(
            {
                "prevent_thread_lock": False,  # Keep app running for E2E tests
                "show_error": True,  # Show errors in test mode for debugging
                "quiet": False,  # Show output in test mode for debugging
            }
        )

    logger.info(f"Starting Yomitalk application on http://{args.host}:{args.port}")
    if args.share:
        logger.info("Public sharing enabled - this will create a public URL")

    try:
        gradio_app.launch(**launch_kwargs)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
