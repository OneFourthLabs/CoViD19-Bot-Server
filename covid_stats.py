import random
import json
import datetime
import sys

from get_data import process_and_get_files
from constants import *
from utils import *

def read_stats_entries(entities, context, fields):
  if entities[entities_index['country']]: # If country is specified in current question...
    if context_index['state'] in context and context[context_index['state']]: # If state is there in context
      context[context_index['state']] = default_values['state'] # Reset state in context
      ## TODO: Better check if state and country correspond or not
  
  return read_entry_arr(entities, context, fields)

class CoViD_Stats:
  def __init__(self):
    _ , _ , self.stats_data, self.max_date = process_and_get_files()

  def update_stats_csv(self):
    print("Starting update_stats_csv", file=sys.stderr)
    (status, message, new_stats_data, new_max_date) = process_and_get_files()
    if not status:
      error_message = "Subject: Problem in CoViD19 Bot data loading\n\n"+message+"\n\nRegards,\nOFL Bot"
      send_email_amazon_ses(email="covid19@onefourthlabs.com", message=error_message)
      print("Error: "+message, file=sys.stderr)
      return False
    else:
      self.stats_data = new_stats_data
      self.max_date = new_max_date
    print("Ending update_stats_csv", file=sys.stderr)
    return True

  def get_stats_cases(self, intent, entities, context):

    warning_txt = ''

    country, state, case_type, date = read_stats_entries(entities, context, ['country', 'state', 'case_type', 'date'])

    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)

    if type(date) == str:
      if len(date) == 0: # if no date is specified assume that the total is being asked
        start_date = read_date('2020-01-20')
        end_date = min(self.max_date, yesterday)
      else:
        if self.max_date < read_date(date):
          warning_txt = 'I have date only till ' + write_date(self.max_date) + '. '
          start_date = end_date = self.max_date
        else:
          start_date = end_date = read_date(date)
    elif type(date) == dict:
      start_date = min(self.max_date, read_date(date['startDate']))
      if self.max_date < read_date(date['endDate']):
        warning_txt = 'I have date only till ' + write_date(self.max_date) + '. '
        end_date = self.max_date
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
    stats_data = self.stats_data
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

  def get_stats_where(self, intent, entities, context):

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
        end_date = min(self.max_date, yesterday)
      else:
        if self.max_date < read_date(date):
          warning_txt = 'I have date only till ' + write_date(self.max_date) + '. '
          start_date = end_date = self.max_date
        else:
          start_date = end_date = read_date(date)
    elif type(date) == dict:
      start_date = min(self.max_date, read_date(date['startDate']))
      if self.max_date < read_date(date['endDate']):
        warning_txt = 'I have date only till ' + write_date(self.max_date) + '. '
        end_date = self.max_date
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

    stats_data = self.stats_data
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

  def get_stats_plot(self, intent, entities, context):
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
    end_date = min(end_date, self.max_date)
    # find case type
    if case_type == 'deaths':
      case_type = 'Deaths'
    elif case_type == 'recovered':
      case_type = 'Recovered'
    else:
      case_type = 'Confirmed'

    stats_data = self.stats_data
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

  def get_map(self, intent, entities, context):
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

  def get_stats_response(self, intent, entities, context):

    if intent.startswith("stats-case_types-in-location-date"):
      return self.get_stats_cases(intent, entities, context)
    elif intent.startswith("stats-where-sel_criterion-case_types-when"):
      return self.get_stats_where(intent, entities, context)
    elif intent.startswith("stats-plot"):
      return self.get_stats_plot(intent, entities, context)
    elif intent.startswith("stats-show-map"):
      return self.get_map(intent, entities, context)
