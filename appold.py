from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

# Google Apps Script endpoints for each clinic
KOOTHALI_URL = 'https://script.google.com/macros/s/AKfycbzJD-cw3n0hvDHflDToVKDFscLtHMACzViHjPJul3ma_X5TsuhrLUamTTfUmKW7foHz/exec'
KOORACHUNDU_URL = 'https://script.google.com/macros/s/AKfycbwXmCEpGwdiIISpSHFgsXKqnXAjkCjEKqNWyvQYMm_r2UeiDGMFjDvKBc5-3NLdwjdtNA/exec'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/koothali', methods=['GET', 'POST'])
def koothali():
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form['age'].strip()
        date = request.form['date'].strip()
        clinic = 'Koothali'

        data = {
            'clinic': clinic,
            'name': name,
            'age': age,
            'date': date
        }

        try:
            response = requests.post(KOOTHALI_URL, json=data)
            result = response.json()
            if result.get('status') == 'success':
                return redirect(url_for('confirmation', token=result['token'], clinic=clinic, name=name))
            else:
                return 'Error saving appointment. Please try again.'
        except Exception as e:
            return f"Error: {e}"

    return render_template('koothali.html')

@app.route('/koorachundu', methods=['GET', 'POST'])
def koorachundu():
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form['age'].strip()
        date = request.form['date'].strip()
        clinic = 'Koorachundu'

        data = {
            'clinic': clinic,
            'name': name,
            'age': age,
            'date': date
        }

        try:
            response = requests.post(KOORACHUNDU_URL, json=data)
            result = response.json()
            if result.get('status') == 'success':
                return redirect(url_for('confirmation', token=result['token'], clinic=clinic, name=name))
            else:
                return 'Error saving appointment. Please try again.'
        except Exception as e:
            return f"Error: {e}"

    return render_template('koorachundu.html')

@app.route('/confirmation')
def confirmation():
    token = request.args.get('token', 'N/A')
    clinic = request.args.get('clinic', 'Clinic')
    name = request.args.get('name', 'Patient')
    return render_template('confirmation.html', token=token, clinic=clinic, name=name)

if __name__ == '__main__':
    app.run(debug=True)
