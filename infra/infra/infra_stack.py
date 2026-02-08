from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
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
        owner = os.getenv("OWNER_NAME_01", "default_user")
        bucket = s3.Bucket(self, "PhotologRawBucket",
            # バケット名を世界で一意にするため、自動生成に任せるか指定します
            # 指定する場合: bucket_name="my-unique-photolog-bucket-2024",
            versioned=True,  # 誤削除防止のためにバージョン管理を有効化
            removal_policy=RemovalPolicy.DESTROY, # 学習用なのでStack削除時にバケットも消す設定（本番はRETAIN推奨）
            auto_delete_objects=True, # バケット削除時に中身も自動削除する
            bucket_name=f"photolog-prod-s3-original-{owner}"
        )
