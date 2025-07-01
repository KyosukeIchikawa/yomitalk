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

  Scenario: Document type and podcast mode changes are persisted in browser state
    Given I have accessed the application page
    When I change the document type to "Blog Post"
    And I change the podcast mode to "Conversational"
    And I close and reopen the browser
    Then the document type should be restored to "Blog Post"
    And the podcast mode should be restored to "Conversational"
    And the settings should be saved in browser state

  Scenario: Multiple setting changes are persisted together
    Given I have accessed the application page
    When I change the document type to "Research Paper"
    And I change the podcast mode to "Academic"
    And I change the character settings to "Zundamon" and "Kyushu Sora"
    And I simulate a page refresh
    Then all my settings should be restored correctly
    And the document type should be "Research Paper"
    And the podcast mode should be "Academic"
    And the characters should be "Zundamon" and "Kyushu Sora"

  Scenario: Setting changes trigger browser state updates immediately
    Given I have accessed the application page
    When I change the document type to "News Article"
    Then the browser state should be updated immediately
    And the user_settings should contain the new document type
    When I change the podcast mode to "News Style"
    Then the browser state should be updated immediately
    And the user_settings should contain the new podcast mode
