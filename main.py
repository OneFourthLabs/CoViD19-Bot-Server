from flask import Flask, request, make_response, jsonify
import pandas as pd
import random
import datetime
import json
import numpy as np
import os, sys
import atexit
from df_payload import get_card_payload, get_plot_payload
from utils import read_date, write_date, unlist, dict_stringify
from apscheduler.schedulers.background import BackgroundScheduler
from get_data import update_stats_csv_job

app = Flask(__name__)
DEBUG_MODE = True

CORONA_JSON = 'coronabot_qa_data.json'
corona_data = pd.read_json(CORONA_JSON)
corona_data['EntitiesStr'] = corona_data['Entities'].apply(dict_stringify)

STATS_CSV = 'coronabot_stats_data.csv'
stats_data = pd.read_csv(STATS_CSV)
stats_data['Date'] = stats_data['Date'].apply(lambda x: x[0:10])
stats_data['Date'] = pd.to_datetime(stats_data['Date'], infer_datetime_format=True)  
max_date = stats_data['Date'].max()

failure_messages = ["Sorry I could not understand you", "I am sorry, I did not follow", "Can you please rephrase that"]

stats_error_messages = ["I could not find the numbers for that query"]
INDIA_PLOT_URLS = {
  'patients': 'https://ai4bharat.org/covid19-indian-patients-tracking',
  'map': 'https://ai4bharat.org/covid19-map',
  'state_wise': 'https://ai4bharat.org/covid19-table'
}

entities_index = {'country': 'geo-country', 'state': 'geo-state', 'case_type': 'case_types', 'location_type': 'location_type', 'chart_type': 'plot_type', 'aggregation_type': 'aggregation_type', 'date': 'date-time'}
default_values = {'country': 'World', 'state': 'Total', 'case_type': 'Confirmed', 'location_type': 'country', 'chart_type': 'barplot', 'aggregation_type': 'total', 'date': ''}
context_index = {'country': 'ctx_geo-country', 'state': 'ctx_geo-state', 'case_type': 'ctx_case_types', 'location_type': 'ctx_location_type', 'chart_type': 'ctx_plot_type', 'aggregation_type': 'ctx_aggregation_type', 'date': 'ctx_date-time'}

def clear_from_context(context, fields):
  for field in fields:
    if context_index[field] in context:
      context[context_index[field]] = ''
  return context

def read_entry(entities, context, field):
  entry = None
  if entities_index[field] in entities and len(entities[entities_index[field]]) > 0:
    entry = entities[entities_index[field]]
  elif context_index[field] in context  and len(context[context_index[field]]) > 0:
    entry = context[context_index[field]]
  else:
    entry = default_values[field]
  return unlist(entry)

def read_entry_arr(entities, context, fields):
  return [read_entry(entities, context, x) for x in fields]

def read_stats_entries(entities, context, fields):

  if entities[entities_index['country']]: # If country is specified in current question...
    if context_index['state'] in context and context[context_index['state']]: # If state is there in context
      context[context_index['state']] = default_values['state'] # Reset state in context
      ## TODO: Better check if state and country correspond or not
  
  return read_entry_arr(entities, context, fields)

def get_stats_cases(intent, entities, context):

  warning_txt = ''

  country, state, case_type, date = read_stats_entries(entities, context, ['country', 'state', 'case_type', 'date'])

  yesterday = datetime.datetime.today() - datetime.timedelta(days=1)

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
def get_stats_where(intent, entities, context):

  # parse values

  country, state, case_type = read_stats_entries(entities, context, ['country', 'state', 'case_type'])
  
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

def get_stats_plot(intent, entities, context):
  # parse values

  country, state, case_type, chart_type, aggregation_type = read_stats_entries(entities, context, ['country', 'state', 'case_type', 'chart_type', 'aggregation_type'])
  
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
  chart_payload['data']['datasets'][0]['backgroundColor'] = 'pink'
  chart_payload['data']['datasets'][0]['borderColor'] = 'red'
  if chart_type == 'lineplot':
    chart_payload['data']['datasets'][0]['fill'] = 'boundary'
  elif chart_type == 'barplot':
    chart_payload['data']['datasets'][0]['borderWidth'] = 1
  response = {
    "Response_Type": "Plot:Worked",
    "URL": "https://quickchart.io/chart?c=" + json.dumps(chart_payload) + "&backgroundColor=white"
  }
  return response

def get_map(intent, entities, context):
  # Hack: Sometimes context seems to mess with our flow; remove the culprit ones
  clear_from_context(context, ['location_type', 'case_type'])
  
  country, state, case_type, location_type = read_stats_entries(entities, context, ['country', 'state', 'case_type', 'location_type'])
  result = { # Default Response
    'Answer': 'I am unable to retrieve the details for the given query',
    'Response_Type': 'Error:OnlyIndiaSupported'
    }
  
  if country == 'India' or country == default_values['country']:
    result = {
      'Answer_Title': 'Cases in India',
      'Answer': 'Please click on the below link to view the interactive map',
      'Response_Type': 'Card',
      'SourceTitle': 'Click here',
      'Image_URL': 'https://i.pinimg.com/originals/41/55/52/415552d055f73f03ff308cb2a527f2d7.jpg'
    }
    
    if case_type == 'total':
      result['Answer_Title'] = 'Track Indian patients by location'
      result['Source'] = INDIA_PLOT_URLS['patients']
    elif location_type == 'state':
      result['Answer_Title'] = 'State-wise Information for India'
      result['Source'] = INDIA_PLOT_URLS['state_wise']
    else:
      result['Answer_Title'] = 'State-wise Spread in India'
      result['Source'] = INDIA_PLOT_URLS['map']
  
  return result

def get_stats(intent, entities, context):

  if intent.startswith("stats-case_types-in-location-date"):
    return get_stats_cases(intent, entities, context)
  elif intent.startswith("stats-where-sel_criterion-case_types-when"):
    return get_stats_where(intent, entities, context)
  elif intent.startswith("stats-plot"):
    return get_stats_plot(intent, entities, context)
  elif intent.startswith("stats-show-map"):
    return get_map(intent, entities, context)

####
def find_answer(intent, entities, context):

  if intent[0:5] == 'stats':
    return get_stats(intent, entities, context)

  entities = dict_stringify(entities)

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

def get_updated_context(params, context):

  # TODO: Construct a list of history instead of replacing with new? Set expiry?
  for param in params:
    if params[param]:
      context['ctx_' + param] = params[param]

  return context


def results():

  req = request.get_json(force=True)

  context_id = req["session"] + "/contexts/global_context"
  # print(' ---------- ', context_id)

  context = {}
  for item in req["queryResult"]["outputContexts"]:
    if item['name'] == context_id:
      context = item["parameters"]

  # find intent
  intent = req["queryResult"]["intent"]["displayName"]
  # find entities
  params = req["queryResult"]["parameters"]

  # print('---->>>>')
  # print(intent)
  # print(params)

  # print(context)
  # print(req["queryResult"]["outputContexts"])

  result = find_answer(intent, params, context)
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

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
  return make_response(jsonify(results()))

# Example: https://webhook-dot-covid-bot.appspot.com/test/what-is/COVID-19,OK
@app.route('/test/<path:query>', methods=['GET', 'POST'])
def test(query):
  intent, entities = query.split('/')
  entities = entities.split(',')
  response = find_answer(intent, entities, {}).to_json(indent=4)
  return make_response(response)

@app.route('/') 
def index():
  return 'The server is running... Yaayy!!!'

if __name__ == '__main__':
  
  # Run job to periodically collect stats
  scheduler = BackgroundScheduler()
  scheduler.add_job(func=update_stats_csv_job, trigger="interval", hours=1)
  scheduler.start()
  atexit.register(lambda: scheduler.shutdown())

  # Run Flask server
  app.run(port=8000, debug=DEBUG_MODE, use_reloader=not DEBUG_MODE)