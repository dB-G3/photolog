from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    RemovalPolicy,
    # aws_sqs as sqs,
)
from constructs import Construct
import os

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "InfraQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # 写真を保存するS3バケットの定義
        bucket_yasu = s3.Bucket(self, "PhotologRawBucket-yasu-v2",
            versioned=True,  # 誤削除防止のためにバージョン管理を有効化
            removal_policy=RemovalPolicy.DESTROY, # 学習用なのでStack削除時にバケットも消す設定（本番はRETAIN推奨）
            auto_delete_objects=True, # バケット削除時に中身も自動削除する
            bucket_name=f"photolog-prod-s3-thumbnail-yasu"
        )

        bucket_megu = s3.Bucket(self, "PhotologRawBucket-megu-v2",
            versioned=True,  # 誤削除防止のためにバージョン管理を有効化
            removal_policy=RemovalPolicy.DESTROY, # 学習用なのでStack削除時にバケットも消す設定（本番はRETAIN推奨）
            auto_delete_objects=True, # バケット削除時に中身も自動削除する
            bucket_name=f"photolog-prod-s3-thumbnail-megu"
        )

        # DynamoDBの定義
        table = dynamodb.Table(
            self, "PhotologMetadataTable",
            table_name=f"photolog-prod-dynamodb-metadata-yasu",
            # パーティションキー: ユーザーを一意に識別するID (例: megu)
            partition_key=dynamodb.Attribute(
                name="UserID", 
                type=dynamodb.AttributeType.STRING
            ),
            # ソートキー: 撮影日（日付で検索・ソートしやすくするため）
            sort_key=dynamodb.Attribute(
                name="ShootingDate", 
                type=dynamodb.AttributeType.STRING
            ),
            # 開発用設定
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, # 使った分だけ課金
            removal_policy=RemovalPolicy.DESTROY             # Stack削除時にテーブルも消す
        )

        # Lambda関数の定義
        meta_lambda = _lambda.Function(
            self, "S3MetaHandler",
            function_name="photolog-prod-lambda-s3metaRegister-yasu",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="S3handler.lambda_handler",
            code=_lambda.Code.from_asset("../lambda"),
            description="S3に画像がアップロードされた際にメタデータをDynamoDBに登録するLambda",
            environment={
                "TABLE_NAME": table.table_name # テーブル名を環境変数で渡す
            },
        )
        table.grant_write_data(meta_lambda) # LambdaにDynamoDB書き込み権限を付与
        bucket_yasu.grant_read(meta_lambda) # LambdaにS3読み取り権限を付与

        # S3イベント通知を設定
        bucket_yasu.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(meta_lambda)
        )
