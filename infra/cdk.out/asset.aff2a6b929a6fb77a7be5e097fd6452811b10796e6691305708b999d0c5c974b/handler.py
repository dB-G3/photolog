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
        # 暫定的な対応：
        # UserIDは固定、ShootingDateはイベント時刻から取得してみます
        user_id = "yasu" 
        shooting_date = record['eventTime'] # ISO 8601形式の文字列が入ります
        
        table.put_item(
            Item={
                'UserID': user_id,          # パーティションキー (必須)
                'ShootingDate': shooting_date, # ソートキー (必須)
                'S3Key': key,               # その他属性
                'BucketName': bucket,
                'Status': 'UPLOADED'
            }
        )
        print(f"Successfully wrote {key} to DynamoDB")

    return {
        'statusCode': 200,
        'body': json.dumps('Data saved to DynamoDB!')
    }