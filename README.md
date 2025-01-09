1. Gitリポジトリを初期化する
git init

2. リモートリポジトリを追加する
git remote add origin git@github.com:ichiharahiroroki/OpenAlex_app.git

3. 必要なファイルをコミットする
git add .
git commit -m "Initial commit"


4. リモートリポジトリにPushする
git branch -M main  # ブランチ名をmainに設定
git push -u origin main
