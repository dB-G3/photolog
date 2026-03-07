# /workspaces/photolog/lambda/get_photos_api.py
import json
import os
import boto3
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# 環境変数からテーブル名を取得
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name)
BUCKET_NAME = os.environ.get('THUMBNAIL_BUCKET_NAME')

def handler(event, context):
    # API Gateway (HTTP API) からのクエリパラメータ取得
    query_params = event.get('queryStringParameters', {})
    user_id = query_params.get('userId', 'User_01') # テスト用にデフォルト設定
    year_month = query_params.get('yearMonth', '') # 例: "2024-05"

    try:
        # 1. DynamoDBからクエリ
        # UserIDが一致し、ShootingDateが指定の文字列で始まるものを検索
        if year_month:
            response = table.query(
                KeyConditionExpression=Key('UserID').eq(user_id) & 
                                       Key('ShootingDate').begins_with(year_month)
            )
        else:
            response = table.query(
                KeyConditionExpression=Key('UserID').eq(user_id)
            )

        items = response.get('Items', [])

        # 2. S3の署名付きURLを各アイテムに付与
        for item in items:
            # S3のパス（YYYY-MM-DD/filename.jpg）からURL生成
            s3_key = item.get('S3Key')
            if s3_key:
                # 動画ファイルの場合はサムネイルと動画両方のURLを生成
                if s3_key.endswith('.mov') or s3_key.endswith('.mp4'):
                    item['isVideo'] = True
                    presigned_url_movieThumbnail = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': BUCKET_NAME, 'Key': s3_key + '.jpg'},
                        ExpiresIn=3600 # 1時間有効
                    )
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                        ExpiresIn=3600 # 1時間有効
                    )
                    item['displayUrl'] = presigned_url_movieThumbnail
                    item['displayUrlMovie'] = presigned_url
                else:
                    item['isVideo'] = False
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                        ExpiresIn=3600 # 1時間有効
                    )
                    item['displayUrl'] = presigned_url

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # CORS対応
            },
            'body': json.dumps(items)
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal Server Error'})
        }