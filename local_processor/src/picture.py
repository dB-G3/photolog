from PIL import Image
from pillow_heif import register_heif_opener

from PIL.ExifTags import TAGS
from PIL import ImageOps

import util

# HEICをPillowで開けるように登録
register_heif_opener()


# EXIF情報を抽出
def get_exif_data(img_file, relative_path, output_dir):
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
                util.output_error_log(output_dir, msg)
                return None

            exif_data = {}
            for tag_id, value in exif_raw.items():
                # タグID（例: 306）を人間が読めるタグ名（例: DateTimeOriginal）に変換
                tag_name = TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value

            return exif_data
        
    except Exception as e:
        msg = "EXIF抽出失敗:" + str(relative_path) + " - " + str(e)
        util.output_error_log(output_dir, msg)
        return None

# 画像を圧縮
def process_image(img_file, target_width, target_height, save_path, relative_path, output_dir):

    try:
        with Image.open(img_file) as img:
            img = ImageOps.exif_transpose(img) # Exifの回転情報を反映
            img.thumbnail((target_width, target_height))
            img.save(save_path)
            return img
    except Exception as e:
        msg = "リサイズ失敗" + str(relative_path) + " - " + str(e)
        util.output_error_log(output_dir, msg)
        return None