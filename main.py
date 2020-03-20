from flask import Flask, request, make_response, jsonify
import pandas as pd 
import json

app = Flask(__name__)

@app.route('/')
def index():    
  return 'Hello World!'

def find_intent_entity_match(intent,entities):
    data=pd.read_json("CoViD_19Mar20.json")
    data = data[data["Intent"] == intent]
    data["intent_match_count"] = data["Entities"].apply(lambda x: len(set(x) & set(entities)))
    answer=data.loc[data['intent_match_count'].idxmax()]
    return answer
    
def results():
  req = request.get_json(force=True)
  params = req["queryResult"]["parameters"]
  entities = {k: v for k, v in params.items() if v is not ""}
  intent = req["queryResult"]["intent"]["displayName"]
  
  result=find_intent_entity_match(intent,entities.keys())
  textAnswer=result["Answer"]
  imageURL = result["Image_URL"]
  response = textAnswer+" Entities: "+",".join(entities)+" Intent: "+intent
  return {'fulfillmentText': response, 'image':imageURL}


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  return make_response(jsonify(results()))


if __name__ == '__main__':
  app.run(port=8000,debug=True)

