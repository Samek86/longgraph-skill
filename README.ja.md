<div align="center">

# longgraph

**Claude Code、Cursor、Codex、Grok Build向けの長期実行エージェントスキル**

永続的な台帳、クリーンコンテキストのスーパーバイザー、検証済みゲートでエージェントのドリフトを防止。
一つのループで多数の長期タスクをキューに入れ（無関係なものでも可能）、ホストを切り替えた後も
同じプロンプトをファイルに対して再送することで継続できます。

一度設計 → 永続的なループグラフをコンパイル → 完了まで全て検証。

[![GitHub stars](https://img.shields.io/github/stars/levi-qiao/longgraph-skill?style=flat-square&color=6C63FF)](https://github.com/levi-qiao/longgraph-skill/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-14B8A6?style=flat-square)](LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-22C55E?style=flat-square)](CONTRIBUTING.md)
![Hosts: Claude Code · Cursor · Codex · Grok Build](https://img.shields.io/badge/Hosts-Claude%20Code%20·%20Cursor%20·%20Codex%20·%20Grok%20Build-111827?style=flat-square)
![Type: agent skill · prompt library](https://img.shields.io/badge/Type-agent%20skill%20·%20prompt%20library-0EA5E9?style=flat-square)

[English](README.md) · 日本語 · [한국어](README.ko.md)

</div>

<img alt="Executor and clean-context supervisor loops running side by side" src="assets/graph.png" width="100%" />

## 📌 このフォークについて

これは[Samek86](https://github.com/Samek86)によって保守されている、[levi-qiao/longgraph-skill](https://github.com/levi-qiao/longgraph-skill)の**機能強化版フォーク**です。

### 🎯 追加機能

- **📚 多言語ドキュメント**: 英語・日本語・韓国語の完全なREADME
- **📊 深いstatus.json配線**: 実行中のアーティファクトがマシンリーダブルな進捗（`status.json`）を出力 — ノードが自動的にフェーズ、ラウンド、ハートビートを更新；ヘルパースクリプトとCI検証を含む
- **🔍 Scout自動ブリーフライフサイクル**: プリセットホットパス上のScoutノード — コンパイラがクリティカルパス外の調査のためにScoutブリーフ + findings プロトコルを自動生成（loop-research / loop-deliver / loop-converge）
- **🔒 シークレットスクラブ**: コミット前に秘密情報をスキャンするローカルスクリプト
- **✅ CI検証**: GitHub Actionsによる自動的な構造とリンクのバリデーション

> **上流との互換性**: すべての拡張は付加的です。コアのloop-graph設計は変更されていません。
> 詳細は[FORK.md](FORK.md)を参照してください。

---

## longgraphとは

**longgraph**（`longgraph-skill`）は、キュレーションされた**エージェントスキル**およびクロスホスト
**プロンプトライブラリ**で、**長期実行/長期水平線**エージェント作業用です—数時間に及ぶコーディング、
マルチマイルストーン移行、**一つのループでの長期タスクのキュー**（関連している必要はありません）、
および一つのコンテキストウィンドウを超えて継続するあらゆる作業に対応します。これは
**エージェントのためのグラフエンジニアリング**です：専門的な役割（executor · supervisor ·
scout）が、永続的で検査可能なファイルを通じて接続されています—別のオーケストレーション
ランタイムではありません。スコアボードがディスク上に存在するため、**実行中にホストを変更**できます：
同じワークスペースを開き、凍結されたノードプロンプトを再送信し、続けます。

> **一つの永続的グラフ、ホスト間でポータブル。** 単純な自己完結型の目標の場合は、
> ホストの通常のタスクまたはゴールを直接使用してください；longgraphは永続的グラフ
> 構造が価値を追加する場所から始まります。

## エビデンス

これらはワンショットデモではありません。longgraphは**Markdownスキル/プロンプトライブラリ**
（オーケストレーションランタイムではありません）。表は**検証可能な公開Git**、
**機能のみが編集された複数日パターン**、および**合成教材**を混合しています。

| ケース | 読者が検証できること | 種類 |
| --- | --- | --- |
| [**このスキルの自己反復**](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md) | **約14カレンダー日**（2026-07-19 → 2026-08-02）にわたる**87**の公開コミット、**74**ファイル、ライブラリに書き戻されたメソッドルール（ウェイクエッジなし、ゲート待機バックログ、ブロック≠パーク、有界ライブエッジ、オーサリング≠ランタイム） | 公開Git事実—固定アンカー`6efcb7f` |
| [**複数日コントロールプレーンパターン**](skills/loop-graph/examples/redacted-multiday-control-plane/README.md) | 複数日のウォールクロック、数十ラウンド、多数のディレクティブ：永続的台帳、クリーンコンテキストスーパーバイザーが自己報告された証拠を覆す、スキップ不可能なゲート、ブロックされた作業レーン、所有者A/B/C—**機能のみ**、プライベートペイロードなし | 編集された実行パターン |
| [**migrate-blob-storage**](skills/loop-graph/examples/migrate-blob-storage/README.md) | マルチマイルストーン台帳：パイロット→コホート、強制収束、スーパーバイザーが自己報告された証拠を覆す、スキップ不可能なゲート+ブロックされた作業レーン | 合成教材（架空のアプリ） |
| [**add-tests-to-cli**](skills/loop-graph/examples/add-tests-to-cli/README.md) | 最小の完全実行：3ラウンド、登録後延期、クリーンコンテキストスーパーバイザーの意図 | 合成教材（架空のCLI） |

**時計の読み方。** 自己反復ウィンドウの約14日/約340時間は
**プロジェクトウォールクロック**（最初の公開コミット→凍結アンカー）であり、連続的なモデル
実行ではなく、無人本番自律性の主張でもありません。[自己反復ケース](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md)のコマンドでGitを再確認してください。
編集された複数日カードは**粗いバケットのみ**を使用し、プライベートGit
再確認可能**ではありません**—そのエビデンス境界を参照してください。

将来のケースの公開ルール：
[公開/プライベート境界](docs/public-private-boundary.md)。

## いつ使用するか

以下のいずれかが必要な場合、longgraphに手を伸ばしてください：

- コンテキストコンパクション/セッションリセット後も動作し続ける**長期水平線エージェント**
- チャットメモリの進捗状況の代わりに**永続的タスク台帳**（単一スコアボード）
- **一つのループでの複数の長期タスク**—項目が無関係であっても、継続的なキュー
- **ホストポータブル継続性**—同じファイルに対してプロンプトを再送信することで、実行中にClaude Code ↔ Cursor ↔ Codex ↔ Grok Buildを切り替え
- 独立した**クリーンコンテキストスーパーバイザー**—同じエージェントが自己を評価するのではない
- **検証済み完了**：受け入れゲートが実際の出力に対して再実行され、自己報告の「完了」ではない
- **スキップ不可能なゲート**と明示的な所有者レッドラインを持つマルチマイルストーン作業
- **Claude Code · Cursor · Codex · Grok Build**間で動作する**Markdownスキル/プロンプトライブラリ**

### いつ使用*しない*か

- ワンショット編集、小さなPRサイズのタスク、または単一のクリーンセッションに収まるもの
- **ランタイムフレームワーク**が必要な場合（LangGraph、CrewAI、AutoGen、カスタムエージェントサーバー）
- 台帳、ゲート、または独立したレビューを必要としない単一の短いプロンプトのみが必要な場合

### 比較

| アプローチ | ランタイム/サーバー？ | 独立検証者 | 永続的スコアボード | マルチタスクキュー+実行中のホスト切り替え |
| --- | --- | --- | --- | --- |
| LangGraph / CrewAI / AutoGen | はい | 自分で構築 | 通常はい | フレームワーク依存；多くの場合単一のデプロイメントスタック |
| 一つのメガプロンプト/単一スキル | いいえ | いいえ（自己チェック） | 弱い（チャットメモリ） | 弱い—進捗はセッションとともに消滅 |
| **longgraph（このリポジトリ）** | **いいえ—Markdownのみ** | **はい（スーパーバイザーノード）** | **はい（`ledger.md`）** | **はい—ファイルが実行；プロンプトを再送信** |

関連検索：*longgraphスキル*、*長期水平線エージェントスキル*、
*長期実行エージェントスキル*、*エージェントドリフト防止*、*マルチタスクエージェントループ*、
*AIコーディングホストをタスク中に切り替える*、*Claude Codeマルチエージェントスーパーバイザー*、
*Grok Buildエージェントループ*、*エージェント台帳*、*ループグラフ*、*エージェントのためのグラフエンジニアリング*、
*クリーンコンテキストレビュー*。

## なぜlonggraph

長期実行エージェントは予測可能な方法でドリフトする傾向があります：スコープが拡大し、「完了」
が自己報告になり、テストが実際のパスを証明しなくなり、初期の決定が
コンテキストから消えます。longgraphは保護手段をモデルのメモリの外に移動します：

- **書かれただけでなく検証済み**—受け入れゲートが実際の出力に対して再実行されます。
- **永続的状態**—台帳はコンテキスト損失を乗り越え、単一のスコアボードのままです。
- **多数の長期タスク、一つのループ**—台帳は継続的なキュー；項目は
  独立している可能性があります（移行、テスト負債、ドキュメント、ゲート）一つのメガゴールを強制することなく。
- **ホストポータブル**—進捗は`.longgraph/<date-slug>/`下のファイルであり、チャット
  履歴ではありません。別のホストを同じワークスペースに向け、コンパイルされたノード
  プロンプトを再送信し、次の開いた台帳項目を拾います。
- **クリーンコンテキストレビュー**—独立したスーパーバイザーがエグゼキューターが見ることができないドリフトを捕まえることができます。
- **強制収束**—成長は定期的に停止され、測定され、簡素化されます。
- **低摩擦の所有者決定**—本物の所有者専用の呼び出しは短い
  推奨されたA/B/C選択として到着し、技術的な宿題の課題ではありません。

これはMarkdownであり、オーケストレーションフレームワークではありません：アプリケーションランタイム、サーバー、
またはベンダーロックインはありません。**Claude Codeプラグイン**としてインストールするか、**Codex /
Cursor / Grok Build**にシンボリックリンクを作成します（インストールスクリプトを参照）。Grok Buildのランタイム
ノードは**プロンプトのみ**のまま—2つの`/loop`ペースト、直接起動なし。

## マルチタスクループとホストの切り替え

**一つのループはキューであり、単一のストーリーではありません。** 各ラウンドは依然として一つの
独立して検証可能な台帳作業項目をエンドツーエンドで完了します（実装→検証→記録）。その
項目は、動作主張、書き込みセット、およびゲートを共有する結合された変更の一つの一貫したワークセットである可能性があります；
無関係な作業は別々のままです。台帳は一度に多数の長い項目を保持できます—
関連するマイルストーン*または*無関係なバックログ（ゲート待機バックログパターンは極端な
ケース：監査中の項目に依存しない有用な作業）。次の長いタスクが何か別のものについてである
たびに新しいグラフが必要というわけではありません。

**ホストは交換可能；ファイルは交換不可能です。** コンパイルされたループグラフ実行は
プロンプトと状態を`.longgraph/<date-slug>/`下に凍結します。他の場所で続けるには：

1. それらのファイル（およびプロジェクト）を見ることができるワークスペースを使用します。
2. 新しいホストで同じ凍結されたexecutor（および、使用されている場合、supervisor）プロンプトを再送信します。
3. ノードは`ledger.md` / `directives.md`を読み取り、次の開いた項目から続けます。

チャットトランスクリプトをエクスポートしているわけではありません。呼び出し構文は依然として各ホストの
方言に従います（[ホストごとのリファレンス](skills/loop-graph/references/)）—*進捗*のみがポータブルです。

## longgraphは適切なツールですか？

| あなたのタスクの形状 | 選択 | 得られるもの |
| --- | --- | --- |
| 通常のタスク/セッションに収まる一つの自己完結型ゴール | ホストの通常のタスクまたはゴールを直接使用 | longgraphラッパーまたは追加のプロンプト層なし |
| 多数の検証済みスライスにわたる機能、統合、移行、または動作要件 | [**`/loop-deliver`**](skills/loop-deliver/README.md) | 共有グラフ上の要件パック、追跡可能な受け入れ証明付き |
| 複数ラウンドの未使用/重複/再利用/スリム化（同じ2ノードグラフ） | [**`/loop-converge`**](skills/loop-converge/README.md) | 事前バインドされた収束パックを持つ共有コンパイラ |
| オープンソースの証拠、一次研究、および実験で実行可能なアプローチを比較 | [**`/loop-research`**](skills/loop-research/README.md) | 証拠主導の決定パック；結果が比較可能な場合にのみ選択 |
| 上記でカバーされていないカスタム形状を持つ多数のラウンド | [**longgraph / loop-graph**](skills/loop-graph/README.md) | カスタムグラフ実行用の共有コンパイラ |

**経験則：** グラフが必要ない場合は、longgraphを使用しないでください。

## クイックスタート

### Claude Code

マーケットプレイスからプラグインをインストール：

```text
/plugin marketplace add levi-qiao/longgraph-skill
/plugin install longgraph@longgraph-skill
```

### Codex、Cursor、またはGrok Build

ライブラリをインストールし、シンボリックリンクを作成してローダーが従うホストに`/longgraph`、`/loop-converge`、`/loop-deliver`、
`/loop-research`を配置します：

```sh
curl -fsSL https://raw.githubusercontent.com/levi-qiao/longgraph-skill/main/install.sh | sh
```

ローカルクローンから、リポジトリルートで`./install.sh`を実行します。

Grok Buildでのオーサリングは、そのインストール後に`/longgraph`です。2つのランタイム
ノードを開始するのは依然としてプロンプトのみ：コンパイルされた`/loop`行を貼り付けます—
[Grok Build](skills/loop-graph/references/grok.md)を参照してください。CursorおよびShell/cronは同じ
プロンプトのみの実行パスを使用します—[ホスト互換性](#ホスト互換性)を参照してください。

### 実行を設計

`/longgraph`を呼び出します；クリーンアップを`/loop-converge`に、要件を
`/loop-deliver`に、証拠主導のオプション選択を`/loop-research`にルーティングします。現在のホストを検出し、
ワークスペースを検査し、実行をコンパイルする前に未解決の所有者決定のみを尋ねます。CodexまたはClaude Codeでの直接作成を選択して、
両方の同じホストランタイムノードを開始するか、手動/クロスホスト起動用のプロンプトのみ（Grok
Buildを含む）を選択します。本当にカスタムな実行形状の場合にのみ`loop-graph`を直接使用してください。

オーサリングとランタイムは別々のままです：オーサースキルは作業をコンパイルしますが、決して
実行しません。生成されたノードは、凍結された実行契約に従って
`.longgraph/<date-slug>/`下に配置されます。

## グラフの仕組み

| 役割 | 責任 | 永続的エッジ |
| --- | --- | --- |
| **Executor** | 一つの独立して検証可能な台帳作業項目を処理し、同じラウンドでそれを検証し、結果を記録 | `ledger.md`を読み書き |
| **Supervisor** | 独自の別個のコンテキストから再検証し、合格した作業をチェックポイントし、ドリフトを修正 | 台帳を読み取る；ディレクティブエッジ（ライブキュー+コールドアーカイブ）を通じてのみ操縦 |
| **Scout** *(オプション)* | クリティカルパスから離れて境界付けられた質問を調査 | 参照時にのみ読み取られる調査結果ファイルを書き込む |

負荷支持ルールは**一つのノード=一つのプロンプト+一つの単一ライターエッジ**です。
台帳には正確に一人のライターがいます。スーパーバイザーはエグゼキューターの
コンテキストを決して共有せず、そのスコアボードを編集せず、一方通行の
ディレクティブエッジを通じてのみ操縦します。

すべての制約の背後にある根拠については、
[方法論](lib/methodology.md)を読んでください。ノードとエッジモデルについては、
[loop-graphモデル](skills/loop-graph/docs/model.md)を参照してください。

## ホスト互換性

| ホスト | loop-graph実行 |
| --- | --- |
| [**Codex**](skills/loop-graph/references/codex.md) | ✅ ホストを検出し、両方のランタイムノードを直接作成 |
| [**Claude Code**](skills/loop-graph/references/claude-code.md) | ✅ ホストを検出し、能力チェックが通過すると2つのバックグラウンドランタイムセッションを直接作成 |
| [**Grok Build**](skills/loop-graph/references/grok.md) | プロンプトのみ—2つの`/loop`タスク（executor + supervisor）、ウェイクエッジなし |
| [**Cursor**](skills/loop-graph/references/cursor.md) | プロンプトのみ実行ターゲット |
| [**shell / cron**](skills/loop-graph/references/shell-cron.md) | プロンプトのみ実行ターゲット |

権威ある構文、ペーシング、コンテキストキャリー、およびフックは別々の
[ホストごとのリファレンス](skills/loop-graph/references/)に存在するため、オーサリングは選択されたホストのみを読み込みます。実行中のホスト切り替えは同じ
永続的実行ディレクトリを再利用します；各ティックの開始方法のみが変わります。

## リポジトリマップ

| パス | 目的 |
| --- | --- |
| [ルート`SKILL.md`](SKILL.md) | `/longgraph`ルーター；集中パックまたはカスタムコンパイラパスを選択 |
| [Loop-graphコンパイラ](skills/loop-graph/SKILL.md) | 共有executor、supervisor、ledger、directive、およびopsアーティファクトを生成 |
| [loop-converge](skills/loop-converge/SKILL.md) | プリセットエントリ：コード収束インタビュー→同じloop-graphコンパイル |
| [loop-deliver](skills/loop-deliver/SKILL.md) | プリセットエントリ：要件配信インタビュー→同じコンパイル |
| [loop-research](skills/loop-research/SKILL.md) | プリセットエントリ：証拠主導ソリューション選択インタビュー→同じコンパイル |
| [プリセット契約](skills/loop-graph/docs/preset-contract.md) | 共有コンパイラとゴール固有パック間の境界 |
| [`lib/`](lib) | 共有方法論 |
| [ホストリファレンス](skills/loop-graph/references) | 各ホストのランタイム事実のための一つの独立して読み込まれる所有者 |
| [実例](skills/loop-graph/examples) | 公開Git自己反復+動作中のゲートを示す架空の台帳 |
| [公開/プライベート境界](docs/public-private-boundary.md) | 公開ツリーに入る可能性があるものとプロジェクトローカルのままであるもの |
| [Runner CLI](runner/README.md) | コンパイル済み run ディレクトリ用エンジン — `--host prompt-only`（安全なデフォルト）、`grok-bot` DualTimer、`mock` はテスト専用。バージョン文字列 `0.3.0-beta`（未タグ） |
| [公開クレーム](docs/ship/PUBLIC_CLAIMS.md) | P1–P10 を既存 pytest 名に束縛（宣伝文ではない） |
| [CHANGELOG](CHANGELOG.md) | Phase 0–1c + H0–H2 の要点。tag は owner のみ |
| [既知の問題](KNOWN_ISSUES.md) | D2 のコーディング Major はクローズ；soak / DualTimer はタイマーのみ / テレメトリ残留 |
| [SECURITY.md](SECURITY.md) | ワークスペース外書き込み拒否、フィクスチャに秘密情報なし、runner は `git push` しない |

## ガバナンス

longgraphは独自のアンチブロートルールをライブラリに適用します：**その価値を証明した
実際の実行なしにプロンプトは入りません。** キュレーションされ、意見があるものが
包括的なものを上回ります。

貢献は歓迎します。[貢献ガイド](CONTRIBUTING.md)から始めてください。

## 🔒 セキュリティとプライバシー

このフォークには追加のセキュリティツールが含まれています：

```bash
# .longgraphディレクトリをコミット前にスキャン
./scripts/scrub-longgraph-secrets.sh

# 特定の実行をスキャン
./scripts/scrub-longgraph-secrets.sh .longgraph/2026-09-08-auth-migration

# ドライランでスキャン内容を確認
./scripts/scrub-longgraph-secrets.sh --dry-run
```

詳細は[FORK.md](FORK.md)を参照してください。

## 📊 可観測性

実行ステータスを追跡するには：

```bash
# すべての実行のステータスを確認
find .longgraph -name status.json -exec jq . {} \;
```

スキーマと統合の詳細については、[docs/observability/status-schema.md](docs/observability/status-schema.md)を参照してください。

## クレジット

loop-graphスキルは実際の実行とコミュニティの入力から成長しました。
[公開Git自己反復ケース](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md)
は、メソッドがこのライブラリに硬化された方法を記録しています。特別な感謝を
[@BrightProgrammer7](https://github.com/BrightProgrammer7)に、`migrate-blob-storage`の例と、マイルストーン
ゲートとノード/エッジの語彙を研ぎ澄ました議論に対して。

このフォークの拡張機能は[Samek86](https://github.com/Samek86)によって保守されています。

## ライセンス

[MIT](LICENSE) © 2026 [levi-qiao](https://github.com/levi-qiao)

フォーク拡張 © 2026 [Samek86](https://github.com/Samek86)
