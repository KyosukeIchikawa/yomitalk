# language: en
Feature: URL extraction functionality
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

  Scenario: Both file upload and URL extraction display in the same text area
    Given the user has accessed the application page
    When the user enters "https://example.com" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows content
    When the user uploads a text file
    Then the extracted text area content is replaced with file content
