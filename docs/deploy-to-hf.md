# Hugging Face Spacesへのデプロイ方法

このプロジェクトは、GitHub Actionsを使用してHugging Face Spacesにデプロイする設定が含まれています。
**デプロイは手動で実行でき、CIが成功した場合のみ実行可能です。**

## 事前準備

### 1. Hugging Face APIトークンの取得
1. [Hugging Face](https://huggingface.co/)にログインします。
2. 右上のプロフィールアイコンをクリックし、「Settings」を選択します。
3. 左サイドバーから「Access Tokens」を選択します。
4. 「New token」ボタンをクリックします。
5. トークン名を入力し、権限を「Write」に設定します。
6. 「Generate token」ボタンをクリックします。
7. 生成されたトークンをコピーします（このページを離れると二度と表示されないので注意）。

### 2. GitHubリポジトリにシークレットを設定
1. GitHubリポジトリのページに移動します。
2. 「Settings」タブをクリックします。
3. 左サイドバーから「Secrets and variables」→「Actions」を選択します。
4. 「New repository secret」ボタンをクリックします。
5. 名前に「HF_TOKEN」と入力し、値に先ほどコピーしたHugging Face APIトークンを貼り付けます。
6. 「Add secret」ボタンをクリックします。

## デプロイの流れ

1. `main`ブランチにプッシュまたはPRがマージされると、自動的にCIが実行されます。
2. CIが成功したことを確認します。
3. GitHubリポジトリの「Actions」タブに移動します。
4. 左サイドバーから「Deploy to Hugging Face Space」ワークフローを選択します。
5. 「Run workflow」ボタンをクリックします。
   - 注意: CIが成功していない場合は、デプロイボタンを押しても失敗します。
6. デプロイが完了するまで待ちます（数分かかることがあります）。
7. デプロイが完了したら、[https://huggingface.co/spaces/Kyosuke0/yomitalk](https://huggingface.co/spaces/Kyosuke0/yomitalk)にアクセスしてアプリケーションが正常に動作しているか確認します。

## トラブルシューティング

### デプロイに失敗する場合
1. GitHub Actionsのログを確認し、エラーメッセージを確認します。
2. CIが成功しているか確認します。
   - CIが成功していない場合は、まずCIを実行して成功させてください。
3. Hugging Face APIトークンが正しく設定されているか確認します。
4. Hugging Face Spacesの容量制限に達していないか確認します。
5. Dockerfileに必要なパッケージがすべて含まれているか確認します。

### アプリケーションが正常に動作しない場合
1. Hugging Face Spaces上のログを確認します（Spacesページの「Files and versions」タブ→「logs」フォルダ）。
2. 必要な環境変数が設定されているか確認します。
3. Dockerfileに必要なファイルがすべてコピーされているか確認します。
