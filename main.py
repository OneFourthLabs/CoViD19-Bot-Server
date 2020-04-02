from flask import Flask, request, make_response, jsonify
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from df_payload import get_card_payload, get_plot_payload
from utils import *
from constants import *
from covid_qa import CoViD_QnA
from covid_stats import CoViD_Stats

app = Flask(__name__)
DEBUG_MODE = True

covid_qa_handler = CoViD_QnA()
covid_stats_handler = CoViD_Stats()

def find_answer(intent, entities, context, question=''):

  if intent.startswith('stats'):
    return covid_stats_handler.get_stats_response(intent, entities, context)

  return covid_qa_handler.get_response(intent, entities, context, question)

def results():

  req = request.get_json(force=True)
  context_id, context = get_context_from_request(req, 'global_context')

  # find intent
  intent = req["queryResult"]["intent"]["displayName"]
  # find entities
  params = req["queryResult"]["parameters"]
  # find the question that user asked
  question = req["queryResult"]["queryText"]

  result = find_answer(intent, params, context, question)
  reply = {}

  if "Error" in result["Response_Type"] or "Text" in result["Response_Type"]:
    reply['fulfillment_text'] = result["Answer"]

  elif "Plot:" in result["Response_Type"]:
    imageURL = result["URL"]
    reply = get_plot_payload(imageURL)

  elif result["Response_Type"] == "Card":
    textTitle = result["Answer_Title"] if result["Answer_Title"] else ""
    textAnswer = result["Answer"] if result["Answer"] else ""
    imageURL = result["Image_URL"] if len(result["Image_URL"]) > 0 else ""
    sourceURL = result["Source"] if result["Source"] else ""
    sourceURLTitle = result["SourceTitle"] if "SourceTitle" in result and result["SourceTitle"] else "Source"
    referenceURL = result["Reference"] if "Reference" in result else ""
    suggestions = []
    if "Suggestions" in result:
      suggestions = [{"title": item} for item in result["Suggestions"]]

    response = textAnswer # + " Entities: " + ",".join(entities)+" Intent: " + intent

    reply = get_card_payload(textTitle, response, imageURL, sourceURL, sourceURLTitle, referenceURL, suggestions)
    
  reply["outputContexts"] = [
        {
          "name": context_id,
          "lifespanCount": 5,
          "parameters": get_updated_context(params, context)
        }
      ]
  return reply

# Cron job function to update data regularly
scheduler = BackgroundScheduler()

@app.before_first_request
def init_server():
  print("Running Flask.before_first_request ...", file=sys.stderr)
  # Run job to periodically collect stats
  scheduler.add_job(func=covid_stats_handler.update_stats_csv, trigger="interval", hours=3)
  scheduler.start()
  #atexit.register(lambda: scheduler.shutdown())
  return

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  return make_response(jsonify(results()))

@app.route('/')
def index():
  return 'The server is running... Yaayy!!!'

if __name__ == '__main__':
  # Run Flask server
  app.run(port=8000, debug=DEBUG_MODE, use_reloader=not DEBUG_MODE)
