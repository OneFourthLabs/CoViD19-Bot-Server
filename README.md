# CoViD-19 Bot Server
This repo contains the source code and data for the `CoViD-19 Bot` backend.  
This includes the chatbot WebHook, data retrieving/processing scripts and daily data.

The public chatbot can be found here: https://covid19.ai4bharat.org/

## Hosting on GCP  

#### Optional: Setting up `virtualenv`
1. `virtualenv --python python3  ~/envs/covid19_webhook`
2. `source ~/envs/covid19_webhook/bin/activate`

#### One time setup
1. `git clone repo` and `cd repo`
2. Set service name in `app.yaml`
3. `pip install -r requirements.txt`
4. Optional: `python main.py` (To check if working)
5. Optional: `gcloud app create` (Only do this unless there's no `default` service)

#### Steps to Run
1. `gcloud app deploy app.yaml`
2. Use the URL indicated for Dialogflow WebHook as `{URL}/webhook`

## Hosting Locally
0. To install libraries: `pip install -r requirements.txt`
1. To expose local server: `ngrok http 8000`
2. To run this WebHook server: `python main.py`
3. Use `{HTTPS_URL_FROM_GROK}/webhook` as Dialogflow webhook URL

## JSON Data Updation

1. Export the [data sheet](https://docs.google.com/spreadsheets/d/1Em3NLwATeXTQOmVzbt7O4l4ZzdohrKWhZI9rtgEWlVY) as CSV
2. Convert CSV to our JSON using [this notebook](https://colab.research.google.com/drive/1vzXlzXLgjg7VpiKAbme5VrFKQlXlcF89)
3. Put the JSON in this repo root directory with proper name.
