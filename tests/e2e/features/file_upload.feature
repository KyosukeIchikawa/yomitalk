Feature: File Upload Functionality
  As a user
  I want to upload files for processing
  So that I can provide content to the application

  Background:
    Given the application is running

  Scenario: Uploading a PDF file
    When I upload a PDF file "sample_paper.pdf"
    Then text should be extracted
    And the "トーク原稿を生成" button should be active

  Scenario: Uploading a text file
    When I upload a text file "sample_text.txt"
    Then text should be extracted
    And the "トーク原稿を生成" button should be active
