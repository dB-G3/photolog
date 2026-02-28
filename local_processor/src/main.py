import util

import os
import datetime
from pathlib import Path

import picture
import movie
import upload


TARGET_WIDTH = 800
TARGET_HEIGHT = 600
BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")
OUTPUT_ZIP_DIR = os.path.join(BASE_DIR, "test-data/output/zip")


if __name__ == "__main__":
    print(f"--- 探索開始: {INPUT_DIR} ---")
    
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
                
                #ファイルの圧縮
                img = picture.process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path_pict, relative_path, OUTPUT_DIR)

                #S3にアップロード
                upload.upload_thumbnail_with_metadata(
                    file_path=save_path_pict,
                    bucket_name='photolog-prod-s3-thumbnail-yasu',
                    object_name=str(save_path_pict.relative_to(output_path)),
                    user_id='yasu',
                    shooting_date=iso_date + '#' + str(save_path_pict.name),
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
                
                print(f"動画処理開始: {relative_path}")
                #print(save_path_video)
                movie.extract_video_thumbnail(img_file, save_path_video_thumbnail.with_suffix(".jpg"), relative_path, 1.0)
                movie.compress_video(img_file, save_path_video)

                #S3にアップロード
                upload.upload_thumbnail_with_metadata(
                    file_path=save_path_video_thumbnail.with_suffix(".jpg"),
                    bucket_name='photolog-prod-s3-thumbnail-yasu',
                    object_name=str(save_path_video_thumbnail.relative_to(output_path))+'.jpg',
                    user_id='yasu',
                    shooting_date=iso_date + '#' + str(save_path_video_thumbnail.name),
                    )
                upload.upload_thumbnail_with_metadata(
                    file_path=save_path_video,
                    bucket_name='photolog-prod-s3-thumbnail-yasu',
                    object_name=str(save_path_video.relative_to(output_path)),
                    user_id='yasu',
                    shooting_date=iso_date + '#' + str(save_path_video.name),
                    )
            
            else:
                print("処理スキップ：" + str(relative_path))
            log_data = log_data + iso_date
            util.output_log(OUTPUT_DIR, log_data)
        else:
            util.output_log(OUTPUT_DIR, "処理スキップ：" + str(img_file.relative_to(input_path)))

    print('Zip圧縮開始')
    tmp_path = Path(OUTPUT_DIR)
    # tmp直下にあるフォルダだけを対象にする
    zip_dir = Path(OUTPUT_ZIP_DIR) / dir_name
    zip_dir.mkdir(parents=True, exist_ok=True)
    for date_dir in tmp_path.iterdir():
        print(date_dir.name)
        if(date_dir.name == os.path.basename(OUTPUT_ZIP_DIR)):
            continue
        if date_dir.is_dir():
            # フォルダをZipに圧縮
            zip_path = os.path.join(OUTPUT_ZIP_DIR, date_dir.name)
            zip_file = util.zip_directory(zip_path, date_dir)
    print('Zip圧縮完了')
