Feature: Session Recovery
  As a user
  I want my session to be recovered after network disconnections or browser reloads
  So that I don't lose my work and can continue where I left off

  Background:
    Given the application is running
    And I wait for the interface to be ready

  Scenario: Recover script content and checkbox state after browser reload
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    When I reload the browser page
    Then my extracted text should be restored
    And my podcast script should be restored
    And my VOICEVOX terms agreement should be restored
    And the audio generation button should show the correct state

  Scenario: Recover audio generation state after connection loss during generation
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    And I start audio generation
    When I simulate a connection loss during audio generation
    And I reconnect to the application
    Then my streaming audio UI should show the combined final audio
    And my completed audio UI should show the final audio if generation completed
    And the progress information should be restored correctly

  Scenario: Resume audio generation when script is unchanged
    Given I have extracted some text content
    And I have generated a podcast script
    And I have completed audio generation successfully
    When I reload the browser page
    Then my session should be recovered
    And the audio generation button should show "音声生成を再開"
    When I click the audio generation button
    Then the existing audio should be available immediately

  Scenario: Show normal generation when script has changed
    Given I have extracted some text content
    And I have generated a podcast script
    And I have completed audio generation successfully
    When I modify the podcast script
    Then the audio generation button should show "音声を生成"
    And not show the resume option

  Scenario: Recover streaming parts when final audio is not available
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    And I start audio generation
    And some audio parts have been generated but not combined
    When I reload the browser page
    Then my streaming audio UI should show the last generated part
    And the progress should reflect partial completion

  Scenario: Persist UI state across multiple browser reloads
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    When I reload the browser page multiple times
    Then my extracted text should be consistently restored
    And my podcast script should be consistently restored
    And my VOICEVOX terms agreement should be consistently restored
    And the session should work correctly after multiple reloads

  Scenario: Recover state when session hash changes
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    When the browser session hash changes
    Then my session data should be migrated to the new session
    And my extracted text should be restored
    And my podcast script should be restored
    And my VOICEVOX terms agreement should be restored

  Scenario: Handle recovery when browser storage is corrupted
    Given I have extracted some text content
    And I have generated a podcast script
    And I have agreed to the VOICEVOX terms
    When the browser storage becomes corrupted
    And I reload the browser page
    Then the application should start with clean state
    And the UI should be functional for new content
    And no errors should be displayed to the user
