# language: en
Feature: Text Management Functionality
  As a user
  I want to manage extracted text content
  So that I can control how content is combined and organized

  Background:
    Given the application is running

  Scenario: Clear text using clear button
    Given the user has accessed the application page
    And the user has entered "Some test content" into the extracted text area
    When the user clicks the "テキストをクリア" button
    Then the extracted text area is empty

  Scenario: Toggle automatic separator insertion
    Given the user has accessed the application page
    When the user unchecks the "追加時に自動で区切りを挿入" checkbox
    Then the automatic separator is disabled
    When the user checks the "追加時に自動で区切りを挿入" checkbox
    Then the automatic separator is enabled
