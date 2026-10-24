![ROKID AIUI Agent Skill — Describe. Build. Verify. 公式製品画像を基にした Rokid Glasses のヘッダー](docs/assets/readme-hero-rokid-glasses.png)

<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.en.md">English</a> · <strong>日本語</strong><br>
  使用ガイド：<a href="docs/usage.zh-CN.md">中文</a> · <a href="docs/usage.en.md">English</a> · <a href="docs/usage.ja.md">日本語</a>
</p>

<div align="center">

[![CI](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml) [![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE) [![AIUI target: 0.19.0](https://img.shields.io/badge/AIUI_target-0.19.0-9BE564.svg)](skills/rokid-aiui-agent/references/aiui-0.19.md)

</div>

# ROKID AIUI Agent Skill

**ひとつの要望から、AIUI Studio にインポートできる完全な Agent へ。**

コミュニティが保守するオープンソースの Agent Skill です。**Codex、Claude Code、Cursor** などのコーディングツールで、ROKID AIUI の仕様に沿った開発を進められます。作りたいものを伝えると、ツールが編集可能なソースプロジェクトを生成し、機能と操作体験を確認して、提出資料を準備します。

普段使っているコーディングツールにインストールすれば、新しい Agent の作成に加え、既存プロジェクトのレビュー、デバッグ、拡張にも使えます。対象バージョンに合う参考資料、プロジェクト検証スクリプト、完全なサンプルをまとめており、API が実際に呼び出されているか、結果が有効か、Studio や対象のグラスで確認すべき項目が何かを確かめられます。

新規プロジェクトの既定バージョンは **AIUI 0.19.0** です。同梱の日本語 Focus Timer は、互換性の回帰テスト用として **0.17.0** を維持しています。ソースは **Apache-2.0** で公開され、確認、変更、拡張が可能です。

[クイックスタート](#クイックスタート) · [必要な環境](#必要な環境) · [Web・デスクトップへの導入（中国語）](docs/web-and-desktop.zh-CN.md) · [サンプルを見る](#同梱の-focus-timer) · [検証範囲](#自動チェック)

## この Skill でできること

コーディングツールから、この Skill を使って次の作業を依頼できます。

- 完全で編集可能な AIUI プロジェクトの作成
- 既存 AIUI プロジェクトの変更や拡張
- 実装する機能に応じた [`app.json` のページ、権限、アプリケーションエントリの設定](skills/rokid-aiui-agent/references/project-anatomy.md#configure-appjson-from-actual-features)
- コミュニティのサンプルを参考にしたカメラ・モデル・音声フローの構築と、キャンセル、再試行、重複入力、実データの受け渡しの確認：[実践ガイド](skills/rokid-aiui-agent/references/community-patterns.md)
- AIUI コード、操作フロー、バージョン互換性のレビューとデバッグ
- プロジェクトの検証と AIUI Studio にインポートできるソースの納品。パッケージ作成の条件を満たす場合は `.aix` も追加で納品
- 機能と UX の確認、Agent 紹介文、権限の説明、審査資料の準備

## 必要な環境

*Prerequisites · 実施する作業に合わせて環境を準備してください。*

| 実施する作業 | 必要なもの |
| --- | --- |
| コーディングツールで Skill を使う | Agent Skills 対応ツール、利用可能なアカウント、Skill の読み取りとプロジェクト編集の権限。ローカル検証にはターミナルの実行権限も必要 |
| 下記の `npx skills` コマンドでインストールする | **Node.js ≥22.20.0** と npm / npx。[Skills CLI の要件](https://github.com/vercel-labs/skills#install-a-skill)を参照 |
| 同梱のプロジェクト検証を実行する | このリポジトリの CI と同じ **Python 3.12** を推奨。基本構造、フィンガープリント、機能一覧のスクリプトは標準ライブラリを使用 |
| ローカルでプレビューやパッケージ作成を行う | 任意で **AIX CLI**。このリポジトリでは `0.8.2` に固定しており、Node.js ≥20 が必要。まず `aix --help` で実際に対応しているコマンドを確認 |
| Studio・実機で受け入れ確認を行う | 利用権限のある **AIUI Studio** アカウント。デバイスの動作確認には対象の **Rokid Glasses** が必要 |

Web とデスクトップ App へのインストールは、[専用ガイド（中国語）](docs/web-and-desktop.zh-CN.md)の該当手順に従ってください。ツール、アカウント、デバイスなどの条件がそろわない検証は、`BLOCKED` と記録します。

このリポジトリの保守や全テストの実行では、[開発時の検証手順](docs/usage.ja.md#5-成果物を確認する)に従って開発用依存関係もインストールしてください。CI の基準環境は Node `24.19.0` と Python `3.12` です。

## 利用するツールを選ぶ

Web、デスクトップ App、CLI（コマンドライン）から利用できます。最初にツールをインストールまたは開き、その後にこの Skill を追加してください。App をインストールしただけでは、Skill は追加されません。

| 利用方法 | 始め方 | インストール・操作手順 |
| --- | --- | --- |
| Codex Web | ChatGPT で Codex Cloud 環境を作成し、クラウド側のプロジェクトリポジトリに Skill を配置 | [Web・クラウドの設定（中国語）](docs/web-and-desktop.zh-CN.md#codex-web) |
| Claude Web | Customize → Skills で完全な Skill ZIP をアップロードし、有効化 | [Web へのアップロード手順（中国語）](docs/web-and-desktop.zh-CN.md#claude-web) |
| Codex デスクトップ App | ChatGPT デスクトップ App をダウンロードし、Codex を選んで内蔵インストーラーから Skill を追加 | [App のダウンロード・導入・呼び出し（中国語）](docs/web-and-desktop.zh-CN.md#codex-desktop) |
| Claude デスクトップ App | Claude をダウンロードし、Code でローカルプロジェクトを開いて Skill を追加 | [App のダウンロード・導入・呼び出し（中国語）](docs/web-and-desktop.zh-CN.md#claude-desktop) |
| CLI / IDE | ターミナルから Skills CLI でインストールし、コーディングツールで呼び出す | [下記の 5 ステップ](#ルート-2codex-などの-vibe-coding-ツールで開発する) |

ターミナルを使わない場合は、デスクトップ App のガイドに従ってください。ブラウザのみを使う場合は、Codex Cloud または Claude Web の手順を選びます。ローカルにインストールした Skill が、すべての Web タスクから自動的に使えるようになるわけではありません。

## クイックスタート

*Getting started · 開始ルートを選び、検証できる最初の AIUI プロジェクトを作りましょう。*

既存プロジェクトがある場合や、まずサンプルを見たい場合はルート 1 を選んでください。AI と一緒に開発する場合はルート 2 を選びます。インストールコマンドと最初の開発依頼文は、そのままコピーして使えます。

### ルート 1：AIUI Studio でプロジェクトを開く

[AIUI Studio へのインポート手順](#aiui-studio-にインポートする)に従い、ローカルまたは GitHub 上の完全なプロジェクトを開きます。その後、Studio で編集と開発を続けられます。

まだプロジェクトがない場合は、[同梱の Focus Timer](#同梱の-focus-timer)から始められます。

### ルート 2：Codex などの Vibe Coding ツールで開発する

以下では Codex の CLI / IDE へのインストールを例に説明します。他の Agent Skills 対応コーディングツールでも利用できます。先に[必要な環境](#必要な環境)を確認してください。デスクトップ App の利用者は、上記ガイドでインストールした後、下記の開発依頼文を使えます。

1. Skill をインストールします。Agent Skills 対応のコーディング環境のターミナルで、次のコマンドを実行してください。現在のユーザー用にインストールし、結果を確認します。

   ```bash
   npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent --agent codex --global
   npx skills list --agent codex --global
   ```

   一覧に `rokid-aiui-agent` が表示されることを確認してください。Claude Code や Cursor では、両コマンドの `codex` を下表の値に置き換えます。`--global` により複数のプロジェクトで Skill を共有でき、AIUI プロジェクトのインポートディレクトリ内に Skill ファイルを置く必要がなくなります。

   | ツール | `--agent` の値 | チャットでの呼び出し方 |
   | --- | --- | --- |
   | Codex | `codex` | `$rokid-aiui-agent` と入力。[公式説明](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills) |
   | Claude Code | `claude-code` | `/rokid-aiui-agent` と入力。[公式説明](https://code.claude.com/docs/en/skills) |
   | Cursor | `cursor` | `/` と入力し、`rokid-aiui-agent` を検索して選択。[公式説明](https://cursor.com/docs/skills#how-skills-work) |

   `gh skill --help` が使える場合は、次の代替コマンドでも Codex にインストールできます。

   ```bash
   gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
   ```

2. 独立したワークスペースを開きます。この Skill のリポジトリ外にあるディレクトリをコーディングツールで開き、ファイルの読み書きとターミナルコマンドの実行ができる Agent モードを有効にしてください。

3. Skill を呼び出します。`/absolute/path/to/my_focus_timer` を自分の出力先の絶対パスに置き換え、次の依頼文を Codex のチャット入力欄に送信してください。

   ```text
   $rokid-aiui-agent を使用して、AIUI 0.19.0 のフォーカスタイマーを作成してください。
   独立したディレクトリ /absolute/path/to/my_focus_timer に出力し、この Skill リポジトリには書き込まないでください。
   最初に読み込んだ SKILL.md のパスを示し、既定の対象バージョンが 0.19.0 であることを確認してください。
   音声による時間設定と、開始、一時停止、再開、リセットに対応し、_current と _blank の両方を対象にしてください。
   AIUI Studio にインポートできる、完全で編集可能なソースプロジェクトを納品してください。
   機能、境界入力、異常からの復旧、ライフサイクルと、フォーカス・タッチ・音声操作の UX を確認してください。
   実行可能な検証を行い、実際の結果、プロジェクト全体の UX 表、機能ごとの検証表を納品してください。
   AIX pack/list とソースフィンガープリントの検証に成功した場合は、インポートルート外に .aix パッケージを出力してください。
   インポートルート外に Agent 紹介文、呼び出し例、権限の用途、審査資料のチェックリストを準備してください。
   未実施の Studio、プラットフォーム、実機検証は BLOCKED のままにし、ローカルプレビューを実機合格として報告しないでください。
   ```

   Claude Code では、最初の行を `/rokid-aiui-agent AIUI 0.19.0 のフォーカスタイマーを作成してください。` に変更します。Cursor では `/` メニューで Skill を選んでから依頼文を貼り付け、先頭の `$rokid-aiui-agent を使用して、` を削除してください。「フォーカスタイマー」を自分の作りたいものに変えたり、既存プロジェクトのレビューや修正を依頼したりできます。

4. 成果物を確認します。完全で編集可能な AIUI プロジェクトディレクトリを受け取り、エージェントが実際に行った検証とその結果を確認してください。成果物の一覧は[次の節](#成果物)にあります。

5. AIUI Studio にインポートします。`app.json` を含むソースディレクトリ自体を選択し、[インポート手順](#aiui-studio-にインポートする)に従って受け入れ確認を続けてください。

インストール後に Skill が見つからない場合は、セッションを開き直すかツールを再起動し、インストールと開発で同じマシン・ユーザーを使っているか確認してください。他のツールのインストール引数は [Skills CLI の対応ツール一覧](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)を参照してください。

## 成果物

新規作成では、完全で編集可能なソースプロジェクトが常に必須の成果物です。AIUI プロジェクトディレクトリとして納品され、そのディレクトリを選択して AIUI Studio にインポートできます。

| 成果物 | 内容と配置先 |
| --- | --- |
| ソースプロジェクト | `app.json`、エントリコード、すべてのページとリソース。独立した出力ディレクトリに配置 |
| 検証レポート | 実際の実行結果、プロジェクト全体の UX 表、機能ごとの検証表、未検証の項目 |
| `.aix` パッケージ | パッケージ作成の条件を満たす場合に追加で納品。インポートルート外に配置 |
| 提出資料 | Agent 紹介文、呼び出し例、権限の用途、審査手順、追加で必要な素材の一覧。インポートルート外に配置 |

`app.json.pages` に宣言したすべてのページと、それらのページが参照する画像、スタイル、その他のリソースを、必ずソースプロジェクトに含めます。単一ページのプロジェクトの構成例は次のとおりです。

```text
my-agent/
├── AGENTS.md
├── aiui-audit-claims.json
├── app.js
├── app.json
└── pages/
    └── index/
        └── index.ink
```

AIX pack/list の全工程とフィンガープリントの検証に成功した場合、標準でインポートルート外に `.aix` パッケージも納品し、ソースフィンガープリント、パッケージのパス、バイト数、SHA-256、内容一覧の検証結果を報告します。このパッケージは AIUI Studio のインポートルートとして選択できず、ソースの代わりにもなりません。

レポート内の `_current` は会話に埋め込まれた画面、`_blank` は全画面を表します。`PASS` は検証を実行して合格した項目、`FAIL` は実行後に失敗した項目、`BLOCKED` は条件がそろわず未検証の項目です。AIX ツールが利用できない場合は `BLOCKED`、実際のパッケージ作成や検証に失敗した場合は `FAIL` と記録します。

## AIUI Studio にインポートする

ソースの保存場所に合わせて、インポート方法を選びます。

- **ローカルプロジェクト**：`app.json` を含むディレクトリ自体を選択
- **GitHub プロジェクト**：リポジトリ URL、ブランチまたはコミット、AIUI プロジェクトのサブディレクトリを指定

同梱の Focus Timer を GitHub からインポートする場合は、次の値を使います。

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

ローカル検証は、AIUI Studio へのインポートや Rokid Glasses 実機での検証を代替しません。Studio にログインしていない場合や、対象デバイスが接続されていない場合は、該当する結果を `BLOCKED` のままにします。

## 同梱の Focus Timer

[Focus Timer のソース](skills/rokid-aiui-agent/assets/focus-timer-agent/)は、このリポジトリに同梱された唯一のアプリケーション例で、そのまま Studio のインポートルートとして使用できます。AIUI `0.17.0` の日本語単一ページタイマーで、既定は 10 分、1～3600 秒と任意のラベルを指定できます。

ソースとローカルテストで、次のイベントと状態の対応を確認しています。

| タイマーの状態 | イベントを受けたときの操作 |
| --- | --- |
| 開始前 | 開始 |
| 計時中 | 一時停止 |
| 一時停止中 | 再開 |
| 完了 | 最初から開始 |

会話で新しい時間を指定すると、新しい Page が開きます。音声による呼び出しは AIUI Studio と Rokid Glasses 実機での検証が必要なため、`BLOCKED` です。うなずきとタッチパッドも実機検証が必要で、同じく `BLOCKED` です。このサンプルは、バックグラウンドでの計時、システム通知、永続化データからの復元を保証しません。

以下は、2026-10-24 に同梱ソースを実際に動かし、プレビューの Enter コントロールで順に開始、一時停止を操作して撮影した画面です。元の 480 × 352 のキャンバス比率を維持しており、クリックすると原寸画像を確認できます。

| 開始前 · `idle` | 計時中 · `running` | 一時停止中 · `paused` |
| --- | --- | --- |
| ![Focus Timer の実際のプレビュー：10:00、開始ボタン](docs/assets/focus-timer-preview/idle.jpg) | ![Focus Timer の実際のプレビュー：09:54、一時停止ボタン](docs/assets/focus-timer-preview/running.jpg) | ![Focus Timer の実際のプレビュー：09:53、再開ボタン](docs/assets/focus-timer-preview/paused.jpg) |

撮影環境は AIX CLI `0.8.2`、ブラウザで実際に読み込まれた Ink は `0.19.1`、表示は既定のコンパクトビュー（`_current`）です。サンプルのソースは引き続き AIUI `0.17.0` 向けに保守しています。画像はブラウザプレビューのキャプチャであり、実機撮影ではありません。Studio、音声、グラス実機での検証を代替しません。[プレビュー全体と再現記録](docs/focus-timer-screenshots.md)

## 自動チェック

**マルチメディア機能では、API が実際に実行されたことを確認します。** 実装とテストの両方で「ユーザーまたは Agent からの入り口 → 実際の API 呼び出し → 有効なデータまたはイベント → 機能の結果」を追跡します。写真撮影では、`CAMERA` の宣言、映像ストリームの取得、カメラオブジェクトの作成だけでは不十分です。`capture.takePhoto()`、または公式の `CameraContext.takePhoto()` による同等の処理を実行して完了を待ち、有効な写真を取得してから処理する必要があります。音声再生、短い効果音、録音、動画なども、それぞれの開始と結果の要件に沿って確認します。[マルチメディアの実装とテスト](skills/rokid-aiui-agent/references/media-implementation-and-testing.md)を参照してください。

Skill はプロジェクトに実装された機能に合わせて検証を組み立て、ローカルの証拠と Studio・実機の証拠を区別します。

| 検証範囲 | 確認する内容 |
| --- | --- |
| プロジェクトとバージョン | プロジェクト構造、ページとリソースの完全性、対象バージョンとの互換性 |
| 機能 | 正常なフロー、境界入力、失敗からの復旧、ライフサイクル |
| UX | 画面を実際に操作し、状態のフィードバック、文言、フォーカス、タッチと音声の操作経路を確認 |
| AIX | 実際に対応しているコマンドを先に確認し、プレビュー、パッケージ作成、パッケージ内容の確認を実行 |
| 提出準備 | 文言、権限の用途、ソースとパッケージの情報、審査手順、素材の出典を確認 |

プレビュー HTML を生成できても、画面が正常に動作したとは限りません。ローカルで操作が成功しても、実機での合格を意味しません。実行条件がそろわない検証は `BLOCKED` と記録します。資料の準備が完了しても、アップロード済み、または審査に合格したことにはなりません。

詳しい検証方法は、[UX・機能テスト](skills/rokid-aiui-agent/references/ux-and-capability-testing.md)と[提出準備ガイド](skills/rokid-aiui-agent/references/submission-preparation.md)を参照してください。[直近の独立した生成検証](tests/evaluations/forward/08-fresh-agent-submission.md)には、0.19 Agent で実際に合格した項目、プレビューの障害、未完了の項目を記録しています。

## 対象バージョン

新規プロジェクトの既定バージョンは AIUI `0.19.0` です。既存プロジェクトで明示された `0.17.0`、`0.18.0` などのバージョンは維持します。同梱のタイマーと最小テンプレートは引き続き `0.17.0` を使用します。

現在のツールは 0.19 のプロジェクト構造検証と機能一覧に対応しています。ただし、このバージョンの機能を PASS と認定するポリシーは未登録のため、機能ごとの受け入れ判定は引き続き `BLOCKED` です。詳細は [AIUI 0.19 ガイド](skills/rokid-aiui-agent/references/aiui-0.19.md)と[公式 0.19.0 クイックスタート](https://open.rokid.com/aiui/guide/quickstart/intro?version=0.19.0&lang=en-US)を参照してください。

## リポジトリの構成

用途に応じて、次のファイルを参照してください。

| パス | 用途 |
| --- | --- |
| [SKILL.md](skills/rokid-aiui-agent/SKILL.md) | Skill の入り口と作業手順 |
| [references/](skills/rokid-aiui-agent/references/) | 必要に応じて読む開発・受け入れ確認の参考資料 |
| [scripts/](skills/rokid-aiui-agent/scripts/) | プロジェクト構造、機能、監査の検証ツール |
| [assets/studio-importable-minimal/](skills/rokid-aiui-agent/assets/studio-importable-minimal/) | Studio にインポートできる最小プロジェクトテンプレート |
| [assets/focus-timer-agent/](skills/rokid-aiui-agent/assets/focus-timer-agent/) | 唯一のアプリケーション例 Agent |
| [中文](docs/usage.zh-CN.md)、[English](docs/usage.en.md)、[日本語](docs/usage.ja.md) | 詳細な使用ガイド |

## 詳細ガイド

他の依頼文、検証コマンド、トラブルシューティングが必要な場合は、以下を参照してください。

- [日本語の使用ガイド](docs/usage.ja.md)：作成、変更、レビュー、デバッグ、パッケージ作成
- [Skill の入り口](skills/rokid-aiui-agent/SKILL.md)：作業手順と納品要件
- [情報源の優先順位](skills/rokid-aiui-agent/references/source-of-truth.md)：公式ドキュメント、実装、サンプルの間で情報が異なる場合の判断基準

## 改善への参加

不具合や要望は [Issues](https://github.com/BreezeLife/rokid-aiui-agent-skill/issues) にお寄せください。不具合を報告する際は、対象の AIUI バージョン、使用ツール、最小限の再現手順、実際の結果を添えてください。ログからはキーや個人データを削除してください。

コードやドキュメントの改善を提出する前に、[AGENTS.md](AGENTS.md) と[開発時の検証手順](docs/usage.ja.md#5-成果物を確認する)を読み、変更に関係する検証と完全なローカル検証を実行してください。バージョンに関する記述には対応する公式情報を引用し、実際のスクリーンショットやログには検証環境を明記します。

## 情報源とライセンス

開発の根拠は、対象バージョンに合う公式ドキュメント、実装、実行可能なサンプルです。第三者の資料は区別して記載しています。帰属の詳細は [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) を参照してください。コードのライセンスは [Apache License 2.0](LICENSE) です。
