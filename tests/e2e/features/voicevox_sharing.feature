Feature: VOICEVOX Core Sharing Across Users
  As a system administrator
  I want VOICEVOX Core to be shared efficiently across multiple users
  So that server resources are optimized and initialization time is reduced

  Background:
    Given the global VOICEVOX Core manager is initialized
    And VOICEVOX Core is available

  Scenario: VOICEVOX Core shared across multiple users
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
