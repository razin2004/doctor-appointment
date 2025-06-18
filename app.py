from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open sheets by name
koothali_sheet = client.open("Koothali_Appointments")
koorachundu_sheet = client.open("Koorachundu_Appointments")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/koothali', methods=['GET', 'POST'])
def koothali():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        date = request.form['date']

        sheet = get_or_create_sheet(koothali_sheet, date)
        row = [name, age, date]
        sheet.append_row(row)

        token = len(sheet.get_all_values())
        return render_template('confirmation.html', name=name, date=date, token=token, place="Koothali")

    return render_template('koothali.html')

@app.route('/koorachundu', methods=['GET', 'POST'])
def koorachundu():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        date = request.form['date']

        sheet = get_or_create_sheet(koorachundu_sheet, date)
        row = [name, age, date]
        sheet.append_row(row)

        token = len(sheet.get_all_values())

        return render_template('confirmation.html', name=name, date=date, token=token, place="Koorachundu")

    return render_template('koorachundu.html')

def get_or_create_sheet(spreadsheet, date):
    try:
        return spreadsheet.worksheet(date)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=date, rows="100", cols="3")

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # use 5000 locally if PORT is not set
    app.run(host='0.0.0.0', port=port)