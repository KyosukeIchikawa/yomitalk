# language: en
Feature: Generate podcast from research paper PDF
  Users can upload research paper PDFs,
  extract text, generate summaries,
  and create podcast-style audio

  Background:
    Given the user has opened the application

  Scenario: PDF upload and text extraction
    Given a sample PDF file is available
    When the user uploads a PDF file
    And the user clicks the extract text button
    Then the extracted text is displayed

  Scenario: API settings
    Given the user has opened the application
    When the user opens the OpenAI API settings section
    And the user enters a valid API key
    Then the API key is saved

  Scenario: OpenAI model selection
    Given the user has opened the application
    When the user opens the OpenAI API settings section
    And the user selects a different OpenAI model
    Then the selected model is saved

  Scenario: Max tokens configuration
    Given the user has opened the application
    When the user opens the OpenAI API settings section
    And the user adjusts the max tokens slider to 2000
    Then the max tokens value is saved

  Scenario: Podcast text generation
    Given text has been extracted from a PDF
    And a valid API key has been configured
    When the user clicks the text generation button
    Then podcast-style text is generated

  Scenario: Podcast generation with characters
    Given text has been extracted from a PDF
    And a valid API key has been configured
    When the user clicks the text generation button
    Then podcast-style text is generated with characters

  Scenario: Podcast generation with custom max tokens
    Given text has been extracted from a PDF
    And a valid API key has been configured
    And the user has set max tokens to 4000
    When the user clicks the text generation button
    Then podcast-style text is generated with appropriate length

  Scenario: Editing extracted text before generation
    Given text has been extracted from a PDF
    And a valid API key has been configured
    When the user edits the extracted text
    And the user clicks the text generation button
    Then podcast-style text is generated with the edited content

  Scenario: Podcast mode selection
    Given the user has opened the application
    When the user selects "セクション解説モード" as the podcast mode
    Then the podcast mode is changed to "セクション解説モード"

  Scenario: Section-by-Section podcast generation
    Given text has been extracted from a PDF
    And a valid API key has been configured
    When the user selects "セクション解説モード" as the podcast mode
    And the user clicks the text generation button
    Then podcast-style text is generated with section-by-section format

  @requires_voicevox
  Scenario: Audio generation
    Given podcast text has been generated
    When the user checks the terms of service checkbox
    And the user clicks the audio generation button
    Then an audio file is generated
    And an audio player is displayed

  Scenario: Terms of service agreement
    Given podcast text has been generated
    When the user views the terms of service checkbox
    Then the "音声を生成" button should be disabled
    When the user checks the terms of service checkbox
    Then the "音声を生成" button should be enabled
    When the user unchecks the terms of service checkbox
    Then the "音声を生成" button should be disabled
