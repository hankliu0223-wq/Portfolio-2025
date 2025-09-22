#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, re, shutil
from pathlib import Path

# 支援的重複命名樣式：
#   filename (1).pdf   filename(1).pdf   filename 2.pdf
PATTERNS = [
    re.compile(r"^(?P<base>.+?) \((?P<n>\d+)\)\.(?P<ext>[^.]+)$", re.IGNORECASE),
    re.compile(r"^(?P<base>.+?)\((?P<n>\d+)\)\.(?P<ext>[^.]+)$", re.IGNORECASE),
    re.compile(r"^(?P<base>.+?) (?P<n>\d+)\.(?P<ext>[^.]+)$", re.IGNORECASE),
]

def candidate_base(path: Path) -> Path | None:
    name = path.name
    for pat in PATTERNS:
        m = pat.match(name)
        if m:
            base = m.group("base").strip()
            ext  = m.group("ext")
            return path.with_name(f"{base}.{ext}")
    return None

def main():
    ap = argparse.ArgumentParser(description="清除重複命名檔案（預設搬到 _dupe_trash）")
    ap.add_argument("--dir", default=str(Path.cwd() / "downloads"),
                    help="要掃描的資料夾（可用 ~/Downloads）")
    ap.add_argument("--ext", default="pdf",
                    help="限定副檔名（逗號分隔，空字串=全部），例：pdf,pptx,docx")
    ap.add_argument("--delete", action="store_true",
                    help="直接刪除（預設只是搬到 _dupe_trash）")
    ap.add_argument("--dry-run", action="store_true",
                    help="預演模式：只列出將處理的檔案，不實際動作")
    args = ap.parse_args()

    target = Path(args.dir).expanduser().resolve()
    if not target.exists():
        print(f"[x] 目錄不存在：{target}")
        return

    exts = set(e.lower().strip().lstrip(".") for e in args.ext.split(",") if e.strip())
    trash = target / "_dupe_trash"
    count = 0

    def is_wanted(file: Path) -> bool:
        return (not exts) or (file.suffix.lower().lstrip(".") in exts)

    print(f"[i] 掃描目錄：{target}")
    for p in target.rglob("*"):
        if not p.is_file():
            continue
        if not is_wanted(p):
            continue

        base = candidate_base(p)
        # 只在「同資料夾裡存在 base 檔名」時才視為重複
        if base and base.exists() and base.parent == p.parent:
            action = "DELETE" if args.delete else "MOVE"
            print(f"[{action}] {p.relative_to(target)}  （原始：{base.name}）")

            if args.dry_run:
                count += 1
                continue

            if args.delete:
                try:
                    p.unlink(missing_ok=True)
                    count += 1
                except Exception as e:
                    print("  [!] 刪除失敗：", e)
            else:
                try:
                    trash.mkdir(parents=True, exist_ok=True)
                    dest = trash / p.name
                    i = 1
                    while dest.exists():
                        dest = trash / f"{p.stem}__dupe{i}{p.suffix}"
                        i += 1
                    shutil.move(str(p), str(dest))
                    count += 1
                except Exception as e:
                    print("  [!] 搬移失敗：", e)

    print(f"\n完成。{'刪除' if args.delete else '搬移'} {count} 個重複檔。")
    if not args.delete and count:
        print(f"  → 已移到：{trash}")

if __name__ == "__main__":
    main()
#刪Mac          python clean_dupes.py --dir "~/Downloads" --ext pdf
#刪專案Downloads python clean_dupes.py --dir "./downloads" --ext pdf
#刪除檔案        python clean_dupes.py --dir "~/Downloads" --ext pdf --delete
