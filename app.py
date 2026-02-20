import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

app = Flask(__name__)

# ==============================
# CONFIGURATION
# ==============================

# Secret key
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecretkey")

# Database configuration (Render provides DATABASE_URL)
database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==============================
# DATABASE SETUP
# ==============================

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ==============================
# MODELS
# ==============================

class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat()
        }

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return jsonify({"message": "Client Management API is running"}), 200

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

# ==============================
# CREATE CLIENT
# ==============================

@app.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    if not all(k in data for k in ("first_name", "last_name", "email")):
        return jsonify({"error": "Missing required fields"}), 400

    existing_client = Client.query.filter_by(email=data["email"]).first()
    if existing_client:
        return jsonify({"error": "Email already exists"}), 400

    client = Client(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone=data.get("phone")
    )

    db.session.add(client)
    db.session.commit()

    return jsonify(client.to_dict()), 201

# ==============================
# GET ALL CLIENTS
# ==============================

@app.route("/clients", methods=["GET"])
def get_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify([client.to_dict() for client in clients]), 200

# ==============================
# GET SINGLE CLIENT
# ==============================

@app.route("/clients", methods=["GET"])
def get_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify([client.to_dict() for client in clients]), 200

# ==============================
# UPDATE CLIENT
# ==============================

@app.route("/clients/<int:id>", methods=["PUT"])
def update_client(id):
    client = Client.query.get_or_404(id)
    data = request.get_json()

    client.first_name = data.get("first_name", client.first_name)
    client.last_name = data.get("last_name", client.last_name)
    client.email = data.get("email", client.email)
    client.phone = data.get("phone", client.phone)

    db.session.commit()

    return jsonify(client.to_dict()), 200

# ==============================
# DELETE CLIENT
# ==============================

@app.route("/clients/<int:id>", methods=["DELETE"])
def delete_client(id):
    client = Client.query.get_or_404(id)

    db.session.delete(client)
    db.session.commit()

    return jsonify({"message": "Client deleted"}), 200

# ==============================
# ERROR HANDLERS
# ==============================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ==============================
# RUN LOCALLY
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)