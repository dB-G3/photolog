import os
from PIL import Image
from pillow_heif import register_heif_opener
from pathlib import Path
from PIL.ExifTags import TAGS
from PIL import ImageOps
import datetime
import hashlib

#動画用
import cv2
import subprocess

TARGET_WIDTH = 800
TARGET_HEIGHT = 600
VIDEOHEIGHT = "600"
VIDEOQUALITY = "28"  # 画質設定（18〜28が一般的。数字が大きいほど高圧縮・低画質）
BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")
LOGFILE_NAME = "log.txt"

# HEICをPillowで開けるように登録
register_heif_opener()

# EXIF情報を抽出
def get_exif_data(img_file, relative_path):
    try:
        # 画像を開く
        with Image.open(img_file) as img:
            # Exif情報を取得
            if img_file.suffix.lower() in [".jpg", ".jpeg"]:
                exif_raw = img._getexif()
            elif  img_file.suffix.lower() in [".heic"]:
                exif_raw = img.getexif()
            
            if not exif_raw:
                print("Exif情報なし")
                return None

            exif_data = {}
            for tag_id, value in exif_raw.items():
                # タグID（例: 306）を人間が読めるタグ名（例: DateTimeOriginal）に変換
                tag_name = TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value

            return exif_data
        
    except Exception as e:
        print(f"  [EXIF抽出失敗] {relative_path}: {e}")
        with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
            print(relative_path + "EXIF抽出失敗", file=o)
        return None

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
        with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
            print(relative_path + "リサイズ失敗", file=o)
        return None

# 画像ファイルのハッシュ値(SHA-256)を計算    
def calculate_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # ファイルを4096バイトずつ読み込んでハッシュを更新（メモリ節約）
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_video_thumbnail(video_file, save_path, second=1.0):
    # 動画ファイルを開く
    cap = cv2.VideoCapture(video_file)
    
    if not cap.isOpened():
        print(f"  [動画オープン失敗] {relative_path}")
        with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
            print(relative_path + "動画オープン失敗", file=o)
        return

    # 動画のFPS（フレームレート）を取得
    fps = cap.get(cv2.CAP_PROP_FPS)
    # 指定した秒数のフレーム位置を計算
    frame_id = int(fps * second)
    
    # 指定フレームまで移動
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    
    # フレームを読み込む
    ret, frame = cap.read()
    if ret:
        # 画像として保存（リサイズも可能）)
        cv2.imwrite(save_path, frame)
        print(f"サムネイルを保存しました: {save_path}")
    else:
        print(f"  [フレーム読み込み失敗] {relative_path}")
        with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
            print(relative_path + "フレーム読み込み失敗", file=o)
    
    cap.release()

def compress_video(input_path, output_path):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libx264',  # 汎用性の高いH.264ビデオコーデック
        '-crf', VIDEOQUALITY,
        '-preset', 'medium',   # 圧縮スピード（slowにすると時間はかかるがより綺麗に圧縮される）
        '-acodec', 'aac',      # 音声も標準的な形式に変換
        '-vf', "scale=-2:"+VIDEOHEIGHT, # 高さ720ピクセルにリサイズ（幅はアスペクト比を維持）
        output_path,
        '-y'
    ]
    subprocess.run(cmd)
    print(f"動画を圧縮しました: {output_path}")

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

            if img_file.suffix.lower() in [".jpg", ".jpeg", ".heic"]:
                #print(f"EXIF抽出開始: {relative_path}") 
                exif_data = get_exif_data(img_file, relative_path)
                
                #print(f"リサイズ開始: {relative_path}")
                img = process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path, relative_path)

                if exif_data.get('DateTimeOriginal'): #撮影日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTimeOriginal'), "%Y:%m:%d %H:%M:%S")
                    # ISO 8601形式の文字列に変換
                    iso_date = dt.isoformat()
                    log_data = log_data + iso_date +","
                elif exif_data.get('DateTime'): #修正日時
                    dt = datetime.datetime.strptime(exif_data.get('DateTime'), "%Y:%m:%d %H:%M:%S")
                    iso_date = dt.isoformat()
                    log_data = log_data + iso_date +","
                else:
                    log_data = log_data + "EXIF撮影日情報なし,"
                hash = calculate_hash(save_path)
                with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
                    log_data = log_data + hash + ","
                    print(log_data, file=o)
            elif img_file.suffix.lower() in [".mov"]:
                extract_video_thumbnail(img_file, save_path.with_suffix(".jpg"), 1.0)
                compress_video(img_file, save_path)
            
            else:
                print(relative_path)
