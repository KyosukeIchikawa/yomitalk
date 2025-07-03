# language: en
Feature: URL extraction functionality
  As a user
  I want to extract text from URLs
  So that I can add web content to my podcast generation

  Background:
    Given the application is running

  Scenario: Extract text from a valid URL
    Given the user has accessed the application page
    When the user clicks on the "Webページ抽出" tab
    And the user enters "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows content
    And the "トーク原稿を生成" button is enabled

  Scenario: Enter an invalid URL
    Given the user has accessed the application page
    When the user clicks on the "Webページ抽出" tab
    And the user enters "invalid-url" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows an error message
    And the "トーク原稿を生成" button remains disabled

  Scenario: URL extraction with separator functionality
    Given the user has accessed the application page
    And the user has entered "Existing content" into the extracted text area
    When the user clicks on the "Webページ抽出" tab
    And the user enters "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md" into the URL input field
    And the user clicks the "URLからテキストを抽出" button
    Then the extracted text area shows content with source separator
    And the extracted text area contains "Existing content"
    And the extracted text area contains source information for "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
