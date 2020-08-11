# CoViD-19 Bot Server
This repo contains the source code and data for the `CoViD-19 Bot` backend.  
This includes the chatbot Dialogflow WebHook, data retrieving/processing scripts and daily data.

- The public chatbot can be found here: [CoViD19 Bot - AI4Bharat](https://covid19.ai4bharat.org/chatbot.html)

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

## Steps to restore Dialogflow backup

1. The chatbot data (intents, entities) can be found here: [Dialogflow-Data.zip](https://github.com/OneFourthLabs/CoViD19-Bot-Server/releases).
2. Go to [Dialogflow](https://dialogflow.cloud.google.com/#/editAgent/) -> Project Settings (Gear Icon)
3. `Export and Import` Tab -> Choose an appropriate option and upload the zip.
