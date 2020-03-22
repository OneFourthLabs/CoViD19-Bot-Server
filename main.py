from flask import Flask, request, make_response, jsonify
import pandas as pd
import random
import datetime
import json
import numpy as np

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
max_date = stats_data['Date'].max()

failure_messages = ["Sorry I could not understand you", "I am sorry, I did not follow", "Can you please rephrase that"]

stats_error_messages = ["I could not find the numbers for that query"]

@app.route('/') 
def index():
  return 'Hello World!'

def read_date(date):
  return datetime.datetime.strptime(date[0:10], '%Y-%m-%d')

def write_date(date):
  return date.strftime("%B %d")

def get_stats_cases(intent, entities):

  warning_txt = ''

  country = entities['geo-country'] if len(entities['geo-country']) > 0 else 'World'
  state = entities['geo-state'] if len(entities['geo-state']) > 0 else 'Total'
  case_type = entities['case_types'] if len(entities['case_types']) > 0 else 'Confirmed'
  yesterday = datetime.datetime.today() - datetime.timedelta(days=1)

  date = entities['date-time']
  if type(date) == str:
    if len(date) == 0: # if no date is specified assume that the total is being asked
      start_date = read_date('2020-01-20')
      end_date = min(max_date, yesterday)
    else:
      if max_date < read_date(date):
        warning_txt = 'I have date only till ' + write_date(max_date) + '. '
        start_date = end_date = max_date
      else:
        start_date = end_date = read_date(date)
  elif type(date) == dict:
    start_date = min(max_date, read_date(date['startDate']))
    if max_date < read_date(date['endDate']):
      warning_txt = 'I have date only till ' + write_date(max_date) + '. '
      end_date = max_date
    else:
      end_date = read_date(date['endDate'])

  # find case type
  if case_type == 'deaths':
    case_type = 'Deaths'
    str_case_type = 'deaths'
  elif case_type == 'recovered':
    case_type = 'Recovered'
    str_case_type = 'patients who were reported to be recovered'
  else:
    case_type = 'Confirmed'
    str_case_type = 'total cases recorded'

  # do the filtering
  if not state == 'Total':
    stats_data_sel = stats_data[(stats_data['State'] == state) & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    if not stats_data_sel.empty:
      str_location = state + ', ' + stats_data_sel.iloc[0]['Country']
  else:
    stats_data_sel = stats_data[(stats_data['Country'] == country) & (stats_data['State'] == state) & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    str_location = ' the world' if country == 'World' else country

  if stats_data_sel.empty:
    response = {
      "Response_Type": "Error:StatsNotFound",
      "Answer": random.choice(stats_error_messages)
    }
    return response

  if start_date == end_date:
    date_str = ' on ' + write_date(start_date)
  else:
    if start_date == read_date('2020-01-20'):
      date_str = ' until ' + write_date(end_date)
    else:
      date_str = ' between ' + write_date(start_date) + ' and ' + write_date(end_date)

  ret_val = format(int(max(0, stats_data_sel[case_type].sum())), ',d')
  # date = date.strftime("%B %d")
  response = {
      "Response_Type": "Text:StatsWorked",
      "Answer": warning_txt + 'In ' + str_location + ', there were ' + ret_val + ' ' + str_case_type + date_str
  }
  return response



####
def get_stats_where(intent, entities):

  # parse values
  country = entities['geo-country'] if len(entities['geo-country']) > 0 else 'World'
  case_type = entities['case_types'] if len(entities['case_types']) > 0 else 'Confirmed'
  #location type can be state or country
  location_type = entities['location_type'] if len(entities['location_type']) > 0 else 'state' if country != 'World' else 'country'
  # sel_criterion can be highest or lowest
  sel_criterion = entities['sel_criterion'] if len(entities['sel_criterion']) > 0 else 'highest'
  yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
  date = entities['date-time']
  if type(date) == str:
    if len(date) == 0: # if no date is specified assume that the total is being asked
      start_date = read_date('2020-01-20')
      end_date = min(max_date, yesterday)
    else:
      if max_date < read_date(date):
        warning_txt = 'I have date only till ' + write_date(max_date) + '. '
        start_date = end_date = max_date
      else:
        start_date = end_date = read_date(date)
  elif type(date) == dict:
    start_date = min(max_date, read_date(date['startDate']))
    if max_date < read_date(date['endDate']):
      warning_txt = 'I have date only till ' + write_date(max_date) + '. '
      end_date = max_date
    else:
      end_date = read_date(date['endDate'])
  # find case type
  if case_type == 'deaths':
    case_type = 'Deaths'
    str_case_type = 'number of deaths'
  elif case_type == 'recovered':
    case_type = 'Recovered'
    str_case_type = 'number of recovered patients'
  else:
    case_type = 'Confirmed'
    str_case_type = 'number of total cases recorded'

  if start_date == end_date:
    date_str = ' on ' + write_date(start_date)
  else:
    if start_date == read_date('2020-01-20'):
      date_str = ' until ' + write_date(end_date)
    else:
      date_str = ' between ' + write_date(start_date) + ' and ' + write_date(end_date)

  # check if query is possible
  if location_type == 'state':
    if country == 'World':
      # this does not make sense
      response = {
        "Response_Type": "Error:SelCriterionStateButNoCountrySpecified",
        "Answer": "I am unable to find the country you have mentioned."
      }
      return response
    if stats_data[(stats_data['Country'] == country) & (stats_data['State'] != 'Total')].empty:
      # we do not have state wise data for this country
      response = {
        "Response_Type": "Error:SelCriterionStateButNoCountrySpecified",
        "Answer": "I do not have state-wise data for " + country
      }
      return response
    stats_data_sel = stats_data[(stats_data['Country'] == country) & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    if stats_data_sel.empty:
      # we do not have state wise data for this country
      response = {
        "Response_Type": "Error:SelCriterionStateButNoCountrySpecified",
        "Answer": "I could not find any data in the range of dates you queried for."
      }
      return response
    stats_data_sel = stats_data_sel[['State', 'Date', case_type]]
    stats_data_sel = stats_data_sel.groupby('State').sum()

    stats_data_sel.drop(['Total'], inplace=True)
    if sel_criterion == 'highest':
      response_state = (stats_data_sel[[case_type]].idxmax())[case_type]
    else:
      response_state = (stats_data_sel[[case_type]].idxmin())[case_type]
    response_value = stats_data_sel.at[response_state, case_type]

    response = {
      "Response_Type": "Text:StatsWhereWorked",
      "Answer": response_state + " had the " + sel_criterion + " " + str_case_type + " in " + country + " with a figure of " + format(int(response_value), ',d') + date_str
    }
    return response

  # check if query is possible
  if location_type == 'country':
    stats_data_sel = stats_data[(stats_data['State'] == 'Total') & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    if stats_data_sel.empty:
      # we do not have state wise data for this country
      response = {
        "Response_Type": "Error:SelCriterionStateButNoCountrySpecified",
        "Answer": "I could not find any data in the range of dates you queried for."
      }
      return response
    stats_data_sel = stats_data_sel[['Country', 'Date', case_type]]
    stats_data_sel = stats_data_sel.groupby('Country').sum()

    stats_data_sel.drop(['World'], inplace=True)
    if sel_criterion == 'highest':
      response_country = (stats_data_sel[[case_type]].idxmax())[case_type]
    else:
      response_country = (stats_data_sel[[case_type]].idxmin())[case_type]
    response_value = stats_data_sel.at[response_country, case_type]

    response = {
      "Response_Type": "Text:StatsWhereWorked",
      "Answer": response_country + " had the " + sel_criterion + " " + str_case_type + " with a figure of " + format(int(response_value), ',d') + date_str
    }
    return response



def get_stats_plot(intent, entities):
  # parse values
  country = entities['geo-country'] if len(entities['geo-country']) > 0 else 'World'
  state = entities['geo-state'] if len(entities['geo-state']) > 0 else 'Total'
  case_type = entities['case_types'] if len(entities['case_types']) > 0 else 'Confirmed'
  chart_type = entities['plot_type'] if len(entities['plot_type']) > 0 else 'barplot'
  aggregation_type = entities['aggregation_type'] if len(entities['aggregation_type']) > 0 else 'total'
  
  yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
  date = entities['date-period']
  if len(date) == 0:
    start_date = datetime.datetime.today() - datetime.timedelta(days=7)
    end_date = datetime.datetime.today() - datetime.timedelta(days=1)
  else:
    start_date = read_date(date['startDate'][0:10])
    end_date = read_date(date['endDate'][0:10])
  end_date = min(end_date, max_date)
  # find case type
  if case_type == 'deaths':
    case_type = 'Deaths'
  elif case_type == 'recovered':
    case_type = 'Recovered'
  else:
    case_type = 'Confirmed'

  if state != 'Total':
    # we are doing selection by state
    stats_data_sel = stats_data[(stats_data['State'] == state) & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    loc_str = state
    if stats_data_sel.empty:
      response = {
        "Response_Type": "Error:PlotDataMissingStateInfo",
        "Answer": "I do not have the stats for " + state
      }
      return response
  else:
    # we are doing selection by country
    stats_data_sel = stats_data[(stats_data['Country'] == country) & (stats_data['State'] == 'Total') & (stats_data['Date'] >= start_date) & (stats_data['Date'] <= end_date)]
    loc_str = country
    if stats_data_sel.empty:
      response = {
        "Response_Type": "Error:PlotDataMissingStateInfo",
        "Answer": "I do not have the stats for " + state
      }
      return response


  labels = stats_data_sel['Date'].apply(write_date).tolist()
  values = stats_data_sel[case_type].apply(int).tolist()

  if aggregation_type != 'daily':
    for i in range(1, len(values)):
      values[i] = values[i - 1] + values[i]

  chart_payload = {}
  chart_payload['type'] = 'line' if chart_type == 'lineplot' else 'bar'
  chart_payload['data'] = {}
  chart_payload['data']['labels'] = labels
  chart_payload['data']['datasets'] = []
  chart_payload['data']['datasets'].append({})
  chart_payload['data']['datasets'][0]['label'] = case_type + " - " + loc_str
  chart_payload['data']['datasets'][0]['data'] = values

  response = {
    "Response_Type": "Plot:Worked",
    "URL": "https://quickchart.io/chart?c=" + json.dumps(chart_payload) + "&backgroundColor=white"
  }
  return response


def get_stats(intent, entities):

  if intent == "stats-case_types-in-location-date":
    return get_stats_cases(intent, entities)
  elif intent == "stats-where-sel_criterion-case_types-when":
    return get_stats_where(intent, entities)
  elif intent == "stats-plot":
    return get_stats_plot(intent, entities)


####
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

  if "Error" in result["Response_Type"] or "Text" in result["Response_Type"]:
    reply = {}
    reply['fulfillment_text'] = result["Answer"]
    return reply

  if "Plot:" in result["Response_Type"]:
    imageURL = result["URL"]
    reply = {}
    reply = {
      "fulfillmentText": "",
      "fulfillmentMessages": [
        {
        }
      ],
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
                "title": "",
                "formattedText": "",
                "image": 
                {
                  "url": imageURL,
                },
                "buttons": [
                  {
                    "title": "See large image",
                    "openUrlAction": 
                    {
                        "url": imageURL
                    }
                  }, 
                ]
              },
            }
            ],
          }
        }
      }
    }

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
