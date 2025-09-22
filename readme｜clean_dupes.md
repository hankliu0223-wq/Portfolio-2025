# clean_dupes.py｜重複命名清除工具（macOS/Windows/Linux）

> 一鍵整理下載夾或專案資料夾，把像 **`檔名 (1).pdf`、`檔名(2).pdf`、`檔名 3.pdf`** 這種重複命名的檔案**移到垃圾區**（預設不直接刪除）。

---

## ✨ 功能特色
- **支援三種常見重複樣式**：`name (1).ext`、`name(1).ext`、`name 2.ext`。
- **只處理同資料夾的重複**：同一層內若有 `name.ext` 與 `name (1).ext` 才算重複。
- **預設安全**：不刪除，統一移到 `_dupe_trash/`，可回收。
- **副檔名篩選**：`--ext pdf`（或 `pdf,pptx,docx`），留空代表**全部**。
- **遞迴掃描**：包含子資料夾（`rglob('*')`）。
- **乾跑模式**：`--dry-run` 只列清單、不動檔案。

---

## 🧰 環境需求
- Python 3.8+（純標準函式庫：`argparse`、`re`、`shutil`、`pathlib`）
- 不需安裝任何第三方套件

---

## 🚀 快速開始（Quick Start）

### 常用指令
```bash
# macOS：清 ~/Downloads 裡的 PDF 重複檔（移到 _dupe_trash）
python clean_dupes.py --dir "~/Downloads" --ext pdf

# 專案的 downloads 資料夾（PDF）
python clean_dupes.py --dir "./downloads" --ext pdf

# 直接刪除（不可復原，請先 dry-run 確認）
python clean_dupes.py --dir "~/Downloads" --ext pdf --delete

# 預演：只列出會被處理的檔案，不實際搬/刪
python clean_dupes.py --dir "~/Downloads" --ext pdf --dry-run

# 多種副檔名
python clean_dupes.py --dir "~/Downloads" --ext pdf,pptx,docx
```

> **Windows 提示**：用 PowerShell 時，`~` 也可展開到使用者家目錄；若出現路徑含空白，請用引號包起來，例如 `"C:\\Users\\You\\My Downloads"`。

---

## ⚙️ 參數說明（CLI）
| 參數 | 預設 | 說明 |
|---|---|---|
| `--dir` | `./downloads` | 要掃描的資料夾，支援 `~`（家目錄）與相對路徑 |
| `--ext` | `pdf` | 逗號分隔的副檔名清單；留空字串代表**全部副檔名** |
| `--delete` | 關 | 直接刪除（危險）—不移到垃圾區 |
| `--dry-run` | 關 | 預演模式，只列出會處理的檔案 |

---

## 🔍 判斷邏輯（白話）
1. 先把你指定的資料夾**整個往下掃**（子資料夾也一起）。
2. 每個檔名套三種規則去比對：
   - `base (n).ext`  
   - `base(n).ext`  
   - `base n.ext`
3. 如果找到它的**原始檔**（`base.ext`）**就在同一個資料夾**，就視為重複版本：
   - 預設 → **搬到** `_dupe_trash/`（會避免覆蓋，必要時自動加尾碼 `__dupe1`、`__dupe2`…）。
   - `--delete` → **直接刪除**。

**為什麼要確認同一層？**  
避免把不同單元或不同週的同名檔案誤判（他們在不同資料夾，通常不是重複）。

---

## 🖨️ 範例輸出
```
[i] 掃描目錄：/Users/you/Downloads
[MOVE] week01/講義 (1).pdf  （原始：講義.pdf）
[MOVE] week01/講義 2.pdf    （原始：講義.pdf）
[MOVE] 報告(1).pdf          （原始：報告.pdf）

完成。搬移 3 個重複檔。
  → 已移到：/Users/you/Downloads/_dupe_trash
```

---

## 🧪 安全 & 建議流程
1. **先用 `--dry-run` 看清單**。
2. 沒問題再不加 `--dry-run` 正式執行。
3. 如果要**永久刪除**，最後一步才加 `--delete`。

---

## 🧯 常見問題（FAQ）
**Q1. 為什麼某些重複沒有被處理？**  
A：規則只認得三種樣式；如果你的檔名像 `副本`、`copy`、`複製`，請看「自訂規則」。

**Q2. 原始檔不見了，只有 `(1)` 版本，會怎樣？**  
A：不會動。因為找不到 **`base.ext`**，本工具不敢判斷。

**Q3. 可不可以跨資料夾比對？**  
A：目前**不會**。為了安全，僅比對同資料夾的重複。

**Q4. 大小寫副檔名會影響嗎？**  
A：不會，已做小寫化比對。

---

## 🧩 進階：自訂規則（例如支援「副本」、「copy」）
在檔案開頭的 `PATTERNS` 追加 regex，例如：
```python
PATTERNS = [
    # 既有規則...
    re.compile(r"^(?P<base>.+?) - copy\.(?P<ext>[^.]+)$", re.IGNORECASE),
    re.compile(r"^(?P<base>.+?) - 副本\.(?P<ext>[^.]+)$", re.IGNORECASE),
]
```
> 正則說明：`(?P<base>...)` 取出檔名主體，`(?P<ext>...)` 取副檔名；`re.IGNORECASE` = 不分大小寫。

---

## 🗂️ 建議搭配的 .gitignore（若此工具放在專案）
```
_dupe_trash/
```

---

## 🧠 迷你名詞小卡
- **dry-run（預演）**：先看要動哪些檔，不真的動手。
- **rglob**：遞迴找檔，包含子資料夾。
- **unlink**：刪除檔案的系統呼叫（小心使用）。
- **shutil.move**：跨資料夾搬移檔案，會保留原始檔名。

---

## 🧾 授權
- 建議 MIT；若你要公開到 GitHub，請加上 LICENSE。

---

## 📬 聯絡
- 作者：劉永漢（NCCU）
- Email：hankliu0223@gmail.com

---

> 建議把這支工具放在你的專案 repo 根目錄，週週清一次 `downloads/`；若要跟前一支 **Moodle PDF 下載器** 串起來用，先下載、再跑 `clean_dupes.py`，你的資料夾會乾淨很多。
