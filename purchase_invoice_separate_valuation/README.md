# Purchase Invoice Separate Valuation

## 概要

このモジュールは、Odoo 16.0において仕入先請求書の作成と在庫評価を完全に分離する機能を提供します。

## 機能

### 1. 複数請求書作成機能
- 従来のOdooでは1つの購買オーダに対して請求済数量が管理されているため、複数回の請求書作成が制限されていました
- このモジュールにより、「最終請求」フラグがOFFの場合は何度でも請求書を作成できます

### 2. 在庫評価からの完全分離
- **すべての仕入先請求書（非最終・最終含む）**で、stock.valuation.layerへの直接的な影響を排除
- 請求書計上は単純に仕入先負債（買掛金）のみを計上
- 在庫評価は入庫時の価格で確定し、請求書では変更されません

### 3. 最終請求によるGRNI残高調整
- 最終請求フラグがONの請求書確定時に、**別の調整仕訳**を自動作成
- この調整仕訳は以下を実現：
  - 入庫時に計上されたGRNIと、POに紐づく請求書のGRNI合計を比較
  - GRNI（Stock Interim Received / 受入未請求）勘定の残高をゼロに調整
  - 仕入差額勘定に差分を反映

### 4. 購買オーダステータス管理
- 最終請求確定時に購買オーダが「請求済」ステータスに変更

## 仕組み

### 入庫時
```
在庫資産 10,000 / GRNI 10,000  （入庫時の標準価格/FIFO価格で計上）
```

### 非最終請求書（5,000円）
```
GRNI 5,000 / 買掛金 5,000  （在庫評価には影響なし）
```

### 最終請求書（5,000円）
```
【請求書仕訳】
GRNI 5,000 / 買掛金 5,000  （通常の請求書計上）

【自動作成される価格差異調整仕訳】
（調整仕訳は作成されません - 合計10,000円で入庫時と一致）
```

### 最終請求書でのGRNI調整例（合計12,000円の場合）
```
【請求書仕訳】
GRNI 7,000 / 買掛金 7,000  （残りの請求）

【自動作成される価格差異調整仕訳】
仕入差額 2,000 / GRNI 2,000  （入庫10,000円 vs 請求12,000円の差額）
```

## 使用方法

### 1. 通常の請求書作成（最終請求OFF）
```
購買管理 → 購買オーダ → [オーダを選択] → 「Create Invoice (Advanced)」ボタン
→ 「Final Invoice」のチェックをOFFのまま → 「Create Invoice」
```

### 2. 最終請求書作成（最終請求ON）
```
購買管理 → 購買オーダ → [オーダを選択] → 「Create Invoice (Advanced)」ボタン
→ 「Final Invoice」をチェックON → 「Create Invoice」
```

確定すると、GRNI調整仕訳が自動的に作成され、請求書フォームの「Price Adjustment Entry」フィールドからアクセスできます。

## 技術仕様

### オーバーライドされるメソッド

1. **account.move._post()**
   - すべての仕入先請求書でpurchase_stockのAnglo-Saxon処理をバイパス
   - 最終請求書確定時に`_sync_price_adjustment_entry()`を呼び出し

2. **account.move._sync_price_adjustment_entry()**
   - 最終請求書専用の新規メソッド
   - PO単位でGRNIの受領・請求合計を比較
   - 別の仕訳（account.move）としてGRNI調整を起票

3. **account.move.line._create_stock_valuation_layer()**
   - 仕入先請求書起因のvaluation layer作成をブロック

4. **purchase.order.line._compute_qty_invoiced()**
   - 最終請求フラグがONの請求書のみをqty_invoiced計算に含める

### 新しいフィールド

- **account.move.is_final_invoice**: 最終請求フラグ（Boolean）
- **account.move.price_adjustment_move_id**: 価格調整仕訳へのリンク（Many2one）

### 新しいウィザード

- **purchase.make_invoice_advance**: 拡張請求書作成ウィザード

## インストール

1. モジュールをaddons-pathにコピー
2. Odooを再起動
3. アプリメニューで「Purchase Invoice Separate Valuation」を検索してインストール

## 依存関係

- purchase
- purchase_stock
- stock_account  
- account

## ライセンス

AGPL-3

## 著者

作成日: 2026年1月28日
