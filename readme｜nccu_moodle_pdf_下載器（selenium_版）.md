# NCCU Moodle PDF 下載器（純 Selenium 版）

> 一鍵掃描指定課程頁，登入後自動找出 **Moodle 主機上的 PDF**，逐一觸發下載到指定資料夾。外站（Google Drive/OneDrive）不處理。

---

## ✨ 功能特色
- **人工登入、程式下載**：你在 Chrome 親自登入，程式再接手抓取（避免 Cookie/SSO 麻煩）。
- **只抓 Moodle 站內 PDF**：包含 `pluginfile.php` 直連檔案；**不會**去抓 Google Drive/OneDrive 等外站。
- **自動建立課程資料夾**：以課程標題命名，方便整理。
- **BFS 方式深入頁面**：沿著課程內頁（resource/folder/url/page/book）最多往下爬 `--depth` 層。
- **避免重複下載**：內建 URL 正規化（去除 token/redirect 等易變參數）。

---

## 🧰 需求環境
- Python 3.9+（3.8 以上也多半可）
- Google Chrome（最新版）
- Selenium 4.6+（含 Selenium Manager，可自動處理驅動）
- 需要套件：`selenium`、`beautifulsoup4`

```bash
# 建議先建立虛擬環境
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate        # Windows PowerShell

pip install --upgrade pip
pip install selenium beautifulsoup4
```

> 若遇到驅動無法自動下載，可另外安裝 ChromeDriver 或改用 `webdriver-manager`（非必要）。

---

## 🚀 快速開始（Quick Start）

```bash
python moodle_pdf_selenium_download_only.py "<課程頁 URL>" --depth 3 --out downloads
```

### 例子
```bash
python moodle_pdf_selenium_download_only.py "https://moodle45.nccu.edu.tw/course/view.php?id=10071" --depth 3
```

**流程**
1. 程式會啟動 Chrome 並開到你提供的課程頁。
2. 你在瀏覽器**自行登入** NCCU Moodle，直到看得見課程內容列表。
3. 回到終端機按 **Enter**，程式開始掃描並逐一開啟 PDF，Chrome 會**直接下載**檔案到指定資料夾。

---

## 🧪 指令參數（CLI）
| 參數 | 型態/預設 | 說明 |
|---|---|---|
| `url` | 必填 | 課程頁 URL，例如 `https://moodle45.nccu.edu.tw/course/view.php?id=10071` |
| `--out` | 預設 `downloads` | 下載根目錄；會在裡面建立一個以課程標題命名的資料夾 |
| `--depth` | 預設 `3` | 向下爬的層數（僅針對 Moodle 內頁：resource/folder/url/page/book） |
| `--keep` | flag | 下載後**保留**瀏覽器不關閉（除錯好用） |

---

## 📂 下載檔案存放位置
- 首次會先在 `--out` 目錄下建立 `moodle_course_tmp`。
- 取得課程標題後，會將資料夾**更名**為課程標題（已做安全字元處理）。
- 下載完成的 PDF 都會在該課程資料夾內。

---

## 🔍 它怎麼找連結？（擷取邏輯）
- 解析 HTML，收集：
  - `a[href]`、`iframe[src]`、`embed[src]`
  - `data-url`、`data-href`
  - `onclick` 中的 `window.open('...')` / `location.href='...'`
  - `meta http-equiv=refresh` 的目標 URL
  - Moodle 常見的 `.resourceworkaround` 區塊中的連結
- 只把**同主機**的內頁加入佇列（避免跳出 Moodle 網域）。
- 以 **BFS**（廣度優先）方式逐層擴張，最多 `--depth` 層。
- 判斷 PDF 的方式：
  - 連結結尾是 `.pdf` 或
  - URL 中包含 `pluginfile.php`
- **URL 正規化**：
  - 去除 fragment `#...`
  - 忽略常見易變 query（`forcedownload`、`download`、`redirect`、`token`、`sesskey`、`expires`、`v`、`t`）

---

## 🖥️ 典型輸出
```
[i] 下載資料夾：/your/path/downloads/課程名稱
[i] 掃描完成：內頁 17 個，PDF 連結 9 個。
  (1/9) 下載：https://moodle.../pluginfile.php/...
  ...
完成。嘗試下載 9 個，已觸發下載 9 個。檔案在：/your/path/downloads/課程名稱
```

---

## 🧯 常見問題（FAQ / Troubleshooting）
**Q1. 明明有連結，為什麼沒抓到？**  
A：可能是外站（Google Drive/OneDrive），本程式只抓 **Moodle 主機**檔案。也可能連結是動態載入，等待時間可自行加長 `time.sleep()`。

**Q2. 下載沒有動靜 / 只開啟預覽？**  
A：已設定 `plugins.always_open_pdf_externally=True`，理論上會**直接下載**。若仍出現內建預覽，請確認 Chrome 設定是否被政策鎖定、或嘗試將 PDF 檔另開新分頁後再關閉。

**Q3. 驅動相容性錯誤（driver version mismatch）？**  
A：升級 Selenium 至 4.6+（內建 Selenium Manager），或手動安裝對應版本的 ChromeDriver。

**Q4. 想抓非 PDF（如 PPTX/DOCX）？**  
A：修改 `looks_pdfish()`：
```python
return low.endswith((".pdf", ".pptx", ".docx")) or "pluginfile.php" in low
```

**Q5. 權限/403？**  
A：請確保你在**同一個 Chrome** 分頁已登入且有課程權限，並於終端機按 Enter 後再開始爬取。

---

## 🔐 法規與道德
- 僅供**個人學習備份**與課程使用；請遵守學校與 Moodle 之**使用條款**。
- 請勿將受版權保護之教材**公開散佈**或作為商業用途。

---

## 🗂️ 專案結構建議
```
repo/
├─ moodle_pdf_selenium_download_only.py
├─ requirements.txt
├─ README.md
└─ downloads/                  # 下載輸出（可忽略追蹤）
```

**requirements.txt**（可直接建立）
```
selenium>=4.6
beautifulsoup4
```

**.gitignore**（選擇性）
```
.venv/
__pycache__/
*.pyc
downloads/
```

---

## 👨‍💻 使用說明（逐步版）
1. 建立虛擬環境並安裝套件。
2. 執行指令，Chrome 會自動開啟到課程頁。
3. 在 Chrome 完成登入，回到終端機按 Enter。
4. 等待下載完成（會自動等待 `.crdownload` 消失）。
5. 打開 `downloads/課程名稱/` 查看所有 PDF。

---

## 🧠 迷你名詞小卡
- **Selenium**：讓 Python 操控瀏覽器（開頁、點擊、輸入）的工具。
- **BeautifulSoup**：解析 HTML，幫你「找出頁面上的連結」。
- **BFS（廣度優先）**：一圈一圈往外擴，確保不會迷路且有層數上限。
- **`pluginfile.php`**：Moodle 站內實際提供檔案的路徑，常見於附件下載。

---

## 🛣️ Roadmap（可選）
- [ ] 加入非 PDF 檔案型別支援（PPTX/DOCX/ZIP）。
- [ ] 平行下載與進度列。
- [ ] `--headless` 參數（無頭瀏覽器）。
- [ ] 排程與多課程列表批次處理。

---

## 🤝 貢獻方式
1. Fork 本倉庫、建立分支（`feat/xxx`）。
2. 開發與測試。
3. 發 PR，說明動機與變更內容。

---

## 🧾 授權（License）
- 預設建議 MIT；若含校內教材，請依原授權限制使用。

---

## 📬 聯絡
- 作者：劉永漢NCCU）
- Email：hankliu0223@gmail.com
- Issues：歡迎提問/回報 bug


