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
    And the user clicks the save button
    Then the API key is saved

  Scenario: Podcast text generation
    Given text has been extracted from a PDF
    And a valid API key has been configured
    When the user clicks the text generation button
    Then podcast-style text is generated

  Scenario: Prompt template editing
    Given the user has opened the application
    When the user opens the prompt template settings section
    And the user edits the prompt template
    And the user clicks the save prompt button
    Then the prompt template is saved

  Scenario: Podcast generation with custom prompt
    Given text has been extracted from a PDF
    And a valid API key has been configured
    And a custom prompt template has been saved
    When the user clicks the text generation button
    Then podcast-style text is generated using the custom prompt

  @requires_voicevox
  Scenario: Audio generation
    Given podcast text has been generated
    When the user clicks the audio generation button
    Then an audio file is generated
    And an audio player is displayed
