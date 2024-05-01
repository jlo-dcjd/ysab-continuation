from flask import Flask, request, render_template, jsonify
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
import os
import pytz
import pandas as pd
import re

load_dotenv() 

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")

app = Flask(__name__)

cluster = MongoClient(mongo_uri)
db = cluster[db_name]
collection = db['ysab-continuation']

def get_app_num():
    cluster = MongoClient(mongo_uri)
    db = cluster[db_name]
    collection = db['ysab']
    # Retrieve all records from the collection
    cursor = collection.find()
    # Convert the cursor to a list of dictionaries
    records = list(cursor)
    # Create a Pandas DataFrame
    df = pd.DataFrame(records)
    cluster.close()
    return df.shape[0] + 1

def app_id():
    year = datetime.datetime.now().year
    application_number = get_app_num()
    project_name = request.form.get('title')
    project_abbreviation = re.sub(r'[^a-zA-Z0-9\s]', '', project_name)
    project_abbreviation = "".join(word[0] for word in project_abbreviation.split())
    funding = 'YSAB'
    # form type - A: application M: progress report mid-term F: progress report final
    form_type = 'A'
    # Generate unique ID
    unique_id = f"{year}-{application_number:03d}-{project_abbreviation}-{funding}-{form_type}"
    return unique_id

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
        try:     
            # Get form data
            form_data = request.form.to_dict()
            name = request.form.get('name')
            email = request.form.get('email')

            #timestamp
            central_timezone = pytz.timezone('America/Chicago')
            current_time = datetime.datetime.now(central_timezone)
            timestamp = current_time.strftime("%m-%d-%Y %H:%M")
            
            form_data = {'_id': app_id(), 'timestamp': timestamp, **form_data}

            # Insert data into MongoDB
            collection.insert_one(form_data)

            # return jsonify({'success': True, 'message': 'Form data submitted successfully'})
            return render_template('confirmation.html', name=name, email=email)
        except Exception as e:
            # return jsonify({'success': False, 'error': str(e)})
             return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=False)
