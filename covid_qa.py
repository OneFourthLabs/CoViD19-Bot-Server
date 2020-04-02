import pandas as pd
import random

from utils import dict_stringify
from constants import CORONA_QA_JSON, failure_messages

class CoViD_QnA:
  def __init__(self, input_file=CORONA_QA_JSON):
    self.corona_json = input_file
    self.corona_data = pd.read_json(input_file)
    self.corona_data['EntitiesStr'] = self.corona_data['Entities'].apply(dict_stringify)

  def get_response(self, intent, entities, context, question):
    entities = dict_stringify(entities)

    data_match_intent = self.corona_data[self.corona_data["Intent"] == intent]

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
