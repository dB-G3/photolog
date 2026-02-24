import os
import hashlib
import time

#ZIP用
import shutil

ERROR_LOGFILE_NAME = "error.txt"
LOGFILE_NAME = "log.txt"

def output_error_log(output_dir, msg):
    print(msg)
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

from pathlib import Path
def zip_directory(output_path, target_dir):
    # 圧縮後のファイル名（拡張子 .zip は自動で付与される）
    # 例: /app/tmp/2025-10-20.zip
    #output_path = target_dir

    # 圧縮実行 (引数: 保存ファイル名, フォーマット, 圧縮したいディレクトリ)
    shutil.make_archive(output_path, 'zip', root_dir=target_dir)
    
    print(f"Zip作成完了: {output_path}.zip")
    return Path(f"{output_path}.zip")