import os
from dotenv import load_dotenv
from flask_login import LoginManager
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
secretKey = os.getenv("secret_key")

UPLOAD_FOLDER = '/Users/mem/personal/transactions/uploadFolder'

app = Flask(__name__)
app.config['SECRET_KEY'] = secretKey
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from BankProject import routes

