

### Hosting on GCP:  
1. `git clone repo` and `cd repo`
2. Set service name in `app.yaml`
3. `virtualenv --python python3  ~/envs/covid19_webhook`
4. `source ~/envs/covid19_webhook/bin/activate`
5. `pip install -r requirements.txt`
6. Optional: `python main.py`
7. Optional: `gcloud app create`
8. `gcloud app deploy app.yaml`
9. Go to the URL indicated

### Host locally:

1. To host local server - `ngrok http 8000`
2. `python main.py`
3. Use `{HTTPS_URL_FROM_GROK}/webhook` as diaglogflow webhook URL

### JSON Data Updation

1. Export the [data sheet](https://docs.google.com/spreadsheets/d/1Em3NLwATeXTQOmVzbt7O4l4ZzdohrKWhZI9rtgEWlVY) as CSV
2. Convert CSV to our JSON using [this notebook](https://colab.research.google.com/drive/1vzXlzXLgjg7VpiKAbme5VrFKQlXlcF89)
3. Put the JSON in this repo root directory with proper name.
