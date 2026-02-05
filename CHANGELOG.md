# CHANGELOG

このファイルは「Web版 簡易画像処理アプリ（OpenCV + FastAPI + Frontend）」の更新履歴を簡単に記録するためのもの。  
（MVP優先：まず動く → 後で設計に寄せる）

> **表記ルール**  
> **Mod** = “Modification（改造/改修）”の区切り。  
> 日付や作業日（Day）ではなく、**機能が一段まとまって前進した単位**でログを切る（＝改修のまとまり / マイルストーン）。

---

## [Unreleased]

---

## 事前進捗（プロジェクト開始前）
- 設計図（Markdown）を作成済み
- 作業スケジュール（Markdown）を作成済み
- 画像処理コア `proc.py` を先行作成（modeごとの処理関数＋dispatcher構成）
- フロント `index.html` / `main.js` は骨組み作成中（mode選択UIの方針あり）

---

## Mod1（画像処理コアの入口固定）
- `proc.py` の dispatcher（入口）を `select_process(proc_type, img, param)` 形式に整理
- `mode`（例：gray / blur / flip）に応じて処理関数へ振り分ける構造を確立
- パラメータを dataclass（`ProcParam`）にまとめる方針を採用
- 想定外 `mode` は `ValueError` を投げる方針に変更（バック側で400変換しやすくする目的）

---

## Mod2（FastAPIで画像を受け取り、OpenCVでデコード確認）
- FastAPIで `POST /api/process-image` を作成（multipart/form-data）
  - `UploadFile`（file）と `mode`（Form）を受け取る
- 受け取ったファイルを `await file.read()` で bytes 化し、OpenCVでデコード確認
  - `np.frombuffer` → `cv2.imdecode(..., IMREAD_COLOR)` の流れを実装
- バリデーション追加
  - 0バイト（空ファイル）を 400 で拒否（detail: "empty file"）
  - デコード失敗（imdecode が None）を 400 で拒否（detail: "failed to decode image"）
- Swagger UI（/docs）から画像を添付して動作確認し、画像の `shape` をJSONで返すことを確認

---

## Mod3（proc呼び出し＋PNGバイナリ返却、フロント連携成立）
- `main.py` から `proc.py`（`select_process`）を呼び出し、`mode` に応じた画像処理を実行できるようにした
- 処理結果（`np.ndarray`）を `cv2.imencode(".png", ...)` でPNGバイナリ化し、`Response(media_type="image/png")` で返すように変更
- フロント側（fetch → blob → 画像表示）まで一連の流れが成立することを確認
- bytes→OpenCVデコード処理を `decode_byte_image()` として関数化し、処理フローを整理
- （未対応）mode別パラメータ受け渡し、詳細バリデーション、`ValueError` 等の例外をHTTP 4xxへ変換する処理は次Modで対応予定

---

## Mod4（アップロード画像のプレビュー表示、未選択ガード）
- `main.js` を更新し、入力画像プレビュー表示を実装
- `<input type="file">` の `change` イベントでファイルを取得し、`URL.createObjectURL(file)` を用いて `input_preview` に表示
- 画像を再選択した際にメモリ解放できるよう、前回URLを保持して `URL.revokeObjectURL(prevUrl)` を追加
- 実行ボタン（`run`）のクリック処理を追加
- 画像未選択の場合は処理を中断し、`error` 要素へエラー表示するガードを実装

---

## Mod5（フロント⇄APIの安定化：状態表示、CORS、入力チェック、エラー取り回し）
- フロント（Live Server: `http://127.0.0.1:5500`）⇄ FastAPI（`http://127.0.0.1:8000`）で `fetch` によるPOST送信を確立
- `main.js`
  - `FormData` による `multipart/form-data` 送信（`file` / `mode`）を実装
  - `try/catch/finally` と `setLoading()` を導入し、**処理中表示**・**ボタン無効化**・**エラー表示**を安定化
  - `res.ok` を確認し、失敗時は `res.text()` を読んで `throw new Error(...)` でエラー内容を拾えるようにした
  - 結果表示用 `blob URL` も `URL.revokeObjectURL(prevResultUrl)` で解放し、連続実行時のメモリ消費を抑制
- `main.py`
  - CORSエラー対策として `CORSMiddleware` を追加し、`http://127.0.0.1:5500` / `http://localhost:5500` を許可オリジンに設定
  - 入力チェックを追加（最低限の事故防止）
    - 空ファイル（0byte）→ 400
    - Content-Type不正 → 400
    - サイズ上限超過 → 413
    - decode失敗 → 400
    - encode失敗 → 500
  - `proc.py` の `ValueError`（unknown mode）を捕捉して 400（HTTPException）へ変換

---

## Mod6（UI状態管理の改善：busyガード＋処理中表示＋確実な復帰）
- `main.js`
  - **処理中フラグ（`isBusy`）**をグローバルに導入し、実行ボタン連打による **多重実行を防止**（`if (isBusy) return;`）を追加
  - UI切替を `setBusy(isBusy)` に集約し、以下を一括制御できるようにした
    - 実行ボタンの `disabled` 切替
    - ステータス表示（処理中: `"処理中..."`）
    - 処理開始時のエラー表示クリア
  - `fetch` 実行処理を `try/catch/finally` で包み、成功/失敗に関わらず **必ずUIが復帰**するようにした
    - `finally` で `isBusy = false` に戻し、`setBusy(false)`（相当）を呼ぶ

### 現時点の状態
ブラウザ操作のみで「画像選択 → mode選択 → 実行 → サーバで画像処理 → PNG返却 → 結果表示」まで一連の動線が安定して成立。  
加えて、処理中は **状態表示**・**ボタン無効化**・**多重実行防止** が効き、失敗時も **必ずUIが復帰**する。  
（チャンネル数の統一は要件外としてスキップ：`gray` は1chのまま返す方針）

---
