import boto3
from botocore.exceptions import NoCredentialsError
import urllib

def upload_thumbnail_with_metadata(file_path, bucket_name, object_name, user_id, shooting_date):
    """
    サムネイルをS3にアップロードし、メタデータに撮影日を込める
    :param file_path: ローカルのファイルパス
    :param bucket_name: S3バケット名
    :param object_name: S3での保存名 (例: thumbnails/user_01/photo.jpg)
    :param user_id: User_NN 形式のID
    :param shooting_date: YYYY-MM-DDTHH:mm:ss#FileName 形式の文字列
    """
    s3_client = boto3.client('s3')

    try:
        # メタデータを定義 (x-amz-meta- は自動付与される)
        metadata = {
            'userid': user_id,
            'shootingdate': shooting_date
        }

        tags = {
                'Owner': 'yasu',
                'Enviroment': 'dev',
                'Project': 'photolog'
            }
        # タグをURLエンコード文字列に変換
        tag_string = urllib.parse.urlencode(tags)

        # アップロード実行
        s3_client.upload_file(
            file_path, 
            bucket_name, 
            object_name,
            ExtraArgs={
                'Metadata': metadata,
                'Tagging': tag_string,
                'ContentType': 'image/jpeg' # 形式に合わせて変更
            }
        )
        print(f"Upload Successful: {object_name}")
        
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")