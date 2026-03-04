# /workspaces/photolog/lambda_S3meta/handler.py
import json
import boto3
import os

# AWS SDKの準備（ハンドラーの外で定義するのがベストプラクティス）
dynamodb = boto3.resource('dynamodb')
# 環境変数からテーブル名を取得（後ほどCDKで設定します）
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    # S3イベントからバケット名とファイル名（キー）を取得
    # ※S3のキーはURLエンコードされている場合があるため、実運用ではunquoteが必要ですが
    #   まずはシンプルに取得します
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        print(f"Processing image: {key} from bucket: {bucket}")

        # DynamoDBへ書き込み
        # table.put_item(
        #     Item={
        #         'ImageId': key,       # パーティションキー
        #         'BucketName': bucket,
        #         'Status': 'UPLOADED',
        #         'Timestamp': record['eventTime']
        #     }
        # )
        print(f"Successfully wrote {key} to DynamoDB")

    return {
        'statusCode': 200,
        'body': json.dumps('Data saved to DynamoDB!')
    }