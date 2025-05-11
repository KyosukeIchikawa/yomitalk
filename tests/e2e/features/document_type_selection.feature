# language: en
Feature: Document Type and Podcast Mode Selection
    As a user of the podcast generation system
    I want to be able to select different document types and podcast modes
    So that I can generate podcasts for various document types with appropriate explanations

    Background:
        Given the user is on the podcast generation page

    Scenario: Default document type and mode selection
        Then the "論文" document type is selected by default
        And the "概要解説" podcast mode is selected by default

    Scenario: Changing document type
        When the user selects "マニュアル" as the document type
        Then the document type is changed to "マニュアル"
        And the "概要解説" podcast mode remains selected

    Scenario: Changing podcast mode
        When the user selects "詳細解説" as the podcast mode
        Then the podcast mode is changed to "詳細解説"
        And the "論文" document type is selected by default

    Scenario: Changing both document type and podcast mode
        When the user selects "ブログ記事" as the document type
        And the user selects "詳細解説" as the podcast mode
        Then the document type is changed to "ブログ記事"
        And the podcast mode is changed to "詳細解説"

    Scenario: Document type selection affects system log
        When the user selects "議事録" as the document type
        Then the system log shows the document type has been set to "議事録"

    Scenario: Podcast mode selection affects system log
        When the user selects "詳細解説" as the podcast mode
        Then the system log shows the podcast mode has been set to "詳細解説"

    Scenario: All document types are available
        Then the following document types are available
            | 論文     |
            | マニュアル |
            | 議事録    |
            | ブログ記事  |
            | 一般ドキュメント   |

    Scenario: All podcast modes are available
        Then the following podcast modes are available
            | 概要解説 |
            | 詳細解説 |
