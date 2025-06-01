Feature: File Upload Functionality
  As a user
  I want to upload files for processing
  So that I can provide content to the application

  Background:
    Given the application is running

  Scenario: Uploading a PDF file with extraction button
    Given the user has accessed the application page
    When the user uploads a PDF file "sample_paper.pdf"
    And the user clicks the "ファイルからテキストを抽出" button
    Then text should be extracted
    And the file input should be cleared
    And the "トーク原稿を生成" button should be active

  Scenario: Uploading a text file with extraction button
    Given the user has accessed the application page
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    Then text should be extracted
    And the file input should be cleared
    And the "トーク原稿を生成" button should be active

  Scenario: File extraction appends to existing text with separator
    Given the user has accessed the application page
    And the user has entered "Existing content" into the extracted text area
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    Then text should be extracted with source separator
    And the extracted text area contains "Existing content"
    And the extracted text area contains source information for "sample_text.txt"

  Scenario: File extraction without automatic separator
    Given the user has accessed the application page
    And the user unchecks the "追加時に自動で区切りを挿入" checkbox
    And the user has entered "Existing content" into the extracted text area
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    Then text should be extracted without separator
    And the extracted text area contains "Existing content"

  Scenario: Multiple file extractions accumulate content
    Given the user has accessed the application page
    When the user uploads a text file "sample_text.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    And the user uploads a text file "another_file.txt"
    And the user clicks the "ファイルからテキストを抽出" button
    Then the extracted text area contains content from both files
    And the extracted text area contains source information for "sample_text.txt"
    And the extracted text area contains source information for "another_file.txt"
