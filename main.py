from flask import Flask, request, make_response, jsonify
import pandas as pd
import json

app = Flask(__name__)

covid_data = pd.read_json("CoViD_20Mar20.json")

@app.route('/')
def index():
    return 'Hello World!'


def find_intent_entity_match(intent, entities):
    data = covid_data[covid_data["Intent"] == intent]
    data["intent_match_count"] = data["Entities"].apply(
        lambda x: len(set(x) & set(entities)))
    answer = data.loc[data['intent_match_count'].idxmax()]
    return answer

def results():
    req = request.get_json(force=True)
    params = req["queryResult"]["parameters"]
    entities = {k: v for k, v in params.items() if v is not ""}
    intent = req["queryResult"]["intent"]["displayName"]

    result = find_intent_entity_match(intent, entities.keys())
    textAnswer = result["Answer"] if result["Answer"] else ""
    textAnswer = textAnswer.replace("\r\n", "\n")
    print("textAnswer", textAnswer)
    imageURL = result["Image_URL"]
    referenceURL = result["Reference"]
    response = textAnswer+" Entities: " + \
        ",".join(entities.keys())+" Intent: "+intent
    reply = {}
    reply["payload"] = {
        "google": {
            "expectUserResponse": True,
            "richResponse": {
                "items": [
                  {
                      "basicCard": {
                          "title": "",
                          "formattedText": response,
                          "image": {
                              "url": imageURL,
                          },
                          "buttons": [
                              {
                                  "title": "See More",
                                  "openUrlAction": {
                                      "url": referenceURL
                                  }
                              }
                          ],
                          "imageDisplayOptions": "CROPPED"
                      },
                      "suggestions": [
                          {
                          }
                      ],
                  }
                ],
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
