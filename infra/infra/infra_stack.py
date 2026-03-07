from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_cognito as cognito,
    CfnOutput,
    RemovalPolicy,
    # aws_sqs as sqs,
)
# alpha 系はこっちで書く
import aws_cdk.aws_apigatewayv2_alpha as apigwv2
import aws_cdk.aws_apigatewayv2_integrations_alpha as integrations

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
            bucket_name=f"photolog-prod-s3-thumbnail-yasu",
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"], # 開発中は "*" でOK。本番はURLを指定
                    allowed_headers=["*"],
                )
            ],
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

        # API用Lambda関数
        api_handler = _lambda.Function(
            self, "ApiGetPhotosHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            function_name="photolog-prod-lambda-apiGetPhotos-yasu",
            code=_lambda.Code.from_asset("../lambda"), 
            handler="get_photos_api.handler",
            description="写真を取得するAPI",
            environment={
                "TABLE_NAME": table.table_name, # テーブル名を環境変数で渡す
                "THUMBNAIL_BUCKET_NAME": bucket_yasu.bucket_name # サムネイルバケット名を環境変数で渡す
            },
        )
        table.grant_read_data(api_handler) # LambdaにDynamoDB読み込み権限を付与
        bucket_yasu.grant_read(api_handler) # LambdaにS3読み取り権限を付与

        # API Gateway
        http_api = apigwv2.HttpApi(
            self, "ApiGateway",
            api_name="photolog-prod-apigateway-apigateway-yasu",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"], # 開発時は全て許可。ブラウザからのアクセスを拒否されないため。
                allow_methods=[apigwv2.CorsHttpMethod.GET],
            )
        )
        # 作成済みの api_handler を APIに紐づける
        http_api.add_routes(
            path="/photos",
            methods=[apigwv2.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration(
                "GetPhotosIntegration",
                api_handler
            )
        )

        # Cognito
        # 1. User Pool の作成
        user_pool = cognito.UserPool(self, "PhotologUserPool",
            user_pool_name="photolog-prod-userPool-auth-yasu",
            self_sign_up_enabled=False,  # 勝手に登録させない
            sign_in_aliases=cognito.SignInAliases(
                username=True  # ユーザー名でログイン
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
                #temp_password_validity=Duration.days(7)
            ),
            # ユーザーがパスワードを忘れた時のリカバリー方法
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # スタック削除時にUserPoolも削除するかどうか (本番運用なら DESTROY 以外も検討)
            removal_policy=RemovalPolicy.DESTROY 
        )

        # 2. Client の作成 (React App用)
        user_pool_client = user_pool.add_client("PhotologAppClient",
            user_pool_client_name="photolog-prod-userPoolClient-reactApp-yasu",
            auth_flows=cognito.AuthFlow(
                user_password=True,  # ID/PW認証を許可
                user_srp=True
            ),
            generate_secret=False  # フロントエンド用なのでシークレットは作らない
        )

        # 3. 後の設定で使うIDを出力
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "AppClientId", value=user_pool_client.user_pool_client_id)
