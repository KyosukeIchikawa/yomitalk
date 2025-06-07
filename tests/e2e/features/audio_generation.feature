Feature: Audio Generation
  As a user
  I want to generate audio from a podcast script
  So that I can listen to the content

  Background:
    Given the application is running
    And a podcast script has been generated
    And I have agreed to the VOICEVOX terms of service

  Scenario: Generating audio from script
    When I click the "音声を生成" button
    Then audio should be generated
    And an audio player should be displayed

  Scenario: Audio progress is displayed during generation
    When I click the "音声を生成" button
    Then audio generation progress should be visible
    And progress information should update during generation
    And final audio should be displayed when complete
