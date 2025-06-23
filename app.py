from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime,time
import pytz
import time as systime
from xhtml2pdf import pisa
from io import BytesIO
from flask import make_response
import os
import qrcode

def generate_qr(location_url, filename):
    img = qrcode.make(location_url)
    filepath = os.path.join("static", filename.replace(".png", ".jpg"))
    img = img.convert("RGB")
    img.save(filepath, "JPEG")
    return filepath  # ← this is already like 'static/koothali_qr.jpg'
    


def get_clinic_time(place, date_str):
    day = datetime.strptime(date_str, "%Y-%m-%d").strftime('%A')  # e.g., 'Monday'
    if place.lower() == "koothali":
        timings = {
            "Sunday": "08:00 AM – 09:30 AM",
            "Monday": "09:45 AM – 01:00 PM",
            "Tuesday": "❌ No Consultation",
            "Wednesday": "09:45 AM – 01:00 PM",
            "Thursday": "09:45 AM – 01:00 PM",
            "Friday": "09:45 AM – 01:00 PM",
            "Saturday": "09:45 AM – 01:00 PM"
        }
    else:
        timings = {
            "Sunday": "11:00 AM – 01:00 PM",
            "Monday": "04:45 PM – 07:00 PM",
            "Tuesday": "❌ No Consultation",
            "Wednesday": "04:45 PM – 07:00 PM",
            "Thursday": "04:45 PM – 07:00 PM",
            "Friday": "04:45 PM – 07:00 PM",
            "Saturday": "04:45 PM – 07:00 PM"
        }
    return timings.get(day, "Unavailable")


def safe_append(sheet, row, max_retries=5):
    for attempt in range(max_retries):
        try:
            values = sheet.get_all_values()
            token = len(values)
            row[0] = token
            sheet.append_row(row)
            return token
        except Exception as e:
            if attempt < max_retries - 1:
                systime.sleep(0.5)
            else:
                raise e


app = Flask(__name__)

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open sheets by name
koothali_sheet = client.open("Koothali_Appointments")
koorachundu_sheet = client.open("Koorachundu_Appointments")

@app.route('/download_pdf')
def download_pdf():
    name = request.args.get('name')
    date = request.args.get('date')
    place = request.args.get('place')
    token = request.args.get('token')

    time_str = get_clinic_time(place, date)

    if place.lower() == "koothali":
        map_url = "https://www.google.com/maps/place/7J3QHQP8%2BX7R/@11.5874875,75.7630657,17z/..."
        qr_file = "koothali_qr.jpg"
    else:
        map_url = "https://www.google.com/maps/place/7J3QGRQW%2B96J/@11.5384625,75.8429407,17z/..."
        qr_file = "koorachundu_qr.jpg"

    qr_path = generate_qr(map_url, qr_file)

    rendered = render_template(
        "pdf_template.html",
        name=name,
        date=date,
        place=place,
        token=token,
        time=time_str,
        qr_image=qr_path
    )

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(rendered.encode("utf-8")), dest=pdf)

    if pisa_status.err:
        return "Error generating PDF", 500

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=appointment_{token}.pdf'
    return response





@app.route('/')
def index():
    return render_template('index.html')

@app.route('/koothali', methods=['GET', 'POST'])
def koothali():
    if request.method == 'POST':
        botcheck = request.form.get('botcheck')
        if botcheck:
            return render_template('koothali.html', message="Spam detected. Booking not allowed.")

        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']
        email = request.form['email'].replace(" ", "").lower()


       
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()

        if date == current_date and current_time>= time(23, 0):  # 1:00 PM or later
            return render_template('koothali.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koothali_sheet, date)
        row = [0, name, age, date, email]

        token = safe_append(sheet, row)

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
        sheet.append_row(["Token Number", "Name", "Age", "Date", "Email"])

          # ✅ Make first row bold and underlined
        sheet.format("A1:E1", {
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
        botcheck = request.form.get('botcheck')
        if botcheck:
            return render_template('koothali.html', message="Spam detected. Booking not allowed.")

        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']
        email = request.form['email'].replace(" ", "").lower()



        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()

        if date == current_date and current_time.hour >= 19 :  # 7:00 PM or later
            return render_template('koorachundu.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koorachundu_sheet, date)
        row = [0, name, age, date, email]

        token = safe_append(sheet, row)

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
        sheet.append_row(["Token Number", "Name", "Age", "Date", "Email"])

             # ✅ Make first row bold and underlined
        sheet.format("A1:E1", {
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