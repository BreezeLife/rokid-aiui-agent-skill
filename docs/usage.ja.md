[簡体中文](usage.zh-CN.md) | [English](usage.en.md) | [日本語](usage.ja.md) | [プロジェクトホーム](../README.md)

# ROKID AIUI Agent Skill 使用ガイド

<!-- usage:scope -->
## 1. この Skill でできること

`rokid-aiui-agent` は、Agent Skills に対応したコーディングエージェントを使って、ROKID AIUI Agent プロジェクトを新規作成、変更、レビュー、デバッグ、検証するための Skill です。標準の成果物は、断片的なコードや `.aix` パッケージだけではなく、編集可能で、そのディレクトリ自体を AIUI Studio のインポートルートとして選択できる完全なソースプロジェクトです。

新規作成または実装を依頼すると、通常は次の成果物が生成されます。

- `AGENTS.md`、`app.json`、アプリケーションエントリ、宣言されたすべての Page と参照リソースを含む AIUI ソースプロジェクト
- 製品として宣言する機能範囲を閉じるための `aiui-audit-claims.json`
- 正確なインポートルートに結び付いたソースフィンガープリント、機能インベントリ、厳格な構造検証、ビジネスロジックテストの結果
- 必須の `## Project UX evidence matrix` と `## Per-capability matrix`
- 使用中の AIX CLI が実際に対応している場合の preview、pack、list の結果
- ローカルパス、または GitHub の Repository、Ref、Directory の3点からなるインポート情報
- 未実施の AIUI Studio、物理デバイス、署名付きエビデンスのゲートを `BLOCKED` と明記した結果

プロジェクトとホストのどちらにも対象バージョンが指定されていない場合、Skill はその前提を明示し、AIUI `0.17.0` 安定版を基準にします。Widget や Agent Worker などの `0.18` 向け機能は、対象環境での対応が明確に確認された場合にのみ生成します。

製品固有の機能宣言がないプロジェクトでも、インポートルートに `aiui-audit-claims.json` が必要です。宣言対象が空であることを閉じた範囲として示す最小の schema 1 は次のとおりです。製品固有の機能がある場合は、実際の範囲に合わせて `claims` を追加してください。

```json
{
  "schemaVersion": 1,
  "scopeClosed": true,
  "claims": []
}
```

`claims` に追加するのは、実際の製品要件に含まれ、ソースインベントリだけでは確実に導出できない機能宣言だけです。空でない各宣言には独立した機能 gate とエビデンスが必要で、類似するソース項目の証明を流用できません。`scopeClosed: true` は宣言範囲が閉じていることだけを示し、機能がテストに合格したことを意味しません。

<!-- usage:install -->
## 2. インストール

Agent Skills に対応したコーディング環境で、汎用 Skills CLI を使用します。

```bash
npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent
```

ローカルの GitHub CLI が `gh skill` コマンドに対応している場合は、次の方法も使用できます。

```bash
gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
```

インストール前に、リポジトリ内の [`SKILL.md`](../skills/rokid-aiui-agent/SKILL.md) とスクリプトを確認してください。更新時は選択したインストールコマンドを再実行し、インストールツールが表示する取得元と revision を確認します。再インストールしただけでは、対象プロジェクトを検証したことにはなりません。

<!-- usage:invoke -->
## 3. 呼び出し方

コーディングエージェントとの会話で、依頼文に `$rokid-aiui-agent` を含めると明示的に呼び出せます。明示的な呼び出しが最も再現しやすい方法です。

```text
$rokid-aiui-agent を使用して、AIUI Studio にインポート可能な完全な ROKID AIUI プロジェクトを作成し、ローカル検証と UX・機能レビューまで実施してください。
```

Skill の暗黙的な検出に対応するホストでは、AIUI の開発、レビュー、デバッグ、AIX preview、パッケージ作成を直接依頼したときに自動で読み込まれる場合もあります。ルーティングの曖昧さを減らすため、公開に関係する作業では常に `$rokid-aiui-agent` を明記することを推奨します。

依頼文には、対象ディレクトリまたは既存のインポートルート、AIUI runtime、眼鏡のモデル、`_current` / `_blank` の表示ターゲット、入力方法、権限、画面言語、成果物の出力先を含めると確実です。情報が不足している場合、Skill はまずプロジェクトを調査します。それでも確認できない内容は、推測した API で埋めず、前提、`UNKNOWN`、または `BLOCKED` として残します。

<!-- usage:prompts -->
## 4. そのまま使える依頼例

<!-- prompt:new-project -->
### AIUI Agent を新規作成する

```text
$rokid-aiui-agent を使用して、独立したディレクトリ /absolute/path/to/weather-agent に完全な ROKID AIUI 天気 Agent を作成してください。
対象は AIUI 0.17.0 とし、会話内の _current と全画面の _blank の両方で Page を表示してください。
まず対象バージョンに合う公式情報を確認し、ブラウザや WeChat Mini Program の知識から API を推測しないでください。
AIUI Studio に直接インポートできる完全なソースディレクトリを納品し、決定論的テスト、厳格なプロジェクト検証、
機能インベントリ、AIX preview/pack/list（CLI のヘルプで対応を確認できたものだけ）を実行してください。
必須の Project UX evidence matrix と Per-capability matrix も出力し、実行していない Studio と実機の項目は BLOCKED のままにしてください。
```

<!-- prompt:timer -->
### フォーカスタイマーを開発する

```text
$rokid-aiui-agent を使用して、Rokid Glasses 向けのフォーカスタイマーを作成し、独立したディレクトリ /absolute/path/to/my-focus-timer に出力してください。
AIUI 0.17.0 の Page-only プロジェクトとし、ディレクトリ自体を AIUI Studio に直接インポートできるようにしてください。
1～3600 の整数 durationSeconds と任意の label を受け取り、未指定時は 600 秒を使用してください。
idle、running、paused、finished、error を実装し、絶対終了時刻から残り時間を計算してください。
hide/show では時間を再同期し、unload ではタイマーを解放してください。
_current と _blank にはそれぞれ適した情報量を設計し、ボタンのタップ操作とフォーカス経路を残してください。
うなずきやハードウェアキーは、対象バージョンの公式情報を確認できた場合にのみ追加し、常にセンサーを使わない fallback も提供してください。
バックグラウンド計時、システムアラーム、通知、永続化からの復元を約束しないでください。

決定論的ロジックテスト、厳格なプロジェクト検証、機能インベントリと、AIX が対応する preview/pack/list を実行してください。
完全な Project UX evidence matrix と Per-capability matrix を出力し、実施していない Studio と物理デバイスのゲートは必ず BLOCKED のままにしてください。
最後に、正確なローカルインポートルート、または GitHub の Repository、Ref、Directory を報告してください。
```

<!-- prompt:review -->
### 既存プロジェクトをレビューする

```text
$rokid-aiui-agent を使用して /absolute/path/to/aiui-project をレビューしてください。ただし、ソースコードは変更しないでください。
正確な AIUI Studio インポートルート、対象バージョン、Page/Widget/Agent Worker、_current/_blank、すべての入力と権限を確認してください。
ソースフィンガープリント、機能インベントリ、厳格なプロジェクト検証を実行し、リポジトリに既にある安全なテストだけを実行してください。
問題を重大度順に示し、Project UX evidence matrix と Per-capability matrix を生成してください。
現在の revision に対する実行エビデンスがない項目を PASS にしないでください。
Studio のログイン環境または物理デバイスがない場合は BLOCKED とし、N/A で代用しないでください。
```

<!-- prompt:debug -->
### プロジェクトを修正またはデバッグする

```text
$rokid-aiui-agent を使用して、現在の AIUI プロジェクトで「タッチパッドを1回押しても主要操作が実行されない」問題を修正してください。
最初に問題を再現し、Page イベント、host focus、element focus、デフォルトイベント、fallback の経路を特定してください。
その後、回帰テストを先に追加して最小限の修正を行ってください。現在の authoring mode と対象バージョンを維持し、存在しないイベント名を作らないでください。
修正後はソースフィンガープリントと機能インベントリを再生成し、厳格な検証と利用可能な AIX フローを実行して、Project UX evidence matrix と Per-capability matrix を更新してください。
古い revision のエビデンスを再利用しないでください。
```

<!-- prompt:verify-package -->
### 検証、プレビュー、パッケージ作成を行う

```text
$rokid-aiui-agent を使用して skills/rokid-aiui-agent/assets/focus-timer-agent を検証してください。最初に scripts/fingerprint_aiui_project.py、
scripts/inventory_aiui_capabilities.py、scripts/validate_aiui_project.py による厳格なプロジェクト検証を順に実行してください。
続けて deterministic tests（決定論的テスト）を実行してください。次に現在の aix --help を確認して、AIX が実際に公開している preview、pack、list だけを実行してください。アップロードやデプロイは行わないでください。
.aix の内容一覧に .git または .aiui-evidence が含まれていないことを確認し、実行コマンド、終了コード、成果物のパス、現在のソース revision を報告してください。
Project UX evidence matrix と Per-capability matrix も完成させ、scripts/validate_aiui_audit.py で最終監査を検証してください。
AIX のブラウザプレビューを AIUI Studio または実機のエビデンスとして扱わないでください。
```

<!-- usage:verify -->
## 5. 成果物を確認する

まず、報告されたインポートルート自体に `app.json` が直接含まれていることを確認してください。`app.json` がさらに深い階層にある親リポジトリを指定してはいけません。次のコマンドは、このリポジトリのタイマーサンプルを使った実行可能な例です。自分のプロジェクトでは `AIUI_IMPORT_ROOT` と対象バージョンを置き換えてください。

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt

AIUI_REPOSITORY_ROOT="$PWD"
AIUI_IMPORT_ROOT="skills/rokid-aiui-agent/assets/focus-timer-agent"

python3 skills/rokid-aiui-agent/scripts/fingerprint_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/inventory_aiui_capabilities.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT" --strict
python3 -m unittest discover -s tests -v
```

このリポジトリの lockfile は `@yodaos-pkg/aix-cli@0.8.2` を固定しており、Node.js `>=20` が必要です。選択中の Node/npm を確認してからロック済み依存関係をインストールし、`--help` に表示された preview、pack、list だけを実行してください。スモークスクリプトは対応済みの pack/list を確認します。

```bash
node --version
npm --version
npm ci --ignore-scripts --no-audit --no-fund

AIX_BIN="$PWD/node_modules/.bin/aix"
AIUI_PREVIEW_DIR="$(mktemp -d "${TMPDIR:-/tmp}/focus-timer-preview.XXXXXX")"
AIUI_PREVIEW_HTML="$AIUI_PREVIEW_DIR/index.html"
export AIX_BIN
"$AIX_BIN" --help
"$AIX_BIN" preview "$AIUI_IMPORT_ROOT" --html-out "$AIUI_PREVIEW_HTML"
test -s "$AIUI_PREVIEW_HTML"
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh skills/rokid-aiui-agent/assets/focus-timer-agent
```

監査バリデーターは、レポートと記録された `argv` を実行由来のデータとして検証しますが、記録されたコマンド自体は実行しません。現在の環境で実際に取得され、必要な署名主体の署名が付いた結果だけが実行エビデンスになります。

最終的な監査検証には、現在の revision に対する監査レポート、コンテンツアドレス化されたエビデンス、リポジトリ外に置かれた絶対パスの trust policy が必要です。

```bash
python3 skills/rokid-aiui-agent/scripts/validate_aiui_audit.py AUDIT.md \
  --repository-root /absolute/path/to/repository \
  --import-root skills/rokid-aiui-agent/assets/focus-timer-agent \
  --trust-policy /absolute/path/outside/repository/trust-policy.json
```

監査の終了コードと機械判定は固定されています。

| 終了コード | 機械判定 | 意味 |
| --- | --- | --- |
| `0` | `release-ready-pass` | 構造が有効で、`Final status: PASS` かつ `Release-ready: YES` |
| `2` | `valid-not-release-ready` | 構造は有効だが、結果が `FAIL` または `BLOCKED` のためリリース不可 |
| `1` | `invalid-or-untrusted` | レポートが無効、古い、改ざんされている、または信頼されていない |

<!-- usage:audit -->
## 6. 必須の UX・機能検証

新規作成、実装、変更、レビューのたびに、2つの独立した表を生成する必要があります。完全な形式は [`ux-and-capability-testing.md`](../skills/rokid-aiui-agent/references/ux-and-capability-testing.md) を参照してください。

- `## Project UX evidence matrix`：target、状態、境界値のテキスト、host/element focus、入力経路ごとの挙動、回復、ライフサイクル、単色グリーン表示、実際の光学環境、動作・性能を項目別に検証します。
- `## Per-capability matrix`：API、コンポーネント、イベント、route、宣言、権限、fallback、cleanup を機能ごとに検証し、固定されたバージョンの公式情報とスキャナーの gate に結び付けます。

結果に使用できる値は次の4つだけです。

- `PASS`：その行で必要なすべてのエビデンスレイヤーが現在のソースに対して実行され、判定条件を満たしている。
- `FAIL`：実行済みのエビデンスが判定条件に反している。
- `BLOCKED`：必要な環境、署名主体、または現在の revision に対するエビデンスが提供されていない。
- `N/A`：ソース範囲と閉じた製品範囲の両方から、その条件が適用対象外だと証明できる場合だけ使用できる。デバイスや時間がないことは `N/A` ではありません。

6つのエビデンスレイヤーは相互に代替できません。`SOURCE` は対象バージョンの根拠、`STATIC` は構造とバインディング、`LOGIC` は決定論的ロジック、`AIX` はローカル CLI と基本的なブラウザレンダリング、`STUDIO` はログイン済み環境でのインポートと Web simulation、`DEVICE` は指定した物理デバイス上の入力、光学表示、性能を証明します。実行エビデンスと AIX キャプチャには `RUNNER` 署名主体の署名が必要です。Studio、物理デバイス、適用範囲の除外には、それぞれ `STUDIO`、`DEVICE`、`SCOPE` として定められた署名主体の署名も必要です。必要な署名がない項目は `BLOCKED` のままにします。

<!-- usage:import -->
## 7. AIUI Studio にインポートする

ローカルインポートでは、`app.json` が直接含まれる AIUI プロジェクトディレクトリを選択してください。プロジェクトがさらに深い階層にある親リポジトリを選択してはいけません。

GitHub からインポートする場合は、Repository、Ref、Directory を必ずセットで指定します。タイマーサンプルのインポート情報は次のとおりです。

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

アカウントでログインした AIUI Studio へのインポートは独立した検証作業です。厳格なソース検証、AIX preview、pack がすべて成功していても、実際にインポートしていない場合は Studio の検証ゲートを `BLOCKED` とし、「AIUI Studio にインポートできるようソースを準備済み」とだけ報告してください。「Studio で検証済み」とは報告しないでください。

<!-- usage:completion -->
## 8. 完了と判断できる条件

「ソースの納品が完了」とは、完全なソースプロジェクト、インポート情報、ローカル検証結果がそろっていることを意味します。これは自動的に「リリース可能」を意味しません。監査バリデーターが現在のフィンガープリントと信頼できるエビデンスに対して `0` を返し、適用対象の `FAIL` / `BLOCKED` が1件もない場合にだけ、`Release-ready: YES` と記載できます。

正しい途中経過の例は、「厳格な構造検証、ロジックテスト、AIX pack/list は完了。AIUI Studio へのインポートと物理 Rokid Glasses 上の UX 検証は `BLOCKED`」です。

<!-- usage:examples -->
## 9. インポート可能なサンプル

- [`skills/rokid-aiui-agent/assets/studio-importable-minimal`](../skills/rokid-aiui-agent/assets/studio-importable-minimal/)：安定版向けの最小 Page プロジェクト
- [`skills/rokid-aiui-agent/assets/focus-timer-agent`](../skills/rokid-aiui-agent/assets/focus-timer-agent/)：日本語のフォーカスタイマー

どちらのディレクトリもインポートルートです。製品仕様を備えたサンプル Agent として、このリポジトリに含めるのはタイマーだけです。リポジトリ内の自動テストは、利用者自身の AIUI Studio と対象デバイスでの検証を代替しません。

<!-- usage:troubleshooting -->
## 10. トラブルシューティング

- **Skill が起動しない**：依頼文の先頭に「`$rokid-aiui-agent` を使用してください」と明記します。
- **Studio にプロジェクトが表示されない**：選択したディレクトリに `app.json` と宣言済み Page が直接含まれていることを確認し、親ディレクトリを選ばないでください。
- **AIX コマンドが存在しない**：使用する実行ファイルの `--help` を先に確認し、そのバージョンが実際に表示するコマンドだけを使用してください。別のブランチや古い Web サイトのコマンドをそのまま使用しないでください。
- **preview は成功するが眼鏡上で動作しない**：preview は `AIX` レイヤーのエビデンスにすぎません。Studio host、センサー、ハードウェアキー、フォーカス、権限、光学表示を証明するものではありません。
- **眼鏡がない場合に N/A と記載できるか**：できません。適用対象となる実機項目は `BLOCKED` です。
- **pack は公開と同じか**：同じではありません。pack は `.aix` を生成して内容を確認するだけです。アップロード、プラットフォーム審査、デプロイ、実機検証は後続の別工程です。
- **Widget / Agent Worker を使用できる条件**：対象 runtime が対応する `0.18` の機能を明確にサポートし、そのバージョン向けの情報源とエビデンス方針が確認できた場合に限ります。
