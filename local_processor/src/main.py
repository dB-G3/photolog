import util

import os
import datetime
from pathlib import Path

import picture
import movie


TARGET_WIDTH = 800
TARGET_HEIGHT = 600
BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")


if __name__ == "__main__":
    print(f"--- 探索開始: {INPUT_DIR} ---")
    
    input_path = Path(INPUT_DIR)
    
    # rglobでサブフォルダ内も含めて対象ファイルを全検索
    for img_file in input_path.rglob("*"):
        log_data = ""
        if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic", ".gif", ".mov", ".mp4", ".avi", ".mpeg"]:
            # 入力フォルダからの相対パスを取得 (例: 2024/01/pic.jpg)
            relative_path = img_file.relative_to(input_path)
            log_data = log_data + str(relative_path) + ","
    
            # 保存先のフルパスを決定
            save_path = Path(OUTPUT_DIR) / relative_path
    
            # 保存先のフォルダがなければ作成 (mkdir -p 相当)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            iso_date = "撮影日時取得不可"
            if img_file.suffix.lower() in [".jpg", ".jpeg", ".heic"]:
                exif_data = picture.get_exif_data(img_file, relative_path, OUTPUT_DIR)
                if exif_data.get('DateTimeOriginal'): #撮影日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTimeOriginal'), "%Y:%m:%d %H:%M:%S")
                elif exif_data.get('DateTime'): #修正日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTime'), "%Y:%m:%d %H:%M:%S")
                # ISO 8601形式の文字列に変換
                iso_date = dt.isoformat()
                
                img = picture.process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path, relative_path, OUTPUT_DIR)

            elif img_file.suffix.lower() in [".mov"]:
                meta = movie.get_video_metadata(img_file)
                if(meta['Creation date']):  #撮影日時
                    dt = datetime.datetime.strptime(meta['Creation date'], "%Y-%m-%d %H:%M:%S")
                    iso_date = dt.isoformat()
                elif(meta['Last modification']):    #修正日時
                    dt = datetime.datetime.strptime(meta['Last modification'], "%Y-%m-%d %H:%M:%S")
                    iso_date = dt.isoformat()
                # ISO 8601形式の文字列に変換
                iso_date = dt.isoformat()
                
                print(f"動画処理開始: {relative_path}")
                movie.extract_video_thumbnail(img_file, save_path.with_suffix(".jpg"), relative_path, 1.0)
                movie.compress_video(img_file, save_path)
            
            else:
                print("処理スキップ：" + str(relative_path))
            log_data = log_data + iso_date
            util.output_log(OUTPUT_DIR, log_data)
        else:
            util.output_log(OUTPUT_DIR, "処理スキップ：" + str(img_file.relative_to(input_path)))
