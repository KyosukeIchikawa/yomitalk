Feature: Podcast Script Generation
  As a user
  I want to generate a podcast script from input text
  So that I can convert the content to audio

  Background:
    Given the application is running
    And text is entered in the input field
    And an OpenAI API key is configured

  Scenario: Generating a talk script
    When I click the "トーク原稿を生成" button
    Then a podcast-format script should be generated
    And token usage information should be displayed
