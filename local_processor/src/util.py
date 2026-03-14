import os
import hashlib
import time

#ZIP用
import shutil

from pathlib import Path

ERROR_LOGFILE_NAME = "error.txt"
LOGFILE_NAME = "log.txt"

def output_error_log(output_dir, msg):
    print(msg)
    print(output_dir)
    with open(output_dir + '/' + ERROR_LOGFILE_NAME,"a") as o:
        print(time.strftime("%Y-%m-%d %H:%M:%S:: ", time.localtime()) + str(msg), file=o)

def output_log(output_dir, msg):
    print(msg)
    with open(output_dir + '/' + LOGFILE_NAME,"a") as o:
        print(time.strftime("%Y-%m-%d %H:%M:%S:: ", time.localtime()) + str(msg), file=o)

# 一時保存用のサブフォルダを作成
def make_temp_dir(output_dir, subdir_name):
    target_dir_name = os.path.join(output_dir, subdir_name)
    if not os.path.exists(target_dir_name):
        os.makedirs(target_dir_name)

# ファイルのハッシュ値(SHA-256)を計算    
def calculate_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # ファイルを4096バイトずつ読み込んでハッシュを更新（メモリ節約）
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# from pathlib import Path
# def zip_directory(output_path, target_dir):
#     # 圧縮後のファイル名（拡張子 .zip は自動で付与される）
#     # 例: /app/tmp/2025-10-20.zip
#     #output_path = target_dir

#     # 圧縮実行 (引数: 保存ファイル名, フォーマット, 圧縮したいディレクトリ)
#     print(f"Zip圧縮開始: {target_dir} -> {output_path}.zip")
#     ret = shutil.make_archive(output_path, 'zip', root_dir=target_dir)
#     print(ret)
    
#     print(f"Zip作成完了: {output_path}.zip")
#     return Path(f"{output_path}.zip")


def copy_original_image(input_path, output_dir):
    """
    オリジナルの画像を、ディレクトリ構造を維持または指定フォルダへコピーする
    """
    # Pathオブジェクトに変換しておくと操作が楽です
    src = Path(input_path)
    dst_dir = Path(output_dir)

    # 出力先ディレクトリがなければ作成
    dst_dir.mkdir(parents=True, exist_ok=True)

    # 出力先のフルパスを作成
    dst_path = dst_dir / src.name

    # 既にファイルが存在するかチェック（スキップ処理）
    if dst_path.exists():
        print(f"スキップ: 既にコピー済みです: {dst_path}")
        return str(dst_path)

    try:
        # メタデータ（作成日時など）を保持したままコピー
        shutil.copy2(src, dst_path)
        print(f"コピー完了: {src.name} -> {dst_dir}")
        return str(dst_path)
    except Exception as e:
        print(f"コピー失敗: {src.name}. エラー: {e}")
        return None