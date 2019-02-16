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

from flask import Flask
import requests
import os

from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client as TwilioClient
from google.cloud import datastore
app = Flask(__name__)


@app.route('/')
def say_hello():
    return 'Hello World!'
    

def ambassador_key(client, number):
    # [START datastore_named_key]
    key = client.key('FoothodlAmbassador', number)
    # [END datastore_named_key]
    return key
    
def member_key(client, number):
    # [START datastore_named_key]
    key = client.key('FoothodlMember', number)
    # [END datastore_named_key]
    return key
    
def generate_confirmation_code():
    import random
    return random.randInt(100, 999)
                
@app.route('/ambassadors/add/<ambassador_number>')
def add_ambassador(ambassador_number):
    client = datastore.Client.from_service_account_json('gcloud.json')
    key = ambassador_key(client, ambassador_number)
    ambassador = client.get(key)
    
    if ambassador:
        return f'Ambassador {ambassador_number} already exists'
    else:
        address = f'0x{ambassador_number}' # TODO: implement address generation 
        ambassador = datastore.Entity(key=key)
        ambassador.update({
            'number': ambassador_number,
            'address': address,
            'status': 'created'
        })
        client.put(ambassador)
        
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        wallet_url = 'http://www.foothodl.com'
        message = twilio_client.messages.create(to="+1%s" % ambassador_number, 
        from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body=f"You have been invited to FOOTHODL as an ambassador.  To redeem funds, provide a member's phone number in your wallet - {wallet_url}")
        return 'Sent ambassador invite to %s' % ambassador_number
    

@app.route('/members/add/<member_number>')
def add_member(member_number):
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
        
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        message = twilio_client.messages.create(to=f"+1{member_number}", 
        from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body="You have been invited to FOOTHODL.")
        return f'Sent member invite to {member_number}'
        
        
@app.route('/request/<ambassador_address>/<member_number>/<amount>')
def request_for_member(ambassador_address, member_number, amount):
        key = member_key(client, member_number)
        member = client.get(key)
        if not member:
            raise Exception(f'member not found for number {member_number}')
        member_number = member.number
        code = generate_confirmation_code()
        member.confirmation_code = code 
        member.requested_amount = amount
        client.put(member)
        twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        message = twilio_client.messages.create(to=f"+1{member_number}", 
        from_="+%s" % os.getenv('TWILIO_NUMBER'), 
            body=f"Your FOOTHODL confirmation code for {amount} is: {code}")
        return 'OK'
        
@app.route('/request/<ambassador_address>/<member_number>/<confirmation_code>')
def confirm_request(ambassador_address, member_number, confirmation_code):
        key = member_key(client, member_number)
        member = client.get(key)
        if not member:
            raise Exception(f'member not found for number {member_number}')
        if not member.confirmation_code or confirmation_code != member.confirmation_code:
            raise Exception(f'confirmation code {confirmation_code} does not match saved code')
        # TODO - send requested amount to ambassador address
        member.requested_amount = None 
        member.confirmation_code = None 
        client.put(member)
        return 'OK'
        



if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8000, debug=True)
