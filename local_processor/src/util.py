import os
import hashlib
import time

#ZIP用
import zipfile

ERROR_LOGFILE_NAME = "error.txt"
LOGFILE_NAME = "log.txt"

def output_error_log(output_dir, msg):
    print(msg)
    with open(output_dir + '/' + ERROR_LOGFILE_NAME,"a") as o:
        print(time.strftime("%Y-%m-%d %H:%M:%S:: ", time.localtime()) + str(msg), file=o)

def output_log(output_dir, msg):
    print(msg)
    with open(output_dir + '/' + LOGFILE_NAME,"a") as o:
        print(time.strftime("%Y-%m-%d %H:%M:%S:: ", time.localtime()) + str(msg), file=o)

# 一時保存用のサブフォルダを作成
def make_temp_dir(output_dir, subdir_name):
    target_dir_name = os.path.join(output_dir, subdir_name)
    if not os.path.exists(target_dir_name):
        os.makedirs(target_dir_name)

# ファイルのハッシュ値(SHA-256)を計算    
def calculate_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # ファイルを4096バイトずつ読み込んでハッシュを更新（メモリ節約）
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

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