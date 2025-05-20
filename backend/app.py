from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import os
import uuid
from boto3.dynamodb.types import Decimal
import botocore.exceptions

app = Flask(__name__)
CORS(app)

# Konfiguration
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localstack:4566")
TABLE_NAME = 'Products'

# DynamoDB Ressourcen & Client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=DYNAMODB_ENDPOINT
)

clientDynamodb = boto3.client(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=DYNAMODB_ENDPOINT
)

# S3 config
S3_BUCKET = "my-s3-bucket"
IMAGES_PATH = "/app/images"  # Mounted path in container

s3 = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="mock_access_key",
    aws_secret_access_key="mock_secret_key",
    region_name="eu-central-1"
)

# SNS config
sns = boto3.client(
    "sns",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url="http://localstack:4566",
)


def create_sns_topic():
    response = sns.create_topic(Name="my-local-topic")
    topic_arn = response['TopicArn']
    print(f"Topic erstellt: {topic_arn}")
    return topic_arn

def subscribe_to_topic(topic_arn):
    response = sns.subscribe(
        TopicArn=topic_arn,
        Protocol="http",
        Endpoint="http://backend-app:5000/notifications"  # wichtig bei Docker!
    )
    print("Subscription ARN:", response['SubscriptionArn'])

# Prüfen + Erstellen der Tabelle
def create_table_if_not_exists():
    try:
        clientDynamodb.describe_table(TableName=TABLE_NAME)
        print(f"Tabelle '{TABLE_NAME}' existiert bereits.")
    except clientDynamodb.exceptions.ResourceNotFoundException:
        print(f"Tabelle '{TABLE_NAME}' wird erstellt...")
        clientDynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        waiter = clientDynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"Tabelle '{TABLE_NAME}' wurde erfolgreich erstellt.")

table_name = 'Products'

# Funktion zum Hinzufügen von Daten
def insert_initial_data():
    table = dynamodb.Table(table_name)
    
    # die initialen Produkte
    products = [
        {"id": "1", "name": "T-Shirt", "price": Decimal('19.99'), "description": "T-Shirt von de Marke C&A", "image": "http://localhost:4566/my-s3-bucket/tshirt.png" },
        {"id": "2", "name": "Jeans", "price": Decimal('39.99'), "description": "Jeans von der Marke H&M", "image": "http://localhost:4566/my-s3-bucket/jeans.png"}, 
        {"id": "3", "name": "Sneakers", "price": Decimal('49.99'), "description": "Sneakers von de Marke adidas",  "image": "http://localhost:4566/my-s3-bucket/sneakers.png" }
    ]
    
    for product in products:
        table.put_item(
            Item={ 
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "description": product["description"],
                "image": product["image"]
            }
        )
    print(f"Inserted {len(products)} initial products.")

# --- create bucket if not exists ---
try:
    s3.head_bucket(Bucket=S3_BUCKET)
    print(f"Bucket '{S3_BUCKET}' already exists.")
except botocore.exceptions.ClientError:
    print(f"Creating bucket '{S3_BUCKET}'")
    s3.create_bucket(
        Bucket=S3_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-central-1"}
    )

# Upload all files in the folder
for filename in os.listdir(IMAGES_PATH):
    filepath = os.path.join(IMAGES_PATH, filename)
    if os.path.isfile(filepath):
        print(f"Uploading: {filename}")
        s3.upload_file(filepath, S3_BUCKET, filename)

# Routen
@app.route("/")
def home():
    return "Willkommen zur E-Commerce-API!"

@app.route("/products", methods=["GET"])
def get_products():
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    return jsonify(response.get("Items", []))

@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json()
    table = dynamodb.Table(TABLE_NAME)
    product_id = str(uuid.uuid4())
    item = {
        "id": product_id,
        "name": data["name"],
        "price": data["price"]
    }
    table.put_item(Item=item)
    return jsonify({"message": "Produkt hinzugefügt", "id": product_id}), 201

@app.route('/notifications', methods=['POST'])
def notify():
    data = request.get_json()
    print(f"DEBUG: Got payload: {data}")
    if not data or 'productId' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    return jsonify({'message': 'OK'}), 200



# Main
if __name__ == "__main__":
    create_table_if_not_exists()
    insert_initial_data()
    topic_arn = create_sns_topic()
    subscribe_to_topic(topic_arn)
    app.run(host="0.0.0.0", port=5000)