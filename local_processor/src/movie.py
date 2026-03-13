#動画用
import cv2
import subprocess
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

import util
import os

VIDEOHEIGHT = "600"
VIDEOQUALITY = "28"  # 画質設定（18〜28が一般的。数字が大きいほど高圧縮・低画質）

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

def extract_video_thumbnail(video_file, save_path, relative_path,  output_dir, second=1.0):
    # 動画ファイルを開く
    cap = cv2.VideoCapture(video_file)
    
    if not cap.isOpened():
        msg = "[動画オープン失敗]" + str(relative_path)
        util.output_error_log(output_dir, msg)
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
        util.output_error_log(output_dir, msg)
    
    cap.release()

def compress_video(input_path, output_path):
    # 出力ファイルが既に存在するかチェック
    if os.path.exists(output_path):
        print(f"スキップ: 既に圧縮済みファイルが存在します: {output_path}")
        return
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libx264',  # H.264
        '-crf', VIDEOQUALITY,
        '-preset', 'medium',   # 圧縮スピード
        '-acodec', 'aac',      # AAC
        '-loglevel', 'quiet',
        '-vf', "scale=-2:"+VIDEOHEIGHT, # 高さ720ピクセルにリサイズ（幅はアスペクト比を維持）
        output_path,
        '-y'
    ]
    subprocess.run(cmd)
    print(f"動画を圧縮しました: {output_path}")

def convert_to_mp4(input_path, output_path):
    """
    MOVなどの動画をChromeで再生可能なH.264/MP4形式に変換する
    """
    # 出力ファイルが既に存在するかチェック
    if os.path.exists(output_path):
        print(f"スキップ: 既に圧縮済みファイルが存在します: {output_path}")
        return output_path
    print(f"変換中: {input_path} -> {output_path}")
    
    # ffmpegコマンドを構築
    command = [
        'ffmpeg',
        '-i', str(input_path),        # 入力
        '-vcodec', 'libx264',         # 映像: H.264 (超広範な互換性)
        '-pix_fmt', 'yuv420p',        # iPhone動画再生に必須の設定
        '-acodec', 'aac',             # 音声: AAC
        '-b:v', '1M',                 # ビットレート(任意) 
        '-y',                         # 上書き許可
        str(output_path)              # 出力
    ]
    
    try:
        # コマンド実行（標準エラーをキャプチャ）
        subprocess.run(command, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"FFmpegエラー: {e.stderr.decode()}")
        raise e