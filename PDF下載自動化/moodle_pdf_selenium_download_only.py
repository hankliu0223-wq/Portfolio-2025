#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moodle PDF 下載器（純 Selenium 版）
流程：
1) 打開 Chrome 到課程頁 → 你登入，直到看得到課程內容
2) 回到終端機按 Enter
3) 程式在瀏覽器裡深入掃描連結並逐一開啟 PDF，Chrome 會自動下載到指定資料夾
※ 僅下載 Moodle 主機上的 PDF（.pdf / pluginfile.php），外站（Google Drive/OneDrive）不處理
"""

import re, time, argparse
import json
from urllib.parse import urlparse, parse_qsl, urlunparse, unquote

# 這些查詢參數常造成「同檔不同URL」的假象：去掉它們來做去重鍵
_SKIP_QUERY_KEYS = {"forcedownload", "download", "redirect", "token", "sesskey", "expires", "v", "t"}

def canon_key(url: str) -> str:
    """
    把 URL 正規化成可比對的 key：
    - 移除 fragment (#...) 與容易變動/無關的 query 參數
    - 只保留 scheme/host/path（避免 token/redirect 造成重複）
    """
    pu = urlparse(url)
    path = pu.path.rstrip("/")  # 去掉尾端斜線
    # 過濾常見造成重複的 query 參數（保留其他有意義的參數）
    # （純 Moodle PDF 多半不需要 query 就能唯一辨識）
    # q = [(k, v) for k, v in parse_qsl(pu.query, keep_blank_values=True) if k.lower() not in _SKIP_QUERY_KEYS]
    # 若你想更激進：直接完全忽略 query（最不會重複）
    q = []
    canon = urlunparse((pu.scheme.lower(), pu.netloc.lower(), path, "", "", ""))  # scheme://host/path
    return canon

def guess_filename_from_url(url: str) -> str:
    """從 URL 最後一段猜檔名（用來判斷本地是否已存在）"""
    pu = urlparse(url)
    name = unquote(pu.path.split("/")[-1]) or "file.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    # 你的程式裡已有 safe_name，可沿用
    return safe_name(name)

from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome Safari")

# ---------- 小工具 ----------
def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()

def looks_moodle_inner(url: str) -> bool:
    low = url.lower()
    return any(p in low for p in [
        "/mod/resource/view.php",
        "/mod/folder/view.php",
        "/mod/url/view.php",
        "/mod/book/view.php",
        "/mod/page/view.php",
    ])

def looks_pdfish(url: str) -> bool:
    low = url.lower()
    return low.endswith(".pdf") or "pluginfile.php" in low

def extract_links(base_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    found = []

    # a[href]
    for a in soup.find_all("a", href=True):
        found.append(urljoin(base_url, a["href"]))

    # iframe/embed/src
    for tag in soup.find_all(["iframe", "embed"], src=True):
        found.append(urljoin(base_url, tag["src"]))

    # data-url / data-href
    for tag in soup.find_all(attrs={"data-url": True}):
        found.append(urljoin(base_url, tag["data-url"]))
    for tag in soup.find_all(attrs={"data-href": True}):
        found.append(urljoin(base_url, tag["data-href"]))

    # onclick="window.open('...')" / "location.href='...'"
    onclick_re = re.compile(r"(window\.open|location\.href|document\.location)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
    for tag in soup.find_all(onclick=True):
        m = onclick_re.search(tag["onclick"])
        if m:
            found.append(urljoin(base_url, m.group(2)))

    # meta refresh
    for meta in soup.find_all("meta", attrs={"http-equiv": lambda v: v and v.lower() == "refresh", "content": True}):
        m = re.search(r'url=([^;]+)', meta["content"], flags=re.I)
        if m:
            found.append(urljoin(base_url, m.group(1).strip()))

    # resourceworkaround（Moodle 常見）
    for div in soup.find_all("div", class_="resourceworkaround"):
        for a in div.find_all("a", href=True):
            found.append(urljoin(base_url, a["href"]))

    # 去重
    uniq, seen = [], set()
    for u in found:
        if u not in seen:
            uniq.append(u); seen.add(u)
    return uniq

def wait_for_downloads(dirpath: Path, timeout: int = 120):
    """等所有 .crdownload 消失"""
    start = time.time()
    while True:
        tmp = list(dirpath.glob("*.crdownload"))
        if not tmp:
            return True
        if time.time() - start > timeout:
            return False
        time.sleep(0.5)

# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser(description="NCCU Moodle PDF 下載器（純 Selenium 版）")
    ap.add_argument("url", help="課程頁 URL，例如：https://moodle45.nccu.edu.tw/course/view.php?id=10071")
    ap.add_argument("--out", default="downloads", help="下載根目錄（預設 downloads）")
    ap.add_argument("--depth", type=int, default=3, help="深入層數（預設 3）")
    ap.add_argument("--keep", action="store_true", help="下載後保留瀏覽器不關閉")
    args = ap.parse_args()

    # 設定下載資料夾（以課程標題建立子資料夾，先用臨時名，後面會更新）
    base_out = Path(args.out).resolve()
    base_out.mkdir(parents=True, exist_ok=True)
    course_dir = base_out / "moodle_course_tmp"
    course_dir.mkdir(exist_ok=True)

    # 配置 Chrome：自動下載 PDF、不彈窗
    opts = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": str(course_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # 不用內建 PDF 檢視器，直接下載
    }
    opts.add_experimental_option("prefs", prefs)
    opts.add_argument(f"user-agent={UA}")

    driver = webdriver.Chrome(options=opts)
    driver.get(args.url)
    print("\n[操作] 已開啟 Chrome。請在瀏覽器中完成 NCCU Moodle 登入，直到能看到課程『內容列表』。")
    input("→ 登入完成後，回到此終端機按 Enter 繼續… ")

    # 取得課程標題，更新下載資料夾名
    title = driver.title.strip() or urlparse(args.url).path
    nice = safe_name(title)
    new_dir = base_out / nice
    if new_dir != course_dir:
        try:
            course_dir.rename(new_dir)
            course_dir = new_dir
        except Exception:
            course_dir = base_out / (nice + "_downloads")
            course_dir.mkdir(exist_ok=True)
    print(f"[i] 下載資料夾：{course_dir}")

    # BFS 掃描
    start_host = urlparse(args.url).netloc
    queue = [(args.url, 0)]
    visited = set()
    pdf_urls = []
    inner_pages = 0

    while queue:
        url, depth = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        if urlparse(url).netloc != start_host:
            continue

        # 瀏覽器前往該頁（確保 Referer/Session 正確）
        driver.get(url)
        time.sleep(0.8)  # 簡單等待頁面渲染
        html = driver.page_source

        links = extract_links(url, html)
        for link in links:
            if looks_pdfish(link):
                if link not in pdf_urls:
                    pdf_urls.append(link)
            elif looks_moodle_inner(link) and depth < args.depth:
                queue.append((link, depth + 1))

        inner_pages += 1

    print(f"[i] 掃描完成：內頁 {inner_pages} 個，PDF 連結 {len(pdf_urls)} 個。")

    # 逐一觸發下載（開新分頁 → 等下載 → 關分頁）
    if not pdf_urls:
        print("  [i] 找不到 Moodle 主機上的 PDF（可能都是外站連結或非 PDF）。")
    else:
        main_tab = driver.current_window_handle
        ok = 0
        for i, url in enumerate(pdf_urls, 1):
            print(f"  ({i}/{len(pdf_urls)}) 下載：{url}")
            driver.execute_script("window.open(arguments[0], '_blank');", url)
            driver.switch_to.window(driver.window_handles[-1])
            # 等 PDF 下載（如果 Chrome 直接打開檔案，也會因為 prefs 設定而自動下載）
            time.sleep(1.5)
            driver.close()
            driver.switch_to.window(main_tab)

            # 等下載穩定（沒有 .crdownload）
            wait_for_downloads(course_dir, timeout=180)
            ok += 1

        print(f"\n完成。嘗試下載 {len(pdf_urls)} 個，已觸發下載 {ok} 個。檔案在：{course_dir}")

    if not args.keep:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    main()
## python moodle_pdf_selenium_download_only.py "網址" --depth 3
