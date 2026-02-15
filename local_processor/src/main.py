import os
import datetime
import hashlib
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

from PIL.ExifTags import TAGS
from PIL import ImageOps

#動画用
import cv2
import subprocess
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import json

#ZIP用
import zipfile

TARGET_WIDTH = 800
TARGET_HEIGHT = 600
VIDEOHEIGHT = "600"
VIDEOQUALITY = "28"  # 画質設定（18〜28が一般的。数字が大きいほど高圧縮・低画質）
BASE_DIR = "../"
INPUT_DIR = os.path.join(BASE_DIR, "test-data/input")
OUTPUT_DIR = os.path.join(BASE_DIR, "test-data/output")
LOGFILE_NAME = "log.txt"
ERROR_LOGFILE_NAME = "error.txt"

# HEICをPillowで開けるように登録
register_heif_opener()

def output_error_log(output_dir, msg):
    print(msg)
    with open(output_dir + '/' + ERROR_LOGFILE_NAME,"a") as o:
        print(msg, file=o)

# 一時保存用のサブフォルダを作成
def make_temp_dir(output_dir, subdir_name):
    target_dir_name = os.path.join(output_dir, subdir_name)
    if not os.path.exists(target_dir_name):
        os.makedirs(target_dir_name)


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
                msg = "EXIF情報なし:" + str(relative_path)
                output_error_log(OUTPUT_DIR, msg)
                return None

            exif_data = {}
            for tag_id, value in exif_raw.items():
                # タグID（例: 306）を人間が読めるタグ名（例: DateTimeOriginal）に変換
                tag_name = TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value

            return exif_data
        
    except Exception as e:
        msg = "EXIF抽出失敗:" + str(relative_path) + " - " + str(e)
        output_error_log(OUTPUT_DIR, msg)
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
        msg = "リサイズ失敗" + str(relative_path) + " - " + str(e)
        output_error_log(OUTPUT_DIR, msg)
        return None
    
# 動画データからメタデータ(撮影日)を抽出
def get_video_metadata(file_path):
    parser = createParser(str(file_path))
    if not parser:
        return None

    return_data = {}
    with parser:
        # 辞書形式で主要なデータを取得
        metadata = extractMetadata(parser).exportDictionary()
        if metadata:
            if metadata['Metadata']:
                return_data['Creation date'] = metadata['Metadata']['Creation date']
            elif metadata['Metadata']['Last modification']:
                return_data['Last modification'] = metadata['Metadata']['Last modification']
            else:
                print("動画の撮影日時情報なし:" + str(file_path))
    return return_data

# ファイルのハッシュ値(SHA-256)を計算    
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
        msg = "[動画オープン失敗]" + str(relative_path)
        output_error_log(OUTPUT_DIR, msg)
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
        msg = "フレーム読み込み失敗:" + str(relative_path)
        output_error_log(OUTPUT_DIR, msg)
    
    cap.release()

def compress_video(input_path, output_path):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libx264',  # H.264
        '-crf', VIDEOQUALITY,
        '-preset', 'medium',   # 圧縮スピード
        '-acodec', 'aac',      # AAC
        '-vf', "scale=-2:"+VIDEOHEIGHT, # 高さ720ピクセルにリサイズ（幅はアスペクト比を維持）
        output_path,
        '-y'
    ]
    subprocess.run(cmd)
    print(f"動画を圧縮しました: {output_path}")

def get_file_path(file_path):
    """
    ファイルパスから指定以下のファイルの一覧を取得する
    :param file_path:ファイルパス
    :return: generator
    """
    if os.path.isfile(file_path):
        yield file_path
    else:
        for (base_dir, _ , file_name_list) in os.walk(file_path):
            for file_name in file_name_list:
                path = os.path.join(base_dir, file_name)
                path = path.replace(os.sep, '/')
                yield path

def zipping(file_path, save_dir=""):
    """
    ファイル及びフォルダごとZIP化関数
    :param file_path: 圧縮対象のファイルおよびディレクトリ
    :param save_dir: 保存先（デフォルトは圧縮対象と同じ階層）
    :return:
    """
    if file_path[-1]==os.sep or file_path[-1]=="/" :
        file_path = file_path[:-1]

    if not os.path.isdir(file_path) and not os.path.isfile(file_path):
        print("Not Found : {}".format(file_path))
        raise FileNotFoundError

    if os.path.isdir(save_dir):
        save_dir = os.path.join(save_dir, os.path.basename(file_path))
    else:
        save_dir = file_path

    zip_file_name = "{}.zip".format(save_dir)

    print('zip file : {}'.format(zip_file_name))
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as z:
        if os.path.isfile(file_path):
            print(">>zipping....   {}".format(file_path))
            file_name = os.path.basename(file_path)
            z.write(file_path, file_name)
        else:
            for file_name in get_file_path(file_path):
                head, tail = file_name.split(os.path.join(file_path,'').replace(os.sep,'/'))
                print(">>zipping....   {}".format(file_name))
                z.write(file_name, tail)

    return zip_file_name

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

            if img_file.suffix.lower() in [".jpg", ".jpeg", ".heic"]:
                #print(f"EXIF抽出開始: {relative_path}") 
                exif_data = get_exif_data(img_file, relative_path)
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
                
                #print(f"リサイズ開始: {relative_path}")
                img = process_image(img_file, TARGET_WIDTH, TARGET_HEIGHT, save_path, relative_path)

            elif img_file.suffix.lower() in [".mov"]:
                meta = get_video_metadata(img_file)
                if(meta['Creation date']):
                    dt = datetime.datetime.strptime(meta['Creation date'], "%Y-%m-%d %H:%M:%S")
                    iso_date = dt.isoformat()
                    log_data = log_data + iso_date +","
                elif(meta['Last modification']):
                    dt = datetime.datetime.strptime(meta['Last modification'], "%Y-%m-%d %H:%M:%S")
                    iso_date = dt.isoformat()
                    log_data = log_data + iso_date +","
                else:
                    log_data = log_data + "動画の撮影日情報なし,"
                extract_video_thumbnail(img_file, save_path.with_suffix(".jpg"), 1.0)
                compress_video(img_file, save_path)
            
            else:
                print(relative_path)
            with open(OUTPUT_DIR + '/' + LOGFILE_NAME,"a") as o:
                print(log_data, file=o)
