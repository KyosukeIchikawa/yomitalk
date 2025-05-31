Feature: VOICEVOX Core Sharing Across Users
  As a system administrator
  I want VOICEVOX Core to be shared efficiently across multiple users
  So that server resources are optimized and initialization time is reduced

  Background:
    Given the global VOICEVOX Core manager is initialized
    And VOICEVOX Core is available

  Scenario: Global VOICEVOX manager initialization
    When the application starts
    Then the global VOICEVOX Core manager should be initialized once
    And all required voice models should be loaded
    And the manager should be available for all users

  Scenario: Multiple user sessions share the same VOICEVOX Core
    Given multiple user sessions are created
    When each session checks VOICEVOX availability
    Then all sessions should report VOICEVOX as available
    And all sessions should use the same global VOICEVOX instance
    And no duplicate VOICEVOX initialization should occur

  @backend_only
  Scenario: Audio generation through shared VOICEVOX Core
    Given a user session with access to shared VOICEVOX
    When the user generates audio from text "こんにちは、テストです"
    Then audio should be generated successfully
    And the audio file should be created
    And the shared VOICEVOX Core should handle the request

  Scenario: Concurrent audio generation by multiple users
    Given multiple user sessions are active
    When all users simultaneously generate audio from different texts
    Then all audio generation requests should succeed
    And each user should receive their own audio file
    And the shared VOICEVOX Core should handle all requests efficiently

  Scenario: VOICEVOX Core resource management
    Given the global VOICEVOX manager is running
    When checking resource usage
    Then only one VOICEVOX Core instance should exist
    And voice models should be loaded only once
    And memory usage should be optimized for multiple users

  Scenario: Session cleanup does not affect shared VOICEVOX
    Given multiple user sessions are using shared VOICEVOX
    When one user session is cleaned up
    Then the shared VOICEVOX Core should remain available
    And other user sessions should continue to work normally
    And no VOICEVOX reinitialization should occur
