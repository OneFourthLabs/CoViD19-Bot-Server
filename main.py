from flask import Flask, request, make_response, jsonify
import pandas as pd
import random
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

@app.route('/') 
def index():
  return 'Hello World!'

# def find_intent_entity_match(intent, entities):
#     data = corona_data[corona_data["Intent"] == intent]
#     print(intent, entities);
#     data["intent_match_count"] = data["Entities"].apply(
#         lambda x: len(set(x) & set(entities)))
#     answer = data.loc[data['intent_match_count'].idxmax()]
#     return answer

failure_messages = ["Sorry I could not understand you", "I am sorry, I did not follow", "Can you please rephrase that"]

def find_answer(intent, entities):

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

  entities = entity_stringify(params)
  result = find_answer(intent, entities)

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
    reply["payload"] = {
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
