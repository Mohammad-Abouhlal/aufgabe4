from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import os
import uuid
from boto3.dynamodb.types import Decimal

app = Flask(__name__)
CORS(app)

# Konfiguration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
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

client = boto3.client(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=DYNAMODB_ENDPOINT
)

# Prüfen + Erstellen der Tabelle
def create_table_if_not_exists():
    try:
        client.describe_table(TableName=TABLE_NAME)
        print(f"Tabelle '{TABLE_NAME}' existiert bereits.")
    except client.exceptions.ResourceNotFoundException:
        print(f"Tabelle '{TABLE_NAME}' wird erstellt...")
        client.create_table(
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
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"Tabelle '{TABLE_NAME}' wurde erfolgreich erstellt.")

table_name = 'Products'

# Funktion zum Hinzufügen von Beispiel-Daten
def insert_initial_data():
    table = dynamodb.Table(table_name)
    
    # Hier definierst du die initialen Produkte
    products = [
        {"id": "1", "name": "T-Shirt", "price": Decimal('19.99'), "description": "T-Shirt von de Marke C&A", "image": "tshirt.png" },
        {"id": "2", "name": "Jeans", "price": Decimal('39.99'), "description": "Jeans von der Marke H&M", "image": "jeans.png"}, 
        {"id": "3", "name": "Sneakers", "price": Decimal('49.99'), "description": "Sneakers von de Marke adidas",  "image": "sneakers.png" }
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

# Main
if __name__ == "__main__":
    create_table_if_not_exists()
    insert_initial_data()
    app.run(host="0.0.0.0", port=5000)
