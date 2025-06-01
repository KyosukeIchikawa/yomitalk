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

  Scenario: Combining file and URL content with separators
    Given the user has accessed the application page
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    And the user enters "https://example.com" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area contains content from both sources
    And the extracted text area contains source information for "sample_text.txt"
    And the extracted text area contains source information for "https://example.com"

  Scenario: Manual text input preserved during extractions
    Given the user has accessed the application page
    And the user has entered "Manual input content" into the extracted text area
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    Then the extracted text area contains "Manual input content"
    And the extracted text area contains content from the file
