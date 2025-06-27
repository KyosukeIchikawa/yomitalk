Feature: Browser State Restoration
  As a user
  I want my session to be restored using browser local storage
  So that I can continue my work even when the connection changes

  Background:
    Given the application is running
    And I have generated some content in my session

  Scenario: Session restored from browser state after reconnection
    When I simulate a connection change that generates a new session hash
    Then my session should be restored from browser local storage
    And my previous session data should be available
    And my audio generation state should be preserved

  Scenario: Browser state persists user preferences
    Given I have configured my API settings and character preferences
    When I close and reopen the browser
    Then my API configuration should be restored (except keys for security)
    And my character preferences should be restored
    And my document type settings should be restored

  Scenario: Browser state handles multiple session transitions
    Given I have an active session with some generated content
    When I experience multiple connection changes
    Then the latest browser state should always be used for restoration
    And session data should be properly migrated between session IDs
    And no duplicate session directories should be created
