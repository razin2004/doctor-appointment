from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime,time
import pytz
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
        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']

       
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()

        if date == current_date and current_time>= time(13, 0):  # 1:00 PM or later
            return render_template('koothali.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koothali_sheet, date)
        current_count = len(sheet.get_all_values())  # Includes header
        token = current_count  # Because token = row number excluding header

        row = [token, name, age, date]
        sheet.append_row(row)
        sheet.format("C2:C", {
        "horizontalAlignment": "CENTER"
        })

        return render_template('confirmation.html', name=name, date=date, token=token, place="Koothali")

    return render_template('koothali.html')
def get_or_create_sheet(spreadsheet, date):
    try:
        return spreadsheet.worksheet(date)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=date, rows="100", cols="4")
        sheet.append_row(["Token Number", "Name", "Age", "Date"]) # ✅ Add column headers
          # ✅ Make first row bold and underlined
        sheet.format("A1:D1", {
        "textFormat": {
        "bold": True,
        "underline": True
        },
        "horizontalAlignment": "CENTER"
        })
        # ✅ Token numbers: bold and center-aligned
        sheet.format("A2:A", {
            "textFormat": {
                "bold": True
            },
            "horizontalAlignment": "CENTER"
        })
        # ✅ Age column (C) and Date column (D): left align
        sheet.format("C2:C", {
            "horizontalAlignment": "CENTER"
        })
        sheet.format("D2:D", {
            "horizontalAlignment": "LEFT"
        })


        return sheet

@app.route('/koorachundu', methods=['GET', 'POST'])
def koorachundu():
    if request.method == 'POST':
        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']

        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()

        if date == current_date and current_time.hour >= 19 :  # 7:00 PM or later
            return render_template('koorachundu.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koorachundu_sheet, date)
        current_count = len(sheet.get_all_values())  # Includes header
        token = current_count  # Because token = row number excluding header

        row = [token, name, age, date]
        sheet.append_row(row)
        sheet.format("C2:C", {
        "horizontalAlignment": "CENTER"
        })
        return render_template('confirmation.html', name=name, date=date, token=token, place="koorachundu")

    return render_template('koorachundu.html')

def get_or_create_sheet(spreadsheet, date):
    try:
        return spreadsheet.worksheet(date)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=date, rows="100", cols="3")
        sheet.append_row(["Token Number", "Name", "Age", "Date"])  # ✅ Add column headers
             # ✅ Make first row bold and underlined
        sheet.format("A1:D1", {
    "textFormat": {
        "bold": True,
        "underline": True
    },
    "horizontalAlignment": "CENTER"
})
        # ✅ Token numbers: bold and left-aligned
        sheet.format("A2:A", {
            "textFormat": {
                "bold": True
            },
            "horizontalAlignment": "CENTER"
        })
        # ✅ Age column (C) and Date column (D): left align
        sheet.format("C2:C", {
            "horizontalAlignment": "CENTER"
        })
        sheet.format("D2:D", {
            "horizontalAlignment": "LEFT"
        })
        return sheet


@app.route('/get_token_count_koothali', methods=['POST'])
def get_token_count_koothali():
    from flask import jsonify
    date = request.json.get('date')
    if not date:
        return jsonify({'count': 0})

    try:
        sheet = get_or_create_sheet(koothali_sheet, date)
        count = len(sheet.get_all_values())-1
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
        count = len(sheet.get_all_values())-1
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # use 5000 locally if PORT is not set
    app.run(host='0.0.0.0', port=port)