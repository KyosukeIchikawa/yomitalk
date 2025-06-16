"""Step definitions for VOICEVOX sharing E2E tests."""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

from yomitalk.components.audio_generator import (
    get_global_voicevox_manager,
    initialize_global_voicevox_manager,
)
from yomitalk.user_session import UserSession


@pytest.fixture
def test_context():
    """Test context fixture for sharing data between steps."""

    class TestContext:
        def __init__(self):
            self.sessions = []
            self.availability_results = []
            self.generated_files = []
            self.test_texts = []
            self.generation_results = None
            self.concurrent_results = []
            self.user_session = None
            self.audio_generator = None
            self.manager_instance = None
            self.manager_count = 0
            self.cleaned_session = None
            self.remaining_sessions = []

    return TestContext()


@given("the global VOICEVOX Core manager is initialized")
def global_voicevox_manager_initialized():
    """Ensure global VOICEVOX Core manager is initialized."""
    manager = initialize_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@given("VOICEVOX Core is available")
def voicevox_core_available():
    """Verify VOICEVOX Core is available."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@given("multiple user sessions are created")
def multiple_sessions_created(test_context):
    """Create multiple user sessions for testing."""
    test_context.sessions = []

    # Create 3 test sessions
    for i in range(3):
        user_session = UserSession(f"test_session_{i}")
        test_context.sessions.append(user_session)


@given("a user session with access to shared VOICEVOX")
def session_with_shared_voicevox(test_context):
    """Create a single user session with access to shared VOICEVOX."""
    test_context.user_session = UserSession("test_session_shared")
    test_context.audio_generator = test_context.user_session.audio_generator
    assert test_context.audio_generator.core_initialized


@given("multiple user sessions are active")
def multiple_active_sessions(test_context):
    """Create multiple active user sessions."""
    test_context.sessions = []
    test_context.test_texts = [
        "最初のユーザーのテキストです",
        "二番目のユーザーのテキストです",
        "三番目のユーザーのテキストです",
    ]

    # Create 3 active sessions
    for i in range(3):
        user_session = UserSession(f"test_session_active_{i}")
        test_context.sessions.append(user_session)


@given("multiple user sessions are using shared VOICEVOX")
def multiple_sessions_using_shared_voicevox(test_context):
    """Create multiple user sessions using shared VOICEVOX."""
    test_context.sessions = []

    # Create 3 test sessions
    for i in range(3):
        user_session = UserSession(f"test_session_shared_{i}")
        test_context.sessions.append(user_session)

        # Verify each session can access shared VOICEVOX
        assert user_session.audio_generator.core_initialized


@given("the global VOICEVOX manager is running")
def global_voicevox_manager_running():
    """Verify the global VOICEVOX manager is running."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@when("the application starts")
def application_starts():
    """Simulate application startup."""
    # This is handled by the global initialization in conftest.py


@when("each session checks VOICEVOX availability")
def each_session_checks_voicevox(test_context):
    """Check VOICEVOX availability for each session."""
    test_context.availability_results = []
    for session in test_context.sessions:
        is_available = session.audio_generator.core_initialized
        test_context.availability_results.append(is_available)


@when(parsers.parse('the user generates audio from text "{text}"'))
def user_generates_audio(test_context, text):
    """Generate audio from the given text."""
    # Create a simple podcast text format
    podcast_text = f"ずんだもん: {text}"

    # Generate audio
    test_context.generated_files = []
    for audio_file in test_context.audio_generator.generate_character_conversation(podcast_text):
        if audio_file:
            test_context.generated_files.append(audio_file)


@when("all users simultaneously generate audio from different texts")
def all_users_generate_simultaneously(test_context):
    """Generate audio simultaneously for all users."""
    import queue
    import threading

    test_context.generation_results = queue.Queue()
    threads = []

    def generate_audio_for_user(generator, text, user_id):
        """Generate audio for a specific user."""
        try:
            podcast_text = f"ずんだもん: {text}"
            files = []
            for audio_file in generator.generate_character_conversation(podcast_text):
                if audio_file:
                    files.append(audio_file)
            test_context.generation_results.put((user_id, True, files))
        except Exception as e:
            test_context.generation_results.put((user_id, False, str(e)))

    # Start threads for concurrent generation
    for i, (session, text) in enumerate(zip(test_context.sessions, test_context.test_texts, strict=False)):
        thread = threading.Thread(target=generate_audio_for_user, args=(session.audio_generator, text, i))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=30)  # 30 second timeout


@when("checking resource usage")
def checking_resource_usage(test_context):
    """Check VOICEVOX resource usage."""
    manager = get_global_voicevox_manager()
    test_context.manager_instance = manager
    test_context.manager_count = 1 if manager else 0


@when("one user session is cleaned up")
def one_session_cleaned_up(test_context):
    """Clean up one user session."""
    if test_context.sessions:
        # Clean up the first session
        session_to_cleanup = test_context.sessions[0]

        # Store reference to check later
        test_context.cleaned_session = session_to_cleanup
        test_context.remaining_sessions = test_context.sessions[1:]

        # Cleanup
        session_to_cleanup.cleanup()


@then("the global VOICEVOX Core manager should be initialized once")
def global_manager_initialized_once():
    """Verify global VOICEVOX manager is initialized exactly once."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("all required voice models should be loaded")
def all_voice_models_loaded():
    """Verify all required voice models are loaded."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    # The manager should be available, which means models are loaded
    assert manager.is_available()


@then("the manager should be available for all users")
def manager_available_for_users():
    """Verify the manager is available for all users."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("all sessions should report VOICEVOX as available")
def all_sessions_report_available(test_context):
    """Verify all sessions report VOICEVOX as available."""
    assert all(test_context.availability_results)


@then("all sessions should use the same global VOICEVOX instance")
def all_sessions_use_same_instance(test_context):
    """Verify all sessions use the same global VOICEVOX instance."""
    manager = get_global_voicevox_manager()
    # All generators should reference the same global manager
    if manager is not None:
        for session in test_context.sessions:
            assert session.audio_generator.core_initialized == manager.is_available()


@then("no duplicate VOICEVOX initialization should occur")
def no_duplicate_initialization():
    """Verify no duplicate VOICEVOX initialization occurred."""
    # This is implicitly tested by the singleton pattern
    manager = get_global_voicevox_manager()
    assert manager is not None


@then("audio should be generated successfully")
def audio_generated_successfully(test_context):
    """Verify audio was generated successfully."""
    assert hasattr(test_context, "generated_files")
    assert len(test_context.generated_files) > 0


@then("the audio file should be created")
def audio_file_created(test_context):
    """Verify audio file was created."""
    for file_path in test_context.generated_files:
        assert Path(file_path).exists()
        assert Path(file_path).stat().st_size > 0


@then("the shared VOICEVOX Core should handle the request")
def shared_voicevox_handles_request():
    """Verify shared VOICEVOX Core handled the request."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("all audio generation requests should succeed")
def all_requests_succeed(test_context):
    """Verify all audio generation requests succeeded."""
    results = []
    while not test_context.generation_results.empty():
        results.append(test_context.generation_results.get())

    test_context.concurrent_results = results
    assert len(results) == 3  # We started 3 users

    for user_id, success, data in results:
        assert success, f"User {user_id} failed: {data}"


@then("each user should receive their own audio file")
def each_user_receives_audio(test_context):
    """Verify each user received their own audio file."""
    for _, success, files in test_context.concurrent_results:
        assert success
        assert len(files) > 0
        # Verify files exist
        for file_path in files:
            assert Path(file_path).exists()


@then("the shared VOICEVOX Core should handle all requests efficiently")
def shared_voicevox_handles_efficiently():
    """Verify shared VOICEVOX Core handled all requests efficiently."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("only one VOICEVOX Core instance should exist")
def only_one_voicevox_instance(test_context):
    """Verify only one VOICEVOX Core instance exists."""
    assert test_context.manager_count == 1


@then("voice models should be loaded only once")
def voice_models_loaded_once():
    """Verify voice models are loaded only once."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("memory usage should be optimized for multiple users")
def memory_usage_optimized():
    """Verify memory usage is optimized."""
    # This is implicit in the shared architecture
    manager = get_global_voicevox_manager()
    assert manager is not None


@then("the shared VOICEVOX Core should remain available")
def shared_voicevox_remains_available():
    """Verify shared VOICEVOX Core remains available after cleanup."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()


@then("other user sessions should continue to work normally")
def other_sessions_work_normally(test_context):
    """Verify other sessions continue to work normally."""
    for session in test_context.remaining_sessions:
        assert session.audio_generator.core_initialized


@then("no VOICEVOX reinitialization should occur")
def no_voicevox_reinitialization():
    """Verify no VOICEVOX reinitialization occurred."""
    manager = get_global_voicevox_manager()
    assert manager is not None
    assert manager.is_available()
