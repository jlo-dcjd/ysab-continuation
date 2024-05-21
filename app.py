from flask import Flask, request, render_template, jsonify, send_file
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
import os
import pytz
import pandas as pd
import re
from bs4 import BeautifulSoup

load_dotenv() 

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")

app = Flask(__name__)

cluster = MongoClient(mongo_uri)
db = cluster[db_name]
collection = db['ysab-continuation']

def get_timestamp():
    central_timezone = pytz.timezone('America/Chicago')
    current_time = datetime.datetime.now(central_timezone)
    timestamp = current_time.strftime("%m-%d-%Y %H:%M")
    return timestamp

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
    # form type - A: application M: progress report mid-term F: progress report final C: continuation
    form_type = 'C'
    # Generate unique ID
    unique_id = f"{year}-{application_number:03d}-{project_abbreviation}-{form_type}"
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

def make_app_form(form_data):
    # Read the HTML file
    with open(r'templates/ysab-continuation.html', 'r', encoding="utf8") as file:
        html_content = file.read()
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the existing h3 tag and update it with the timestamp
    h4_tag = soup.find('h4')
    if h4_tag:
        h4_tag.string = f"{get_timestamp()}"

    # Update the value attribute of input fields based on dictionary keys
    for key, value in form_data.items():
        input_field = soup.find('input', {'id': key})
        if input_field:
            input_field['value'] = value
        select_field = soup.find('select', {'id': key})
        if select_field:  
            # Clear any previously selected option
            for option in select_field.find_all('option'):
                if 'selected' in option.attrs:
                    del option.attrs['selected']
                # Set the selected attribute for the matching option
                if option.get('value') == value:
                    option['selected'] = 'selected'
                    
        # Handle textarea fields
        textarea_field = soup.find('textarea', {'id': key})
        if textarea_field:
            textarea_field.string = value
            
        # Handle table input fields
        table_input_field = soup.find('input', {'name': key})
        if table_input_field:
            table_input_field['value'] = value

        # Save the updated HTML content to a file
        with open(r'templates/ysab-continuation-record.html', 'w') as file:
            file.write(str(soup))


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

            form_data = {'_id': app_id(), 'timestamp': get_timestamp(), **form_data}

            # Insert data into MongoDB
            collection.insert_one(form_data)
           # make html application w/ user responses
            make_app_form(form_data)

            # return jsonify({'success': True, 'message': 'Form data submitted successfully'})
            return render_template('confirmation.html', name=name, email=email)
        except Exception as e:
            # return jsonify({'success': False, 'error': str(e)})
             return render_template('error.html', error=str(e))
        
@app.route('/download')
def download_file():
    p = r'templates/ysab-continuation-record.html'
    return send_file(p, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)
