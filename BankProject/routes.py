from flask import render_template, request, url_for, session, redirect, flash
from BankProject.models import User, Transaction
from BankProject import app
from BankProject import db
from BankProject.forms import RegistrationForm, LoginForm
from flask_login import login_user, current_user, logout_user

from werkzeug.utils import secure_filename
import os
import pytesseract
import requests
from PIL import Image
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
apiKey = os.getenv("API_KEY")
client = OpenAI(api_key=apiKey)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/home')
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part')
            return render_template('input.html')
        image = request.files['image']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if image.filename == '':
            flash('No selected file')
            return render_template('input.html')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('organize'))
    return render_template('input.html')

@app.route('/organize')
def organize():
    return 'Hello world'

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('upload_file'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username = form.username.data, email = form.email.data, password = form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('upload_file'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember = form.remember.data)
            return redirect(url_for('upload_file'))
        else:
            flash('Login Unsuccessful.', 'danger')
    return render_template('login.html', title = 'Login', form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

ALLOWED_EXTENSION = {'png'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

def categorize_transaction(transaction_description):
    prompt = f"Categorize the transaction: {transaction_description}. Use one of the following words and make sure to give only one word: Dining, Clothes, Groceries, Rent, Transportation, Entertainment, Health, Miscellaneous"
    chat_completion = client.chat.completions.create(
        messages = [{
            "role":"user",
            "content":prompt
        }],
        model="gpt-3.5-turbo"
    )
    return chat_completion.choices[0].message.content

def extract_purchases_bofa(text):
    start_index = text.find("Purchases and Adjustments") + len("Purchases and Adjustments")
    end_index = text.find("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD")
    last_index = text.find("Interest Charged")

    purchases_and_adjustments_section = text[start_index:end_index].strip()

    lines = purchases_and_adjustments_section.split('\n')

    extracted_transactions = []
    extracted_dates = []
    extracted_prices = []

    for line in lines:
        parts = line.split(' ', 2)
        dateText = parts[0]
        transactionText = ' '.join(parts[-1].split()[:-3])
        transactionText = transactionText.replace('=', '')
        priceText = parts[-1].split()[-1]

        extracted_dates.append(dateText)
        extracted_transactions.append(transactionText)
        extracted_prices.append(priceText)

    for i, input in enumerate(extracted_transactions):
        words = input.split()
        result = ' '.join(words[:-2])
        extracted_transactions[i] = result

    return extracted_transactions, extracted_dates, extracted_prices

def extract_purchases_chase(text):
    arrayText = text.split('\n')
    joinArray = '|'.join(arrayText)
    finalArray = joinArray.split('||')
    for index in range(len(finalArray)):
        finalArray[index] = finalArray[index].split('|')


    extracted_transactions = []
    extracted_dates = []
    extracted_prices = []

    for i in range(3):
        for input in finalArray[i]:
            if i == 0:
                extracted_dates.append(input)
            elif i == 1:
                words = input.split()
                result = ' '.join(words[:-2])
                extracted_transactions.append(result)
            elif i == 2:
                extracted_prices.append(input)
    
    return extracted_transactions, extracted_dates, extracted_prices

def createCategory(extractedTransactions):
    for index, transaction in enumerate(extractedTransactions):
        category = categorize_transaction(transaction)
        extractedTransactions[index] = category
    return extractedTransactions

