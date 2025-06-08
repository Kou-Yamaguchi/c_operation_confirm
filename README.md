# 自動採点スクリプト（C言語課題）

このリポジトリには、**C言語の課題提出物に対する自動採点スクリプト**が含まれています。  
以下の手順に従って、**Pythonが初めての人でも**環境構築から実行まで進められるよう説明しています。

---

## このスクリプトの目的

このスクリプトは、学生が提出したC言語のプログラムについて

- コンパイルが成功するか（gcc を使用）
- 指定の入力に対して正しい出力を出すか

を一括で評価し、名簿と照らし合わせて提出状況も把握できるようにするものです。

---

## 🔧 前提環境

- Windows または macOS
- Python未インストールでもOK（後述の手順でインストールします）

---

## 1. Pythonのインストール

Pythonの公式サイトから最新版をインストールしてください。

### Windows の場合

1. [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) にアクセス
2. 上部の「Download Python 3.x.x」をクリック
3. インストーラーを開き、「**Add Python to PATH**」にチェック ✅ を入れてから「Install Now」をクリック

### macOS の場合

1. [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/) にアクセス
2. 「Download Python 3.x.x」 をクリックし `.pkg` ファイルをダウンロード
3. ダブルクリックでインストールを進めます

インストール後、以下のコマンドで確認できます：

```sh
python3 --version
```

---

## 2. 仮想環境(venv)の作成と起動

Pythonの環境を汚さずに実行するため、仮想環境(venv)を使います。

### 1. 仮想環境の作成

ターミナル（またはコマンドプロンプト）で、プロジェクトフォルダに移動して以下を実行：

```sh
python3 -m venv venv
```

### 2. 仮想環境の起動

- Windowsの場合：

```cmd
venv\Scripts\activate
```

- macOS/Linuxの場合：

```sh
source venv/bin/activate
```

※仮想環境が有効になると、プロンプトの先頭に (venv) と表示されます。

---

## 3. 必要なパッケージのインストール

次のコマンドで必要なモジュール（pandas, openpyxl）をインストールします。

```sh
pip install -r requirements.txt
```

---

## 4. 必要ファイルの配置

以下の3種類のファイル／フォルダを準備してください。

```
project/
├── score.py              # 採点スクリプト（このリポジトリ内）
├── requirements.txt      # 必要なモジュール一覧
├── tests/                # テストケースフォルダ（*.in, *.out）
│   └── tests-1/
│       ├── case1.in
│       ├── case1.out 
│       └── ...
├── submits/              # 学生の提出物が入ったフォルダ
│   └── submits-1/
│       ├── 0000001/last.c
│       ├── 0000002/main.c
│       └── ...
└── roster.xlsx           # 名簿（学籍番号と氏名のExcel）
```

### 🧾 roster.xlsx の形式（例）

| A        | B          | ... | 
| -------- | ---------- | --- | 
| 学籍番号 | 名前       |     | 
| 0000001  | 山田　太郎 |     | 
| 0000002  | 佐藤　花子 |     | 
| ...      | ...        |     | 

※1行目はヘッダー行です。

### 📁 tests フォルダの形式（例）

- sample1.in（入力ファイル）
- sample1.out（期待される出力ファイル）
- sample2.in、sample2.out も同様に

---

## 5. スクリプトの実行

以下のコマンドで採点を実行できます：

```sh
python score.py --submits submits/{submits} --tests tests/{tests} --roster {roster}.xlsx --outfile result.xlsx
```

成功すると、採点結果が result.xlsx に保存されます。

---

## ✅ 出力されるファイルの内容

出力ファイル result.xlsx には、名簿に記載されている学生すべての採点結果が出力されます。

| A          | B          | C       | D    | E                | 
| ---------- | ---------- | ------- | ---- | ---------------- | 
| student_id | name       | compile | test | detail           | 
| 0000001    | 山田　太郎 | OK      | OK   | All tests passed | 
| 0000002    | 佐藤　花子 | NA      | NA   | 未提出           | 
| 9999999    |            | OK      | NG   | 出力不一致       | 

※名簿に存在しない提出者（聴講生など）は末尾に追加されます。

---

## 🧼 仮想環境の終了

作業が終わったら、以下のコマンドで仮想環境を終了できます。

```sh
deactivate
```

---

## 📩 問題が起きたときは？

- Pythonが動かない／pipが見つからない → インストール時の PATH 設定が漏れている可能性があります。
- Excelが開けない → Excelがインストールされているか確認してください（Googleスプレッドシートでも代用可）。

不明な点がある場合はTAや担当教員に気軽に相談してください。

---