Feature: ファイルからテキストを抽出する
  ユーザーとしては、様々な形式のファイル（PDFやテキストファイル）から
  テキストを抽出し、ポッドキャスト形式の音声を生成したい

  @file_extraction
  Scenario: PDFファイルからテキストを抽出する
    Given Gradioアプリが起動している
    When the user uploads a PDF file
    Then the extracted text is displayed

  @file_extraction
  Scenario: テキストファイルからテキストを抽出する
    Given Gradioアプリが起動している
    When the user uploads a text file
    Then the extracted text is displayed

  @file_extraction
  Scenario: 抽出したテキストからポッドキャストテキストを生成する
    Given Gradioアプリが起動している
    And OpenAI APIキーが設定されている
    And text has been extracted from a file
    When the user clicks the generate podcast button
    Then the podcast text is generated

  @file_extraction @audio
  Scenario: 生成されたポッドキャストテキストから音声を生成する
    Given Gradioアプリが起動している
    And VOICEVOXが設定されている
    And podcast text has been generated
    When the user clicks the generate audio button
    Then the audio is generated
