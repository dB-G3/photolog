# /workspaces/photolog/lambda_S3meta/handler.py
import json
import boto3
import os

# AWS SDKの準備（ハンドラーの外で定義するのがベストプラクティス）
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
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

        # 1. S3からオブジェクトのメタデータを取得する
        try:
            response = s3_client.head_object(Bucket=bucket, Key=key)
            # ユーザー定義メタデータは 'Metadata' キーの中に小文字で格納される
            metadata = response.get('Metadata', {})
            
            # x-amz-meta-shootingdate -> metadata['shootingdate']
            # x-amz-meta-userid       -> metadata['userid']
            shooting_date = metadata.get('shootingdate')
            user_id = metadata.get('userid')

            if not shooting_date or not user_id:
                print(f"Error: Metadata missing for {key}. UserID: {user_id}, Date: {shooting_date}")
                continue

            # 2. DynamoDBへ書き込み
            table.put_item(
                Item={
                    'UserID': user_id,          # パーティションキー
                    'ShootingDate': shooting_date, # ソートキー
                    'S3Key': key,
                    'BucketName': bucket,
                    'Status': 'UPLOADED'
                }
            )
            print(f"Successfully registered {key} for User: {user_id}")

        except Exception as e:
            print(f"Error getting metadata for {key}: {str(e)}")
            raise e
        print(f"Successfully wrote {key} to DynamoDB")

    return {
        'statusCode': 200,
        'body': json.dumps('Data saved to DynamoDB!')
    }