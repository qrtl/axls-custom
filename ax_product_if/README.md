# AX Prodcut Interface

## 何をするか?

Product を取り込む

### どうやって

1. 取り込むデータソース毎に、res.products.if.provider を継承したクラスを作る
2. データを取り込む
3. Product に反映させる

とりあえず ESC から取り込む Provider を完成させた。

## 設定

設定に Product daata interface の設定項目が追加される。有効化のチェックボックスを On に
する。FIle location はデフォルトのままで良い。

### プロバイダの登録

Purchase > Configuration > Products Interface が追加される。 Product IF はデータソース毎
にプロバイダを作成し、そのプロバイダを定期実行して品目を登録する。

## いつまで使うか?
ESCが廃止されたら停止する (2023/1?)