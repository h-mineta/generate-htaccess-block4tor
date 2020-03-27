# generate_htaccess_block4tor

## 実行方法
* `generate_htaccess_block4tor.sh` を編集し、環境に合わせる
* `generate_htaccess_block4tor.sh` をcrontab等で定期実行する

## 応用編
メール送信
```
./generate_htaccess_block4tor.sh | mail -s "実行結果レポート" -r from@exsample.com to@exsample.com
```
