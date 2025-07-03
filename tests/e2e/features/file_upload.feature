Feature: File Upload Functionality
  As a user
  I want to upload files for processing
  So that I can provide content to the application

  Background:
    Given the application is running

  Scenario: Uploading a PDF file in file upload tab
    Given the user has accessed the application page
    When the user clicks on the "ファイルアップロード" tab
    And the user uploads a PDF file "sample_paper.pdf"
    Then text should be extracted
    And the file input should be cleared
    And the "トーク原稿を生成" button should be active

  Scenario: File extraction with separator and content accumulation
    Given the user has accessed the application page
    And the user has entered "Existing content" into the extracted text area
    When the user clicks on the "ファイルアップロード" tab
    And the user uploads a text file "sample_text.txt"
    Then text should be extracted with source separator
    And the extracted text area contains "Existing content"
    And the extracted text area contains source information for "sample_text.txt"
    And the file input should be cleared
