from PIL import Image
import pytesseract
import requests
from openai import OpenAI
import time
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
apiKey = os.getenv("API_KEY")
client = OpenAI(api_key=apiKey)

def recentFile(folder_path):
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.DS_Store') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    if not files:
        return None
    most_recent_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
    return os.path.join(folder_path, most_recent_file)


def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

def extract_purchases_and_adjustments(text):

    start_index = text.find("Purchases and Adjustments") + len("Purchases and Adjustments")
    end_index = text.find("TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD")
    last_index = text.find("Interest Charged")

    purchases_and_adjustments_section = text[start_index:end_index].strip()
    totalPrice = text[end_index:last_index].strip()

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

    transactionFinal = '\n'.join(extracted_transactions)

    return transactionFinal, extracted_dates, extracted_prices, totalPrice

folderPath = "/Users/thamim/vscodestuffs/personal/expensemanagerproject/bankStatements"

mostRecent = recentFile(folderPath)

extracted_text = extract_text_from_image(mostRecent)

transaction_text, dates, prices, totalPrice = extract_purchases_and_adjustments(extracted_text)

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

transactions = transaction_text.split('\n')  

data = {'Date': [], 'Transaction': [], 'Category': [], 'Amount': []}

print("Beginning Excel transfer.")

for i in range(0, len(transactions), 3):
    for j in range(min(3, len(transactions) - i)):
        generated_category = categorize_transaction(transactions[i + j])
        data['Date'].append(dates[i+j])
        data['Transaction'].append(transactions[i+j])
        data['Category'].append(generated_category)
        data['Amount'].append(prices[i+j])
        time.sleep(21)








df = pd.DataFrame(data)
# # Save to Excel file with adjusted column width
# excel_path = '/Users/thamim/Downloads/Transactions.xlsx'
# with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
#     df.to_excel(writer, index=False, sheet_name='Sheet1')
#     workbook = writer.book
#     worksheet = writer.sheets['Sheet1']
    
#     for i, col in enumerate(df.columns):
#         max_len = df[col].astype(str).apply(len).max()
#         max_len = max(max_len, len(col) + 2)
#         worksheet.set_column(i, i, max_len)

# print("Finished Excel transfer.")

# Existing code...

# Save to Excel file with adjusted column width
excel_path = '/Users/thamim/Downloads/Transactions.xlsx'

# Try to read the existing Excel file
try:
    existing_df = pd.read_excel(excel_path, sheet_name='Sheet1')
    # Concatenate existing data with new data
    df = pd.concat([existing_df, df], ignore_index=True)
except FileNotFoundError:
    # If the file doesn't exist, write the new data directly
    df.to_excel(excel_path, index=False, sheet_name='Sheet1', engine='openpyxl')

# Write the updated DataFrame to the Excel file without overwriting
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    
    for i, col in enumerate(df.columns):
        max_len = df[col].astype(str).apply(len).max()
        max_len = max(max_len, len(col) + 2)
        
        # Use column_dimensions instead of set_column
        worksheet.column_dimensions[chr(65 + i)].width = max_len

print("Finished Excel transfer.")


