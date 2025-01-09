1. Gitリポジトリを初期化する
git init

2. リモートリポジトリを追加する
git remote add origin git@github.com:ichiharahiroroki/OpenAlex_app.git

3. 必要なファイルをコミットする
git add .
git commit -m "Initial commit"


4. リモートリポジトリにPushする
git branch -M main  # 現在のブランチの名前を「main」に変更する
git push -u origin main


################
EC2での作業Amazon Linuxの場合
1.以下のコマンドでGitをインストールします
sudo yum update -y
sudo yum install git -y

2. リモートリポジトリをHTTPSでクローン
git clone https://github.com/ichiharahiroroki/OpenAlex_app.git

3. クローンされたリポジトリに移動
cd OpenAlex_app

4. リポジトリの内容を確認
ls

5. 最新の状態をPull（すでにリモートリポジトリとローカルは同期しているはずですが、以下のコマンドで最新状態を確認できます）
git pull origin main