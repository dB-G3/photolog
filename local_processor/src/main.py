import os
from PIL import Image
from pathlib import Path
from PIL.ExifTags import TAGS
from PIL import ImageOps
import datetime
import hashlib

TARGET_WIDTH = 800
TARGET_HEIGHT = 600
BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")
LOGFILE_NAME = "log.txt"

# EXIF情報を抽出
def get_exif_data(img_file):
    # 画像を開く
    with Image.open(img_file) as img:
        # Exif情報を取得
        exif_raw = img._getexif()
        
        if not exif_raw:
            print("Exif情報なし")
            return None

        exif_data = {}
        for tag_id, value in exif_raw.items():
            # タグID（例: 306）を人間が読めるタグ名（例: DateTimeOriginal）に変換
            tag_name = TAGS.get(tag_id, tag_id)
            exif_data[tag_name] = value
            
        return exif_data

# 画像を圧縮
def process_image(img_file, target_width, target_height, save_path, relative_path):

    try:
        with Image.open(img_file) as img:
            img = ImageOps.exif_transpose(img) # Exifの回転情報を反映
            img.thumbnail((target_width, target_height))
            img.save(save_path)
            #print(f"  [リサイズ完了] {save_path.name}")
            return img
    except Exception as e:
        print(f"  [リサイズ失敗] {relative_path}: {e}")
        return None

# 画像ファイルのハッシュ値(SHA-256)を計算    
def calculate_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # ファイルを4096バイトずつ読み込んでハッシュを更新（メモリ節約）
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    print(f"--- 探索開始: {INPUT_DIR} ---")
    
    input_path = Path(INPUT_DIR)
    
    # rglobでサブフォルダ内も含めてJPGを全検索
    for img_file in input_path.rglob("*"):
        log_data = ""
        if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic", ".gif", ".mov", ".mp4", ".avi", ".mpeg"]:
            # 入力フォルダからの相対パスを取得 (例: 2024/01/pic.jpg)
            relative_path = img_file.relative_to(input_path)
            log_data = log_data + str(relative_path) + ","
            #print(relative_path)
    
            # 保存先のフルパスを決定
            save_path = Path(OUTPUT_DIR) / relative_path
    
            # 保存先のフォルダがなければ作成 (mkdir -p 相当)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            if img_file.suffix.lower() in [".jpg", ".jpeg"]:
                #print(f"EXIF抽出開始: {relative_path}") 
                exif_data = get_exif_data(img_file)
                
                #print(f"リサイズ開始: {relative_path}")
                img = process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path, relative_path)

                if(exif_data.get('DateTimeOriginal')):
                    #log_data = log_data + f"撮影日: {exif_data.get('DateTimeOriginal')},"
                    dt = datetime.datetime.strptime(exif_data.get('DateTimeOriginal'), "%Y:%m:%d %H:%M:%S")
                    #year   = dt.year
                    #month  = dt.month
                    # ISO 8601形式の文字列に変換
                    iso_date = dt.isoformat()
                    log_data = log_data + iso_date +","
                else:
                    log_data = log_data + "EXIF撮影日情報なし,"
                hash = calculate_hash(save_path)
                with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
                    log_data = log_data + hash + ","
                    print(log_data, file=o)
            else:
                print(relative_path)
