import util

import os
import datetime
from pathlib import Path

import picture
import movie
import upload

import argparse
import sys

import shutil


TARGET_WIDTH = 800
TARGET_HEIGHT = 600
BASE_DIR = "../"
ENV = "prod"

if ENV == "dev":
    INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")
    OUTPUT_DIR_ORIGINAL = os.path.join(BASE_DIR, "test-data/output/original")
    OUTPUT_ZIP_DIR = os.path.join(BASE_DIR, "test-data/output/zip")
elif ENV == "prod":
    INPUT_DIR = os.path.join(BASE_DIR, "real-data/input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "real-data/output")
    OUTPUT_DIR_ORIGINAL = os.path.join(BASE_DIR, "real-data/output/original")
    OUTPUT_ZIP_DIR = os.path.join(BASE_DIR, "real-data/output/zip")
else:
    print("環境変数 ENV は prod か dev を指定してください")
    sys.exit(1)
    
def main():
    parser = argparse.ArgumentParser(description='Photolog Local Processor')
    parser.add_argument('--user', type=str, required=True, help='実行するユーザー名 (yasu, megu など)')
    args = parser.parse_args()
    user_id = args.user
    num_processed_files = 0

    print(f"--- 探索開始: {user_id}:{INPUT_DIR} ---")
    
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    
    print('Zip圧縮開始')
    
    # 1. 圧縮したいフォルダたちが並んでいる親フォルダ
    original_root = Path(OUTPUT_DIR_ORIGINAL)
    
    # 2. 出来上がったZipを保存する専用のフォルダ（階層を分ける）
    # 例: ../test-data/output/zip_archives/
    zip_store_dir = Path(OUTPUT_ZIP_DIR)
    zip_store_dir.mkdir(parents=True, exist_ok=True)

    for date_dir in original_root.iterdir():
        # フォルダ以外、またはもしzipフォルダが紛れ込んでいてもスキップ
        if not date_dir.is_dir() or date_dir.name == "zip":
            continue
            
        print(f"圧縮処理中: {date_dir.name}")

        # 出力先の指定
        zip_output_path = zip_store_dir / date_dir.name
        
        # base_name: 作成するzipのパス
        # format: 'zip'
        # root_dir: 圧縮したいフォルダ（date_dir）
        shutil.make_archive(
            base_name=str(zip_output_path), 
            format='zip', 
            root_dir=str(date_dir)
        )

    print('Zip圧縮完了')

if __name__ == "__main__":
    main()
