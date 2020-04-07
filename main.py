from flask import Flask, request, make_response, jsonify
from flask_cors import CORS, cross_origin
import sys, os
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import dialogflow
from google.api_core.exceptions import InvalidArgument
from google.protobuf.json_format import MessageToDict

from df_payload import get_card_payload, get_plot_payload
from utils import *
from constants import *
from covid_qa import CoViD_QnA
from covid_stats import CoViD_Stats

DEBUG_MODE = True
DIALOGFLOW_PROJECT_ID = 'PROJECT_ID_HERE'
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/user/Downloads/sa.json"

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

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

        # + " Entities: " + ",".join(entities)+" Intent: " + intent
        response = textAnswer

        reply = get_card_payload(textTitle, response, imageURL,
                                 sourceURL, sourceURLTitle, referenceURL, suggestions)

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
    scheduler.add_job(func=covid_stats_handler.update_stats_csv,
                      trigger="interval", hours=3)
    scheduler.start()
    #atexit.register(lambda: scheduler.shutdown())
    return


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    return make_response(jsonify(results()))


@app.route('/')
def index():
    return 'The server is running... Yaayy!!!'


@app.route('/get_dialogflow_account_details', methods=['GET'])
def get_dialogflow_account_details():
    client = dialogflow.AgentsClient()
    parent = client.project_path(DIALOGFLOW_PROJECT_ID)
    details = client.get_agent(parent)
    return make_response(jsonify(MessageToDict(details)))


@app.route('/get_response_for_query', methods=['POST'])
def get_response_for_query():
    input_ = request.json
    session_id = input_["session"]
    text_data = input_["queryInput"]["text"]["text"]
    language_code = input_["queryInput"]["text"]["languageCode"]

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(
        DIALOGFLOW_PROJECT_ID, session_id)
    text_input = dialogflow.types.TextInput(
        text=text_data, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(
            session=session, query_input=query_input)
    except InvalidArgument:
        raise

    return make_response(jsonify(MessageToDict(response)))


if __name__ == '__main__':
    # Run Flask server
    app.run(port=8000, debug=DEBUG_MODE, use_reloader=not DEBUG_MODE)
