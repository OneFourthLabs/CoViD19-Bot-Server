from flask import Flask, request, make_response, jsonify
import pandas as pd
import random
import datetime
import json

app = Flask(__name__)


def entity_stringify(entities):
  str_ = ""
  for key in sorted(entities.keys()) :
    if len(entities[key]) > 0:
      str_ += key + ":["
      if type(entities[key] == str):
        str_ += entities[key]
      elif type(entities[key] == list):
        str_ += ','.join(entities[key])
      str_ += "],"
  return str_

CORONA_JSON = 'coronabot_qa_data.json'
corona_data = pd.read_json(CORONA_JSON)
corona_data['EntitiesStr'] = corona_data['Entities'].apply(entity_stringify)

STATS_CSV = 'coronabot_stats_data.csv'
stats_data = pd.read_csv(STATS_CSV)
stats_data['Date'] = stats_data['Date'].apply(lambda x: x[0:10])
stats_data['Date'] = pd.to_datetime(stats_data['Date'], infer_datetime_format=True)  

failure_messages = ["Sorry I could not understand you", "I am sorry, I did not follow", "Can you please rephrase that"]

stats_error_messages = ["I could not find the numbers for that query"]

@app.route('/') 
def index():
  return 'Hello World!'

def get_stats(intent, entities):

  country = entities['geo-country'] if len(entities['geo-country']) > 0 else 'World'
  state = entities['geo-state'] if len(entities['geo-state']) > 0 else 'Total'
  case_type = entities['case_types'] if len(entities['case_types']) > 0 else 'Confirmed'
  yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
  date = datetime.datetime.strptime(entities['date-time'][0:10], '%Y-%m-%d') if len(entities['date-time']) > 0 else yesterday


  if not state == 'Total':
    stats_data_sel = stats_data[(stats_data['State'] == state) & (stats_data['Date'] == date)]
    str_location = state + ', ' + stats_data_sel.iloc[0]['Country']
  else:
    stats_data_sel = stats_data[(stats_data['Country'] == country) & (stats_data['State'] == state) & (stats_data['Date'] == date)]
    str_location = country

  if stats_data_sel.empty:
    response = {
      "Response_Type": "Error:StatsNotFound",
      "Answer": random.choice(stats_error_messages)
    }
    return response

  if case_type == 'deaths':
    case_type = 'Deaths'
    str_case_type = 'deaths'
  elif case_type == 'recovered':
    case_type = 'Recovered'
    str_case_type = 'patients who were reported to be recovered'
  else:
    case_type = 'Confirmed'
    str_case_type = 'total cases recorded'

  ret_val = max(0, stats_data_sel.iloc[0][case_type])
  date = date.strftime("%B %d")
  response = {
      "Response_Type": "Error:EntitiesNotFound",
      "Answer": 'In ' + str_location + ' there were ' + str(ret_val) + ' ' + str_case_type + ' till ' + date
  }
  print(response["Answer"])
  return response

def find_answer(intent, entities):


  if intent[0:5] == 'stats':
    return get_stats(intent, entities)

  entities = entity_stringify(entities)

  data_match_intent = corona_data[corona_data["Intent"] == intent]

  # intent was not found
  if data_match_intent.empty:
    response = {
      "Response_Type": "Error:IntentNotFound",
      "Answer": random.choice(failure_messages)
    }
    return response

  # intent was found
  data_match = data_match_intent[data_match_intent['EntitiesStr'] == entities]

  if data_match.empty:
    response = {
      "Response_Type": "Error:EntitiesNotFound",
      "Answer": random.choice(failure_messages)
    }
    return response

  return data_match.iloc[0]

def results():

  req = request.get_json(force=True)

  # find intent
  intent = req["queryResult"]["intent"]["displayName"]
  # find entities
  params = req["queryResult"]["parameters"]

  result = find_answer(intent, params)

  if "Error" in result["Response_Type"]:
    reply = {}
    reply['fulfillment_text'] = result["Answer"]
    return reply

  if result["Response_Type"] == "Card":
    textTitle = result["Answer_Title"] if result["Answer_Title"] else ""
    textAnswer = result["Answer"] if result["Answer"] else ""
    imageURL = result["Image_URL"] if len(result["Image_URL"]) > 0 else ""
    sourceURL = result["Source"] if result["Source"] else ""
    referenceURL = result["Reference"]
    suggestions = []
    for item in result["Suggestions"]:
      suggestions.append({"title": item})

    response = textAnswer # + " Entities: " + ",".join(entities)+" Intent: " + intent

    reply = {}
    reply = {
      "fulfillmentText": "",
      "fulfillmentMessages": [
        {
        }
      ],
      "source": "example.com",
      "payload": {
        "google": 
        {
          "expectUserResponse": True,
          "richResponse": 
          {
            "items": [
            {
              "basicCard": 
              {
                "title": textTitle,
                "formattedText": response,
                "image": 
                {
                  "url": imageURL,
                },
                "buttons": [
                {
                  "title": "Source",
                  "openUrlAction": 
                  {
                      "url": sourceURL
                  }
                }, 
                {
                  "title": "Learn more",
                  "openUrlAction": 
                  {
                    "url": referenceURL
                  }
                }
                ],
                "imageDisplayOptions": "CROPPED"
              },
            }
            ],
            "suggestions": suggestions
          }
        }
      }
    }

  return reply

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  return make_response(jsonify(results()))

# Example: https://webhook-dot-covid-bot.appspot.com/test/what-is/COVID-19,OK
@app.route('/test/<path:query>', methods=['GET', 'POST'])
def test(query):
  intent, entities = query.split('/')
  entities = entities.split(',')
  response = find_intent_entity_match(intent, entities).to_json(indent=4)
  return make_response(response)


if __name__ == '__main__':
  app.run(port=8000, debug=True)
