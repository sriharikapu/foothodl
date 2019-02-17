# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, render_template
import requests
import os
import logging
from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client as TwilioClient
from google.cloud import datastore
app = Flask(__name__, static_folder="static", template_folder="templates")

def ambassador_key(client, number):
    # [START datastore_named_key]
    key = client.key('FoothodlAmbassadorUser', number)
    # [END datastore_named_key]
    return key
    
def member_key(client, number):
    # [START datastore_named_key]
    key = client.key('FoothodlMemberUser', number)
    # [END datastore_named_key]
    return key
    
def generate_confirmation_code():
    import random
    return random.randint(100, 999)
    
def format_number(number):
    if number[0] == '1':
        return number[1:]
    return number

@app.route('/')
def landing_page():
    return render_template("index.html", donate_address=os.getenv('PAYMENT_ADDRESS'))

def add_ambassador(ambassador_number):
    ambassador_number = format_number(ambassador_number)
    client = datastore.Client.from_service_account_json('gcloud.json')
    key = ambassador_key(client, ambassador_number)
    ambassador = client.get(key)
    
    if ambassador:
        return f'Ambassador {ambassador_number} already exists'
    else:
        ambassador = datastore.Entity(key=key)
        ambassador.update({
            'number': ambassador_number,
            'status': 'created'
        })
        client.put(ambassador)
        logging.info(f'added ambassador {ambassador_number}')
        
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        wallet_url = f'http://www.foothodl.com/{ambassador_number}'
        try:
            message = twilio_client.messages.create(to="+1%s" % ambassador_number, 
        from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body=f"(Ambassador invite) Thank you for volunteering to join FOOTHODL as an ambassador.  To redeem funds, provide a member's phone number in your wallet - {wallet_url}")
        except:
            logging.error('unable to send SMS message')
        return 'Sent ambassador invite to %s' % ambassador_number
    

def add_member(member_number):
    member_number = format_number(member_number)
    client = datastore.Client.from_service_account_json('gcloud.json')
    key = member_key(client, member_number)
    member = client.get(key)
    if member:
        return f'Member {member_number} already exists'
    else:
        member = datastore.Entity(key=key)
        member.update({
            'number': member_number,
            'status': 'created'
        })
        client.put(member)
        logging.info(f'added member {member_number}')
        
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        try:
            message = twilio_client.messages.create(to=f"+1{member_number}", 
        from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body="You have been invited to FOOTHODL. Provide your phone number to a volunteer to get their assistance.")
        except:
            logging.error('unable to send SMS message')
        return f'Sent member invite to {member_number}'
    

@app.route('/register/<ambassador_number>/<member_number>')
def register(ambassador_number, member_number):
    add_ambassador(ambassador_number)
    add_member(member_number)
    return 'OK'
        
@app.route('/request/<ambassador_number>/<member_number>/<amount>')
def request_for_member(ambassador_number, member_number, amount):
        member_number = format_number(member_number)
        ambassador_number = format_number(ambassador_number)
        client = datastore.Client.from_service_account_json('gcloud.json')
        key = member_key(client, member_number)
        member = client.get(key)
        if not member:
            raise Exception(f'member not found for number {member_number}')
        code = generate_confirmation_code()
        logging.info(f'confirmation code for member {member_number} request for {amount}: {code}')
        member.update({
            'confirmation_code': code,
            'requested_amount': amount
        })
        client.put(member)
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        try:
            message = twilio_client.messages.create(to=f"+1{member_number}", 
            from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body=f"Your FOOTHODL confirmation code is: {code}. Share this code with the volunteer assisting you.")
        except:
            logging.error('unable to send SMS message')
        return 'OK'
        
@app.route('/confirm/<ambassador_number>/<member_number>/<confirmation_code>')
def confirm_request(ambassador_number, member_number, confirmation_code):
        ambassador_number = format_number(ambassador_number)
        client = datastore.Client.from_service_account_json('gcloud.json')
        key = member_key(client, member_number)
        member = client.get(key)
        if not member:
            raise Exception(f'member not found for number {member_number}')
        if not member['confirmation_code'] or int(confirmation_code) != member['confirmation_code']:
            raise Exception(f'confirmation code {confirmation_code} does not match saved code')
        logging.info(f'confirmation code {confirmation_code} matches saved code')
        key = ambassador_key(client, ambassador_number)
        ambassador = client.get(key)
        logging.info(f'confirming request for member {member_number}')
        from payment import send_payment 
        send_payment(ambassador['address'], member['requested_amount'])
        member.update({
            'confirmation_code': None,
            'requested_amount': None
        })
        client.put(member)
        return 'OK'
        
@app.route('/saveAddress/<ambassador_number>/<ambassador_address>')
def saveAddress(ambassador_number, ambassador_address):
    ambassador_number = format_number(ambassador_number)
    client = datastore.Client.from_service_account_json('gcloud.json')
    key = ambassador_key(client, ambassador_number)
    ambassador = client.get(key)
    if not ambassador:
        raise Exception(f'ambassador {ambassador_number} not found')
    if ambassador.get('address'):
        logging.info(f'ambassador {ambassador_number} already has address saved.')
        return 'Did not save address'
    ambassador['address'] = ambassador_address
    client.put(ambassador)
    return f'Saved address {ambassador_address}'  

    
        
@app.route('/<int:number>')
def wallet(number):
    return render_template("wallet.html", number=number)


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8000, debug=True)
