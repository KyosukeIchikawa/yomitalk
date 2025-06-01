# language: en
Feature: URL extraction functionality
  As a user
  I want to extract text from URLs
  So that I can add web content to my podcast generation

  Background:
    Given the application is running

  Scenario: Extract text from a valid URL
    Given the user has accessed the application page
    When the user enters "https://example.com" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows content
    And the "トーク原稿を生成" button is enabled

  Scenario: Enter an invalid URL
    Given the user has accessed the application page
    When the user enters "invalid-url" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows an error message
    And the "トーク原稿を生成" button remains disabled

  Scenario: Extract text from GitHub README URL
    Given the user has accessed the application page
    When the user enters a GitHub README URL into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows GitHub README content

  Scenario: Click extract button with empty URL field
    Given the user has accessed the application page
    When the user leaves the URL input field empty
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows an error message

  Scenario: URL extraction appends to existing text with separator
    Given the user has accessed the application page
    And the user has entered "Existing content" into the extracted text area
    When the user enters "https://example.com" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows content with source separator
    And the extracted text area contains "Existing content"
    And the extracted text area contains source information for "https://example.com"

  Scenario: URL extraction without automatic separator
    Given the user has accessed the application page
    And the user unchecks the "追加時に自動で区切りを挿入" checkbox
    And the user has entered "Existing content" into the extracted text area
    When the user enters "https://example.com" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows appended content without separator
    And the extracted text area contains "Existing content"

  Scenario: Clear extracted text using clear button
    Given the user has accessed the application page
    And the user has entered "Some text content" into the extracted text area
    When the user clicks the "テキストをクリア" button
    Then the extracted text area is empty
