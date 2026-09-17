# サロン売り案件ボード

Threads / Instagram のプロフィールから飛ばす、店舗の売り案件一覧ページ。

公開URL: https://claude.ai/artifact/EUZ6q1bkHXtiz9DRmp2nSU

## 何が載って、何が載らないか

一覧に出すのは **県・年商・希望金額** の3つだけ。それ以外（立地・席数・スタッフ・
利益・譲渡理由など）はページに出さず、案件番号を添えて @nailsalon_support に
連絡してもらう。運営者の個人名はページのどこにも出さない。

売りたい人は自分でフォームに入力できる。必須は **メール・電話・店舗URL** と、
一覧に出る **県・年商・希望金額**。入力すると登録用の文章ができるので、コピーして
Threads に貼って送る形。「コピーしてThreadsを開く」の1タップでコピーと遷移が
同時に走る。自動では一覧に出ないので、しょーもない案件を弾ける。

## 一覧を編集する

`index.html` 末尾の `<script>` 冒頭にある定数を書き換える。

```js
var UPDATED  = "2026.09.17";  // ヘッダーに出る更新日
var THREADS  = "https://www.threads.com/@nailsalon_support";
var IS_SAMPLE = true;         // 実案件に差し替えたら false（サンプル注意枠が消える）

var LISTINGS = [
  { no: "001", pref: "千葉県", sales: 1800, price: 2200, status: "open", date: "09/12" },
  ...
];
```

- `sales` / `price` は **万円単位の数字**。`1800` → 「1,800万円」と表示される。
- `status` は `"open"`（募集中）/ `"talk"`（商談中）/ `"done"`（成約済み）。
  `open` 以外はデフォルトで非表示で、チェックボックスを入れると出る。
- 案件を消したい時は、その行ごと削除する。

## ファイルの形式について

このHTMLは Artifact として公開する前提なので、`<!doctype html>` / `<html>` /
`<head>` / `<body>` を持たない。Artifact 側がそれを付けて配信する。
他のホスティング（GitHub Pages など）に置く場合は、標準の head で包む必要がある。

ロゴのイラストは `data:` URI として直接埋め込んであるので、外部ファイルの依存はない。
