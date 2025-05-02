# language: en
Feature: Template Management for Podcast Generation
  Users can select and customize templates
  to control the format of the generated podcast

  Background:
    Given the user has opened the application

  Scenario: Select a template
    Given the user has opened the application
    When the user opens the template settings
    And the user selects the "technical.j2" template
    And the user saves the template settings
    Then the selected template is applied

  Scenario: Customize a template
    Given the user has opened the application
    When the user opens the template settings
    And the user enters a custom template
    And the user saves the template settings
    Then the custom template is applied

  Scenario: Podcast generation with custom template
    Given text has been extracted from a PDF
    And a valid API key has been configured
    And a custom template has been applied
    When the user clicks the text generation button
    Then podcast-style text is generated using the custom template

  Scenario: Reset template to default
    Given the user has opened the application
    When the user opens the template settings
    And the user has a custom template
    And the user clicks the reset template button
    Then the default template is restored

  Scenario: Template validation
    Given the user has opened the application
    When the user opens the template settings
    And the user enters an invalid template
    And the user tries to save the template settings
    Then an error message about invalid template is displayed
