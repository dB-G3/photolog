# /workspaces/photolog/lambda_S3meta/handler.py
def lambda_handler(event, context):
    print("Event: ", event)
    return {
        'statusCode': 200,
        'body': 'Hello from S3 Event Lambda!'
    }