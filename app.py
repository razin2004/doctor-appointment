from flask import Flask, render_template, request, redirect, url_for, session, flash
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
    day = datetime.strptime(date_str, "%Y-%m-%d").strftime('%A')
    
    sheet = client.open("Clinic_Schedule").sheet1
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("Place", "")).lower() == place.lower() and str(row.get("Day", "")) == day:
                if row.get("Status") == "Closed":
                    return "❌ No Consultation"
                return f"{row.get('Start', '')} – {row.get('End', '')}"
    except Exception:
        pass
    
    return "Unavailable"

def is_on_leave(place, date):
    sheet = client.open("Doctor_Leave").sheet1
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("Place", "")).lower() == place.lower() and str(row.get("Date", "")) == date:
                return True
    except Exception:
        pass
    
    return False


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

from datetime import datetime, timedelta
import json

def get_end_time_from_string(time_str):
    if "No Consultation" in time_str or time_str == "Unavailable":
        return None
    
    try:
        end_part = time_str.split("–")[1].strip()  # "01:00 PM"
        end_time = datetime.strptime(end_part, "%I:%M %p").time()
        return end_time
    except:
        return None
app = Flask(__name__)
app.secret_key = "your_secret_key_here"
# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open sheets by name
koothali_sheet = client.open("Koothali_Appointments")
koorachundu_sheet = client.open("Koorachundu_Appointments")

@app.route('/doctor-login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'GET':
        if session.get('doctor'):
            return redirect('/doctor-dashboard')
        return redirect('/')

    username = request.form['username']
    password = request.form['password']

    if username == "doctor" and password == "1234":
        session['doctor'] = True
        return redirect('/doctor-dashboard')

    return render_template('index.html', error="Invalid username or password")

@app.route('/doctor-dashboard')
def doctor_dashboard():
    if not session.get('doctor'):
        return redirect('/doctor-login')

    try:
        records = client.open("Clinic_Schedule").sheet1.get_all_records()
        schedule_json = json.dumps(records)
    except:
        schedule_json = "[]"
        
    try:
        leave_records = client.open("Doctor_Leave").sheet1.get_all_records()
    except:
        leave_records = []

    return render_template('doctor_dashboard.html', schedule_json=schedule_json, leave_records=leave_records)
@app.route('/add-leave', methods=['POST'])
def add_leave():
    if not session.get('doctor'):
        return redirect('/doctor-login')

    place = request.form['place']
    date = request.form['date']

    sheet = client.open("Doctor_Leave").sheet1
    try:
        records = sheet.get_all_records()
        for row in records:
            if str(row.get("Place", "")).lower() == place.lower() and str(row.get("Date", "")) == date:
                flash(f"Temporary leave already exists for {place.capitalize()} on {date}!", "error")
                return redirect('/doctor-dashboard')
    except Exception:
        pass

    sheet.append_row([place, date, "Temporary Leave"])
    
    flash(f"Temporary leave created for {place.capitalize()} on {date}.", "success")

    return redirect('/doctor-dashboard')

@app.route('/delete-leave', methods=['POST'])
def delete_leave():
    if not session.get('doctor'):
        return redirect('/doctor-login')

    place = request.form['place']
    date = request.form['date']

    try:
        sheet = client.open("Doctor_Leave").sheet1
        records = sheet.get_all_values()
        
        for i, row in enumerate(records):
            if i > 0 and row[0].lower() == place.lower() and row[1] == date:
                sheet.delete_rows(i+1)
                flash(f"Temporary leave deleted for {place.capitalize()} on {date}.", "success")
                break
    except Exception as e:
        flash(f"Error deleting leave: {str(e)}", "error")

    return redirect('/doctor-dashboard')

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
    try:
        sheet = client.open("Clinic_Schedule").sheet1
        records = sheet.get_all_records()
        koothali_schedule = [r for r in records if r["Place"].lower() == "koothali"]
        koorachundu_schedule = [r for r in records if r["Place"].lower() == "koorachundu"]
    except Exception as e:
        koothali_schedule = []
        koorachundu_schedule = []

    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    tomorrow = today + timedelta(days=1)
    
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    koothali_leaves = []
    koorachundu_leaves = []
    
    try:
        lsheet = client.open("Doctor_Leave").sheet1
        l_records = lsheet.get_all_records()
        for r in l_records:
            if r["Date"] in [today_str, tomorrow_str]:
                if r["Place"].lower() == "koothali":
                    koothali_leaves.append(r["Date"])
                elif r["Place"].lower() == "koorachundu":
                    koorachundu_leaves.append(r["Date"])
    except:
        pass

    return render_template('index.html', 
                           koothali_schedule=koothali_schedule, 
                           koorachundu_schedule=koorachundu_schedule,
                           koothali_leaves=koothali_leaves,
                           koorachundu_leaves=koorachundu_leaves,
                           today_str=today_str,
                           tomorrow_str=tomorrow_str)

@app.route('/update-schedule', methods=['POST'])
def update_schedule():
    if not session.get('doctor'):
        return redirect('/doctor-login')

    place = request.form['place']
    day = request.form['day']
    start = request.form.get('start', '')
    end = request.form.get('end', '')
    status = request.form['status']  # Open / Closed

    sheet = client.open("Clinic_Schedule").sheet1
    records = sheet.get_all_records()

    for i, row in enumerate(records, start=2):
        if row["Place"].lower() == place.lower() and row["Day"] == day:
            sheet.update(f"A{i}:E{i}", [[place, day, start, end, status]])
            flash(f"Schedule updated for {place.capitalize()} on {day}.", "success")
            break

    return redirect('/doctor-dashboard')

@app.route('/check_leave', methods=['POST'])
def check_leave():
    from flask import jsonify
    data = request.json
    place = data.get('place')
    date = data.get('date')

    return jsonify({'leave': is_on_leave(place, date)})
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
@app.route('/koothali', methods=['GET', 'POST'])
def koothali():
    if request.method == 'POST':
        botcheck = request.form.get('botcheck')
        if botcheck:
            return render_template('koothali.html', message="Spam detected. Booking not allowed.")

        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']
        phone = request.form['phone'].strip()


       
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()
        if is_on_leave("koothali", date):
            return render_template(
                'koothali.html',
                message="Doctor is on leave on the selected date. Booking unavailable."
            )
        clinic_time = get_clinic_time("koothali", date)
        if "No Consultation" in clinic_time or clinic_time == "Unavailable":
            return render_template('koothali.html', message="Clinic is closed on the selected date.")
        end_time = get_end_time_from_string(clinic_time)

        if date == current_date and end_time and current_time >= end_time:
            return render_template('koothali.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koothali_sheet, date)
        row = [0, name, age, date, phone]

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
        sheet = spreadsheet.add_worksheet(title=date, rows="100", cols="5")

        sheet.append_row(["Token Number", "Name", "Age", "Date", "Phone"])

        sheet.format("A1:E1", {
            "textFormat": {"bold": True, "underline": True},
            "horizontalAlignment": "CENTER"
        })

        sheet.format("A2:A", {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        })

        sheet.format("C2:C", {"horizontalAlignment": "CENTER"})
        sheet.format("D2:D", {"horizontalAlignment": "LEFT"})

        return sheet

@app.route('/koorachundu', methods=['GET', 'POST'])
def koorachundu():
    if request.method == 'POST':
        botcheck = request.form.get('botcheck')
        if botcheck:
            return render_template('koorachundu.html', message="Spam detected. Booking not allowed.")

        name = ' '.join(request.form['name'].split()).title()


        age = int(request.form['age'])  # ← this removes leading zeros

        date = request.form['date']
        phone = request.form['phone'].strip()



        
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.time()
        if is_on_leave("koorachundu", date):
            return render_template(
                'koorachundu.html',
                message="Doctor is on leave on the selected date. Booking unavailable."
            )
        clinic_time = get_clinic_time("koorachundu", date)
        if "No Consultation" in clinic_time or clinic_time == "Unavailable":
            return render_template('koorachundu.html', message="Clinic is closed on the selected date.")
        end_time = get_end_time_from_string(clinic_time)

        if date == current_date and end_time and current_time >= end_time:
            return render_template('koorachundu.html', message="Today's booking is closed as the clinic timing is over.")

        sheet = get_or_create_sheet(koorachundu_sheet, date)
        row = [0, name, age, date, phone]

        token = safe_append(sheet, row)

        sheet.format("C2:C", {
        "horizontalAlignment": "CENTER"
        })
        return render_template('confirmation.html', name=name, date=date, token=token, place="Koorachundu")

    return render_template('koorachundu.html')

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
    debug=True if os.environ.get("FLASK_ENV") == "development" else False
    port = int(os.environ.get("PORT", 5000))  # use 5000 locally if PORT is not set
    app.run(host='0.0.0.0', port=port)