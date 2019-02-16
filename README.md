# FOOTHODL

This project aims to provide a financial foothold to people in need, with the assistance of a network of volunteer ambassadors.

The xDai Ethereum sidechain is used for fast transactions, and a modified version of Austin Griffith's [burner wallet](https://github.com/austintgriffith/burner-wallet) is used for redeeming donated funds. 

## Local Server Development

Use [virtualenv](https://virtualenv.pypa.io/en/stable/) to set up each
service's environment and start the each service in a separate terminal.

Open a terminal and start the first service:

```Bash
$ cd foothodl-server
$ virtualenv -p python3 env
$ source env/bin/activate
$ pip3 install -r requirements.txt
$ python3 main.py
```

The server should now be running at `http://localhost:8000`. 

## Setting up GCloud Service Account 

Follow the instructions at `https://cloud.google.com/docs/authentication/` and create file `gcloud.json` in the `foothodl-server` directory containing credentials JSON.

## Setting up Twilio

Copy `.env.example` to `.env` and modify the values to Twilio credentials. The `python-dotenv` library will load these values into the Flask application.

## Deployment

These instructions are specific to Google Cloud. 

Make sure you have an App Engine project setup first, and have `gcloud` configured on your machine for that project.

Run the following command to deploy:

```Bash
$ gcloud app deploy app.yaml
```

Enter `Y` when prompted.  Or to skip the check add `-q`.

The deployed url will be `https://foothodl.<your project id>.appspot.com`

