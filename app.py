from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime,time

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
        date_str = request.form['date']  # from form input: YYYY-MM-DD

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return render_template('koothali.html', message="Invalid date format.")

        today = datetime.today().date()
        now_time = datetime.now().time()

        # ✅ Block if selected date is today and current time is after 1:00 PM
        if selected_date == today and now_time >= time(13, 0):
            return render_template('koothali.html', message="Today's booking is closed as the clinic timing is over.")

        # ✅ Allow booking
        sheet = get_or_create_sheet(koothali_sheet, date_str)
        row = [name, age, date_str]
        sheet.append_row(row)

        token = len(sheet.get_all_values())
        return render_template('confirmation.html', name=name, date=date_str, token=token, place="Koothali")

    return render_template('koothali.html')

@app.route('/koorachundu', methods=['GET', 'POST'])
def koorachundu():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        date = request.form['date']

        # Check if the selected date is today
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().time()

        if date == current_date and current_time.hour >= 20 :  # 7:00 PM or later
            return render_template('koorachundu.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koorachundu_sheet, date)
        row = [name, age, date]
        sheet.append_row(row)

        token = len(sheet.get_all_values())
        return render_template('confirmation.html', name=name, date=date, token=token, place="koorachundu")

    return render_template('koorachundu.html')

def get_or_create_sheet(spreadsheet, date):
    try:
        return spreadsheet.worksheet(date)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=date, rows="100", cols="3")

@app.route('/get_token_count_koothali', methods=['POST'])
def get_token_count_koothali():
    from flask import jsonify
    date = request.json.get('date')
    if not date:
        return jsonify({'count': 0})

    try:
        sheet = get_or_create_sheet(koothali_sheet, date)
        count = len(sheet.get_all_values())
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

@app.route('/get_token_count_koorachundu', methods=['POST'])
def get_token_count_koorachundu():
    from flask import jsonify
    date = request.json.get('date')
    if not date:
        return jsonify({'count': 0})

    try:
        sheet = get_or_create_sheet(koorachundu_sheet, date)
        count = len(sheet.get_all_values())
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # use 5000 locally if PORT is not set
    app.run(host='0.0.0.0', port=port)