# 🐾 Animalia

**Animalia** は、動物好きのための SNS アプリです。  
ユーザーはペットの写真を投稿・閲覧・いいね・コメントでき、他ユーザーと交流することができます。  
また、独自の推薦アルゴリズムやタスク管理機能も搭載しており、よりパーソナライズされた体験を提供します。

---

## 🚀 起動方法

このプロジェクトは、`Makefile` を通じて各種サービスを簡単に起動できるようになっています。

### バックエンド（Go + Docker）

```bash
cd animalia
make run
```

初回実行時にデータベースの初期データを投入したい場合は以下のコマンドを使います：

```bash
make run-seed
```

Lambdaのビルドとデプロイを行いたい場合は：

```bash
make deploy
```

---

### フロントエンド（React Native / Expo）

Animalia のモバイルアプリは [Expo](https://expo.dev/) を使って構築されています。  
以下の手順でローカル環境で起動できます。

#### ✅ 必要な環境

- Node.js（推奨: v18以上）  
  バージョン管理には [nvm](https://github.com/nvm-sh/nvm) の使用を推奨します。
- npm または yarn
- Expo CLI（`npx` 経由で利用可能）

#### 📦 セットアップ手順

```bash
# フロントエンドディレクトリに移動
cd animalia/app-front

# 依存パッケージのインストール
npm install
```

#### 🚀 起動

```bash
npx expo start
```

実行後、QRコードが表示されるので、Expo Go アプリ（iOS/Android）でスキャンすることで実機で確認できます。

#### 🔐 `.env` ファイルについて

このアプリケーションの起動には `.env` ファイルが必要です。  
`.env` にはAPIの接続先などの環境変数が含まれており、セキュリティ上の理由からリポジトリには含まれていません。

> `.env` ファイルは開発者にお問い合わせください。

---

## 🗂 ディレクトリ構成

```
.
└── animalia
    ├── Makefile
    ├── README.md
    ├── algorithm
    │   ├── common
    │   ├── recommend_system
    │   ├── search_engine
    │   └── task_scoring_system
    ├── app-front
    │   ├── app
    │   ├── assets
    │   ├── components
    │   ├── constants
    │   ├── features
    │   ├── hooks
    │   ├── providers
    │   ├── scripts
    │   └── utils
    ├── backend-go
    │   ├── aws
    │   ├── cmd
    │   ├── ent
    │   └──internal
    │       ├── domain
    │       ├── handler
    │       ├── infra
    │       ├── injector
    │       ├── routes
    │       ├── seed
    │       └── usecase
    └── db
        └── Dockerfile
```

本プロジェクトは、動物系SNSアプリ「Animalia」のフルスタック構成であり、以下のように機能ごとにディレクトリが整理されています。

- **`algorithm/`**  
  推薦システム・検索エンジン・スコアリング処理など、機械学習・自然言語処理を含むアルゴリズム群を管理しています。  
  `common/` や `recommend_system/` など、目的別に細かく分割されています。

- **`app-front/`**  
  React Native（Expo）を用いたフロントエンドアプリケーションです。  
  画面構成、UIコンポーネント、ドメイン別機能、状態管理、フックなどがビジネスロジックごとに整理されています。


  本プロジェクトでは、Feature-Sliced Design (FSD) を採用しています。
  features/ ディレクトリには、auth や post、like などのユーザー操作単位の機能を集約しており、各機能が独立して保守・拡張しやすい構造となっています。



- **`backend-go/`**  
  Go言語を使ったバックエンドで、Clean Architecture に準拠した構造になっています。  
  - `cmd/`: Lambda 関数の定義と、それぞれの関数のエントリーポイントを配置  
  - `aws/`: CDK によるインフラ定義  
  - `ent/`: ORM（ent）によるモデル定義  
  - `internal/`: ドメイン・ユースケース・インフラ連携など、アプリケーションコアロジック  
    - `domain/`, `usecase/`, `handler/`, `routes/`, `infra/`, `seed/`, `injector/` などに整理されています。

- **`db/`**  
  ローカル開発・CI環境用のデータベース定義を含むディレクトリで、`Dockerfile` によりDBコンテナを構築します。

このように、Animalia はフロント・バック・アルゴリズム・インフラの各層が適切に分離されており、拡張性と保守性に優れた構成となっています。

## バックエンドのテストについて

本プロジェクトのバックエンドでは、**ユースケース層（Usecase Layer）** を中心に、自動テストを整備しています。  
**依存するリポジトリや外部サービスをモック化**し、ビジネスロジックの挙動のみを厳密に検証する構成としています。

### ✅ テスト設計のポイント

- **ユースケース単位の責務を明確化**し、それぞれ独立して検証可能に設計
- `ent` を用いた DB エンティティを使用しつつも、`repository/mock` を使って**実行対象を限定**
- `assert` を活用し、**出力・副作用・失敗パターンまで網羅**
- 各処理が **正常系 / 異常系の両面**から正しく動作するかを確認

---

### 🔗 関連ファイル構成（例）

```
backend-go/
├── internal/
│   └── usecase/
│       └── comment_test.go   # ユースケースのテスト
│
├── internal/
│   └── domain/
│       └── repository/
│           └── mock/                # テスト用のモックリポジトリ
```
```
