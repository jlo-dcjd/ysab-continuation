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

# pre-populate fields auto
def get_app_list():
    cluster = MongoClient(mongo_uri)
    db = cluster[db_name]
    collection = db['ysab']
    # Retrieve all records from the collection
    cursor = collection.find()
    # Convert the cursor to a list of dictionaries
    records = list(cursor)
    # Create a Pandas DataFrame
    df = pd.DataFrame(records)
    df['app_record'] = pd.concat([df.timestamp.str[:10], df[['name', 'app_title', 'email', 'phone', 'title', 'amount', 'service_area', 'facility', 'address', 'problem_statement', 'category1', 'category2', 'category3', 'category4', 'category5', 'category6', 'category7', 'description1', 'description2', 'description3', 'description4', 'description5', 'description6', 'description7', 'cost1', 'cost2', 'cost3', 'cost4', 'cost5', 'cost6', 'cost7', 'items1', 'items2', 'items3', 'items4', 'items5', 'items6', 'items7', 'total1', 'total2', 'total3', 'total4', 'total5', 'total6', 'total7', 'grandTotal', 'youth_total', 'benefit_per_youth']].astype(str)], axis=1).apply(lambda row: ' : '.join(row), axis=1)
    cluster.close()
    return df.app_record.to_list()

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html', app_list = get_app_list())

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
