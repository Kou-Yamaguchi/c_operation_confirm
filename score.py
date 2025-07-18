#!/usr/bin/env python3
import os
import subprocess, argparse
import shutil
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

TIMEOUT_SEC = 2  # 実行時間の上限（無限ループ対策）
CFLAGS = ["-std=c11", "-Wall", "-Wextra", "-O2"]


def compile_c(src: Path, exe: Path):
    """gcc でコンパイルし、成功なら True"""
    try:
        subprocess.run(
            ["gcc", *CFLAGS, "-o", str(exe), str(src)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def run_tests(exe: Path, tests_dir: Path, work_dir: Path ,read_file: Path = None) -> tuple[bool, str]:
    """準備済みテスト全てを回し、1つでも失敗すれば False"""

    all_ok = True
    review_msgs = []

    if read_file and not read_file.exists():
        raise FileNotFoundError(f"課題実行時に読み込むファイルが見つかりません: {read_file}")
    
    if read_file and read_file.exists():
        cp_path = Path(shutil.copy2(read_file, work_dir))  # 課題実行時に読み込むファイルをコピー

    for infile in sorted(tests_dir.glob("*.in")):
        tname = infile.stem  # test1, test2, ...
        exp = tests_dir / f"{tname}.out"

        if not exp.exists():
            raise FileNotFoundError(f"期待出力ファイルが見つかりません: {exp}")

        in_data = infile.read_bytes()
        try:
            result = subprocess.run(
                ["./" + os.path.basename(exe)],
                # input=infile.read_text(), string 入力が必要な場合はこれを使う
                input=in_data,  # バイナリ入力が必要な場合はこれを使う
                # capture_output=True,
                # text=True,
                cwd=work_dir,  # 作業ディレクトリを指定
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired:
            review_msgs.append(f"{tname}: タイムアウト({TIMEOUT_SEC}s 超過)")
            all_ok = False
            break

        out_text = result.stdout.decode("utf-8", errors="replace")

        if result.returncode != 0:
            return False, f"{tname}: 戻り値 {result.returncode}"
        # 改行・空白を丸めて比較
        out_norm = " ".join(out_text.split())
        exp_norm = " ".join(exp.read_text().split())
        if out_norm == exp_norm:
            continue
        else:
            review_msgs.append(f"{tname}: 出力不一致\n  期待: {exp_norm}\n  実際: {out_norm}")
            all_ok = False

    if cp_path and cp_path.exists():
        try:
            cp_path.unlink()  # 課題実行時に読み込むファイルを削除
        except FileNotFoundError:
            pass

    return all_ok, "\n".join(review_msgs) if review_msgs else "全てのテストに合格しました"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--submits", required=True, type=Path, help="学生フォルダが入った親ディレクトリ"
    )
    ap.add_argument(
        "--tests", required=True, type=Path, help="テストケースを置いたディレクトリ"
    )
    ap.add_argument(
        "--readfile", type=Path, default=None, help="課題実行時に読み込むファイル (オプション, 課題による)"
    )
    ap.add_argument(
        "--writefile", type=str, default=None, help="課題実行時に書き込むファイル (オプション, 課題による)"
    )
    ap.add_argument(
        "--roster", required=True, type=Path, help="学生名簿ファイル xlsx (1行目ヘッダ: 学籍番号, 名前, ...)"
    )
    ap.add_argument("--outfile", default="result.xlsx", help="結果出力ファイル名")
    args = ap.parse_args()

    records = {}

    skip_ids = [
        # 不具合があるなど、特定の学生の提出をスキップする場合はここに追加
        # 例: "1234567",
    ]

    for student_dir in tqdm(sorted(args.submits.iterdir()), desc="採点中", unit="件"):
        if not student_dir.is_dir():
            continue
        # 例: 0000001-0.c, 0000001-1.c ... -> 一番後ろ(最新)を採点対象に
        c_files = sorted(student_dir.glob("*.c"))
        if not c_files:
            continue  # Cファイルがない場合はスキップ

        src = c_files[-1]
        # print(f"採点対象: {src}")
        exe = src.with_suffix("")  # ./student_name/0000001-0

        ok_compile, msg_compile = compile_c(src, exe)

        student_id = src.stem.split("-")[0]

        if student_id in skip_ids:
            # 特定の学生の提出をスキップする場合
            print(f"Skipping student {student_id} due to skip list.")
            continue

        if not ok_compile:
            records[student_id] = {
                "student_id": student_id,
                "compile": "NG",
                "test": "NA",
                "detail": msg_compile.splitlines()[-1],
            }
            continue

        ok_test, msg_test = run_tests(exe, args.tests, student_dir, args.readfile)
        records[student_id] = {
            "student_id": student_id,
            "compile": "OK",
            "test": "OK" if ok_test else "NG",
            "detail": msg_test
        }

        # 後始末
        try:
            exe.unlink()
        except FileNotFoundError:
            pass

    roster = pd.read_excel(args.roster, dtype={"学籍番号": str})
    roster = roster.rename(columns={"学籍番号": "student_id", "名前": "name"})

    final_rows = []
    for _, row in roster.iterrows():
        student_id = row.student_id
        rec = records.get(
            student_id, {"student_id": student_id, "compile": "NA", "test": "NA", "detail": "未提出"}
        )
        rec["name"] = row.name
        final_rows.append(rec)

    # 名簿外・提出フォーマットが崩れている学生の提出も追加
    extras = [
        v | {"name": ""}
        for k, v in records.items()
        if k not in roster.student_id.values
    ]
    extras.sort(key=lambda x: x["student_id"])
    final_rows.extend(extras)

    def sanitize_text(text):
        """Excelに書き込む前に不正な文字を除去"""
        return ILLEGAL_CHARACTERS_RE.sub("", text) if isinstance(text, str) else text
    
    df = pd.DataFrame(final_rows)
    df = df.map(sanitize_text)  # 全てのセルに適用
    df.to_excel(args.outfile, index=False)

    # pd.DataFrame(final_rows).to_excel(args.outfile, index=False)
    print(f"結果を {args.outfile} に保存しました ({len(final_rows)} 件)")


if __name__ == "__main__":
    main()
