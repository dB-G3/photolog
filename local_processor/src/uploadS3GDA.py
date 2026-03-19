import os
import boto3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import argparse
import sys
import hashlib
import base64
import util

from botocore.exceptions import ClientError

from botocore.config import Config

# .envから環境変数を読み込む（infra/.env またはプロジェクトルートの.env）
load_dotenv()

# 設定（環境変数が空の場合はデフォルト値を使用）
BUCKET_NAME_BASE = 'photolog-prod-s3-original-'
STORAGE_CLASS = 'DEEP_ARCHIVE'
ENV = "prod"

if ENV == "dev":
    ZIP_DIR = Path("../test-data/output/zip")  # ZIPファイルが格納されているディレクトリ
elif ENV == "prod":
    ZIP_DIR = Path("../real-data/output/zip")  # ZIPファイルが格納されているディレクトリ
else:
    print("環境変数 ENV は prod か dev を指定してください")
    sys.exit(1)

def calculate_md5(file_path):
    """ファイルのMD5ハッシュを計算する"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.digest()

def verify_and_upload(user_id):
    BUCKET_NAME = BUCKET_NAME_BASE + user_id

    # リトライ設定：標準的な指数バックオフを有効化
    config = Config(
    retries = {
        'max_attempts': 10, # 最大10回リトライ
        'mode': 'standard' # 指数バックオフ
    }
    )
    s3_client = boto3.client('s3', config=config)

    if not ZIP_DIR.exists():
        print(f"Error: ディレクトリが見つかりません -> {ZIP_DIR}")
        return

    zip_files = list(ZIP_DIR.glob("*.zip"))
    if not zip_files:
        print(f"ディレクトリ{ZIP_DIR}にZIPファイルが見つかりません")
        return

    print(f"アップロード開始　{len(zip_files)} files...")

    num_processed_files = 0
    for zip_path in zip_files:
        file_name = zip_path.name
        s3_key = file_name

        # 1. ローカルでハッシュ計算
        local_md5_bin = calculate_md5(zip_path)
        local_md5_b64 = base64.b64encode(local_md5_bin).decode('utf-8')
        local_md5_hex = hashlib.md5(open(zip_path, 'rb').read()).hexdigest()

        print(f"[{file_name}] Local MD5: {local_md5_hex}")

        # S3上の既存チェック
        try:
            response = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            s3_etag = response['ETag'].strip('"') # ETagはダブルクォートで囲まれている
            # 通常のアップロード(Multipartでない場合)は ETag = MD5
            if local_md5_hex == s3_etag:
                print(f"[{file_name}] S3のETagと一致しました。スキップ: S3に既に存在します: s3://{BUCKET_NAME}/{s3_key}")
                num_processed_files = num_processed_files + 1
                print(f"処理済み = {num_processed_files}")
                continue
            else:
                print(f"s3://{BUCKET_NAME}/{s3_key}：S3上に同一キーが存在しますがハッシュが一致しないため、別名保存します")
                s3_key = s3_key + '(1).zip'
        except ClientError as e:
            # 404 エラー (NotFound) であれば存在しないのでアップロードを続行
            if e.response['Error']['Code'] != '404':
                # 404以外（権限エラーなど）は再送すべきでないため例外を出す
                raise e

        try:
            # 2. アップロード (ContentMD5を指定することでS3側で整合性チェックが行われる)
            with open(zip_path, "rb") as f:
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_key,
                    Body=f,
                    StorageClass=STORAGE_CLASS,
                    ContentMD5=local_md5_b64, # これを指定するとS3が受信時にハッシュ検証してくれる
                    Metadata={
                        'Project': 'photolog',
                        'Owner': 'yasu',
                        'UploadDate': datetime.now().isoformat(),
                        'LocalMD5': local_md5_hex,  # 独自メタデータとしても保存,
                        'Environment': 'prod'
                    }
                )

            # 3. 再照合 (S3のETagを取得して比較)
            response = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
            s3_etag = response['ETag'].strip('"') # ETagはダブルクォートで囲まれている

            # 通常のアップロード(Multipartでない場合)は ETag = MD5
            if local_md5_hex == s3_etag:
                print(f"[{file_name}] 検証成功: S3のETagと一致しました。")
            else:
                msg = f"[{file_name}] 警告: ハッシュが一致しません！ (S3 ETag: {s3_etag})"
                print(msg)
                util.output_error_log(ZIP_DIR, msg)
            
        except Exception as e:
            msg = f"アップロードもしくは照合失敗: {str(e)}"
            print(f"[{file_name}] {msg}")
            util.output_error_log(ZIP_DIR, msg)

        num_processed_files = num_processed_files + 1
        print(f"処理済み = {num_processed_files}")

def main():
    parser = argparse.ArgumentParser(description='Photolog Local Processor')
    parser.add_argument('--user', type=str, required=True, help='実行するユーザー名 (yasu, megu など)')
    args = parser.parse_args()
    user_id = args.user

    verify_and_upload(user_id)

if __name__ == "__main__":
    start_time = datetime.now()
    print(f"Upload process started at: {start_time}")
    
    main()
    
    end_time = datetime.now()
    print(f"Finished at: {end_time} (Duration: {end_time - start_time})")