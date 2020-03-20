

GCP Steps:  
1. `git clone repo` and `cd repo`
2. Set service name in `app.yaml`
3. `virtualenv --python python3  ~/envs/covid19_webhook`
4. `source ~/envs/covid19_webhook/bin/activate`
5. `pip install -r requirements.txt`
6. Optional: `python main.py`
7. Optional: `gcloud app create`
8. `gcloud app deploy app.yaml`
9. Go to the URL indicated
