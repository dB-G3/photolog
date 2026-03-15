import os
import json
import piexif
from datetime import datetime
from pathlib import Path
import time

def fix_exif_from_json(image_path):
    img_p = Path(image_path)
    json_path = img_p.with_suffix(img_p.suffix + ".json")
    
    if not json_path.exists():
        return False

    try:
        img_str = str(img_p)
        # 1. まず既存のEXIFを読み込む
        try:
            exif_dict = piexif.load(img_str)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # 2. すでに撮影日時が入っているかチェック
        # ExifIFD.DateTimeOriginal (タグ番号: 36867) を確認
        existing_date = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
        
        if existing_date:
            # すでにデータがある場合は、何もしない
            output_log(f"Skipping: {img_p.name} already has EXIF date: {existing_date.decode('utf-8')}")
            return False

        # 3. EXIFがない場合のみ、JSONからデータを取得して書き込み
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        timestamp = int(data['photoTakenTime']['timestamp'])
        dt_object = datetime.fromtimestamp(timestamp)
        exif_time_str = dt_object.strftime("%Y:%m:%d %H:%M:%S")

        # 各タグにセット（piexifはbytes型を期待するので注意）
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_time_str
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_time_str
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_time_str

        # バイナリに変換して画像に挿入
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, img_str)
        
        output_log(f"Fixed: {img_p.name} updated with JSON timestamp: {exif_time_str}")
        return True

    except Exception as e:
        output_log(f"Error processing {image_path}: {e}")
        return False

LOGFILE_NAME = 'override.log'    
def output_log(msg):
    print(msg)
    with open(LOGFILE_NAME,"a") as o:
        print(time.strftime("%Y-%m-%d %H:%M:%S:: ", time.localtime()) + str(msg), file=o)



BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "real-data/input")
#OUTPUT_DIR = os.path.join(BASE_DIR, "real-data/output/test")
    
def main():

    print(f"--- 探索開始: {INPUT_DIR} ---")
    
    input_path = Path(INPUT_DIR)
    # output_path = Path(OUTPUT_DIR)
    
    # rglobでサブフォルダ内も含めて対象ファイルを全検索
    for img_file in input_path.rglob("*"):
        log_data = ""
        if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic", ".gif", ".mov", ".mp4", ".avi", ".mpeg"]:
            fix_exif_from_json(img_file)

if __name__ == "__main__":
    main()