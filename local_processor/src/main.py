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
ENV = "dev"

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
    
    # rglobでサブフォルダ内も含めて対象ファイルを全検索
    for img_file in input_path.rglob("*"):
        log_data = ""
        if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic", ".gif", ".mov", ".mp4", ".avi", ".mpeg"]:
            # 入力フォルダからの相対パスを取得 (例: 2024/01/pic.jpg)
            relative_path = img_file.relative_to(input_path)
            log_data = log_data + str(relative_path) + ","

            iso_date = "撮影日時取得不可"
            if img_file.suffix.lower() in [".jpg", ".jpeg", ".heic"]:
                exif_data = picture.get_exif_data(img_file, relative_path, OUTPUT_DIR)
                if exif_data.get('DateTimeOriginal'): #撮影日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTimeOriginal'), "%Y:%m:%d %H:%M:%S")
                elif exif_data.get('DateTime'): #修正日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTime'), "%Y:%m:%d %H:%M:%S")
                else:
                    # 撮影日時が取得できない場合はUNIXエポック日時の開始日時をセット
                    dt = datetime.datetime(1970, 1, 1, 0, 0, 0)
                # ISO 8601形式の文字列に変換
                iso_date = dt.isoformat()

                # 保存先のフルパスを決定
                # datetimeオブジェクトに変換
                try:
                    dt = datetime.datetime.fromisoformat(iso_date)
                    # 日付だけの文字列にする (2025-10-20)
                    dir_name = dt.date().isoformat() 
                except Exception as e:
                    print(e)
                    dir_name = "1970-01-01"
                # 保存先フォルダなければ作成
                temp_dir = Path(OUTPUT_DIR) / dir_name
                temp_dir.mkdir(parents=True, exist_ok=True)
                save_path_pict = temp_dir / relative_path.name
                # オリジナルデータを日付フォルダにコピー
                temp_dir2 = Path(OUTPUT_DIR_ORIGINAL) / dir_name
                temp_dir2.mkdir(parents=True, exist_ok=True)
                save_path_pict_original = temp_dir2 / relative_path.name
                util.copy_original_image(img_file, save_path_pict_original.parent)
                
                #ファイルの圧縮
                ret = picture.process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path_pict, relative_path, OUTPUT_DIR)

                #S3にアップロード
                upload.upload_thumbnail_with_metadata(
                    #file_path=save_path_pict,
                    file_path=ret[1],
                    bucket_name='photolog-prod-s3-thumbnail-' + user_id,
                    object_name=str(save_path_pict.relative_to(output_path)),
                    user_id=user_id,
                    shooting_date=iso_date,
                    )

            elif img_file.suffix.lower() in [".mov"]:
                meta = movie.get_video_metadata(img_file)
                if(meta['Creation date']):  #撮影日時
                    dt = datetime.datetime.strptime(meta['Creation date'], "%Y-%m-%d %H:%M:%S")
                elif(meta['Last modification']):    #修正日時
                    dt = datetime.datetime.strptime(meta['Last modification'], "%Y-%m-%d %H:%M:%S")
                # ISO 8601形式の文字列に変換
                iso_date = dt.isoformat()

                # 保存先のフルパスを決定
                try:
                    dt = datetime.datetime.fromisoformat(iso_date)
                    # 日付だけの文字列にする (2025-10-20)
                    dir_name = dt.date().isoformat() 
                except Exception as e:
                    print(e)
                    dir_name = "1970-01-01"
                # 保存先フォルダなければ作成
                temp_dir = Path(OUTPUT_DIR) / dir_name
                temp_dir.mkdir(parents=True, exist_ok=True)
                save_path_video = temp_dir / relative_path.name
                save_path_video_thumbnail = temp_dir / relative_path.name
                # オリジナルデータを日付フォルダにコピー
                temp_dir2 = Path(OUTPUT_DIR_ORIGINAL) / dir_name
                temp_dir2.mkdir(parents=True, exist_ok=True)
                save_path_video_original = temp_dir2 / relative_path.name
                util.copy_original_image(img_file, save_path_video_original.parent)

                print(f"動画処理開始: {relative_path}")
                #print(save_path_video)
                if img_file.suffix.lower() in [".mov"]:
                    save_path_video = temp_dir / relative_path.with_suffix(".mp4").name
                    save_path_video_thumbnail = temp_dir / relative_path.with_suffix(".mp4").name
                    img_file = movie.convert_to_mp4(img_file, save_path_video)
                else:
                    movie.compress_video(img_file, save_path_video)
                movie.extract_video_thumbnail(img_file, save_path_video_thumbnail.with_suffix(".jpg"), relative_path, save_path_video, 0.1)

                #S3にアップロード
                upload.upload_thumbnail_with_metadata(
                    file_path=save_path_video_thumbnail.with_suffix(".jpg"),
                    bucket_name='photolog-prod-s3-thumbnail-' + user_id,
                    object_name=str(save_path_video_thumbnail.relative_to(output_path))+'.jpg',
                    user_id=user_id,
                    shooting_date=iso_date + '#' + str(save_path_video_thumbnail.name),
                    )
                upload.upload_thumbnail_with_metadata(
                    file_path=save_path_video,
                    bucket_name='photolog-prod-s3-thumbnail-' + user_id,
                    object_name=str(save_path_video.relative_to(output_path)),
                    user_id=user_id,
                    shooting_date=iso_date + '#' + str(save_path_video.name),
                    )
            
            else:
                print("処理スキップ：" + str(relative_path))
            log_data = log_data + iso_date
            util.output_log(OUTPUT_DIR, log_data)
            num_processed_files = num_processed_files + 1
            print(f"Processed...{num_processed_files}")
        else:
            util.output_log(OUTPUT_DIR, "処理スキップ：" + str(img_file.relative_to(input_path)))

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
