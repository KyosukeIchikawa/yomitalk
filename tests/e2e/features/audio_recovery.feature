Feature: Audio Generation Recovery
  As a user
  I want audio generation to resume after connection interruption
  So that I don't lose my audio generation progress

  Background:
    Given the application is running
    And a podcast script has been generated
    And I have agreed to the VOICEVOX terms of service

  Scenario: Audio generation resumes after connection interruption
    Given audio generation was interrupted and reconnected
    Then audio generation should resume after reconnection
    And streaming audio should be restored
    And final audio should be restored

  Scenario: Audio state is preserved across sessions
    When I click the "音声を生成" button
    And I wait for audio generation to start
    And I simulate connection interruption
    And I reconnect to the application
    Then audio generation should resume from where it left off
    And audio components should be restored to their previous state
