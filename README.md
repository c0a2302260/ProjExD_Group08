# ShootingKokaton

## 実行環境の必要条件
* python >= 3.10
* pygame >= 2.1

## ゲームの概要
* 白いこうかとんを操作して、黒いこうかとんを倒すゲーム
* ウェーブが上昇する事に難易度が上昇するので倒されないようにより多くのウェーブをクリアしよう！
* ←↓↑→で移動
* SPACEでビームを発射(SHIFTを押しながらで散弾)
* SHIFTで加速
* EでEMP
* ENTERで重力場
* RSHIFTで無敵
## ゲームの実装
### 共通基本機能
* musou_kokaton.py
* ビームの速度調整

### 担当追加機能
* 残弾数の追加(担当:渋谷) : 自機が発射するビームの残弾数を管理する機能
* ウェーブ制で敵の追加(担当:臼井) : 敵を倒すとウェーブが上昇し、敵の数が増える機能
* 残機の追加(担当:浜屋) : 自機の残機を表示する機能。0になるとゲームオーバー
* クールダウンのスキル（担当:林田）:スキル使用する場合スコアは減らずクールタイムが発生する
* 背景スクロール（担当：飯野）：背景を右にスクロールする

### ToDo
<<<<<<< HEAD

### メモ
emp,gravity, hyperのクールダウンの追加。スコア減少しない。
=======
- [ ] 背景をスクロールさせる
- [ ]  敵を背景と同じく右に移動させる
### メモ
* Enemyクラスのupdateメソッドでipを(-3, 0)に変更
* Mainクラスの下で背景が動くように設定
* bg_imgとbg_img2で1つの背景として、tmrの値を参照してスクロールの速度を調整
>>>>>>> c0b23008/move_bg
