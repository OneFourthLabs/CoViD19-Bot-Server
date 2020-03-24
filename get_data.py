# -*- coding: utf-8 -*-
"""csv-to-json.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uMcGJKRFaEVstKb6YKnPw1l-bzRylmfN
"""

import pandas as pd
import datetime
import os 
import json
import numpy as np

# replace some names used in the file so that they confirm to ISO standards 
# (which is what DialogFlow will give as system intents)
replacement_dict = {
    'US': 'United States',
    'Korea, South': 'South Korea'
}

# get the three files
# os.system("rm *.csv")
os.system("curl -O https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv")
os.system("curl -O https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv")
os.system("curl -O https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv")

def process_df(label):
    ## read the file corresponding to one: recovered, deaths, new cases
    df = pd.read_csv('time_series_19-covid-' + label + '.csv')
    ## replace any non-standard ways of referencing countries / states
    for key in replacement_dict:
        df.replace(key, replacement_dict[key], inplace=True)
    ## rename columns for easy access
    df.rename(columns={df.columns[0]: 'State', df.columns[1]: 'Country'}, inplace=True)
    ## delete lat and long 
    df.drop(df.columns[2:4], axis=1, inplace=True)
    ## remove nans for empty states to empty string
    df['State'].fillna('Total', inplace=True)
    df.fillna('', inplace=True)
    ## create new rows for those countries which have only state wise numbers
    df_group = df.groupby(by=df.columns[1]).sum()
    df_group.reset_index(inplace=True)
    ## append the new rows for country wise aggregation to original df
    df = df.append(df_group, sort=True)
    df['State'].fillna('Total', inplace=True)
    df.fillna('', inplace=True)
    ## remove any duplicate rows - eg. country like India which has no state-wise info
    df.drop_duplicates(inplace=True)
    ## convert from wide form to narrow/long form
    df = pd.melt(df, id_vars = ['Country', 'State'] , var_name = 'Date', value_name=label)
    df.drop_duplicates(inplace=True)
    df[label].replace('', np.nan, inplace=True)
    df.dropna(subset=[label], inplace=True)
    return df

## process the three files
df_confirmed = process_df('Confirmed')
df_recovered = process_df('Recovered')
df_deaths = process_df('Deaths')
## merge the three files into one
df = df_confirmed.merge(df_recovered, on=['Country', 'State', 'Date']).merge(df_deaths, on=['Country', 'State', 'Date'])

##load India data
# get india data
os.system("curl -O https://api.rootnet.in/covid19-in/stats/daily")
with open('daily') as f:
  data = json.load(f)
for item in data['data']:
    day = item['day']
    # don't put India level data as that is already available
    # df = df.append({
    #     'Country': 'India', 
    #     'State': 'Total', 
    #     'Date': day, 
    #     'Confirmed': item['summary']['total'], 
    #     'Recovered': item['summary']['discharged'], 
    #     'Deaths': item['summary']['deaths']
    #     }, ignore_index=True)
    for reg_item in item['regional']:
        df = df.append({
            'Country': 'India',
            'State': reg_item['loc'],
            'Date': day,
            'Confirmed': reg_item['confirmedCasesIndian'] + reg_item['confirmedCasesForeign'],
            'Recovered': reg_item['discharged'],
            'Deaths': reg_item['deaths']
        }, ignore_index=True)


## convert the date string to datetime format
df['Date'] = pd.to_datetime(df['Date'])
df.sort_values(by=['Country', 'State', 'Date'], inplace=True)
df[['Confirmed','Recovered','Deaths']] = df[['Confirmed','Recovered','Deaths']].fillna(0)

for index, row in df.iterrows(): 
    if (type(row['Confirmed']) == str) or (type(row['Recovered']) == str) or (type(row['Deaths']) == str):
        print(row)
        break

df[['Confirmed','Recovered','Deaths']] = df[['Confirmed','Recovered','Deaths']].diff()

df = df[(df['Confirmed'] >= 0) & (df['Recovered'] >= 0) & (df['Deaths'] >= 0)]
# df = df[df['Date'] != datetime.datetime.strptime('2020-01-22', '%Y-%m-%d')]


df_total = df[df['State'] == 'Total']
df_total = df_total.groupby('Date').sum()

df_total.reset_index(level=0, inplace=True)
df_total['State'] = 'Total'
df_total['Country'] = 'World'
df_total = df_total[['Country', 'State', 'Date', 'Confirmed', 'Recovered', 'Deaths']]
df = df.append(df_total, ignore_index = True)

df.to_csv('coronabot_stats_data.csv', index=False)

# # writes output to json file which is optimised for query
# # queries can be on country, then optionally state, and optionally date
# with open('coronabot_stats_data.json', 'w') as json:
#     prev_country = ""
#     prev_state = ""
#     json.write('{\n')
#     for i in df.index: 
#         country = df['Country'][i]
#         state = df['State'][i]
#         if not prev_country == country:
#             if not prev_country == "":
#                 json.write('\n\t}\n},\n')
#             json.write('"' + country + '": {\n')
#             json.write('\t"' + state + '": {\n')
#         elif not prev_state == state:
#             json.write('\t},\n')
#             json.write('\t"' + state + '": {\n')
#         else:
#             json.write(',\n')
#         json.write('\t\t"' + 
#                    str(df['Date'][i]) + 
#                    '": {\n\t\t\t"Deaths": ' + str(df['Deaths'][i]) + 
#                    ',\n\t\t\t"Recovered": ' + str(df['Recovered'][i]) + 
#                    ',\n\t\t\t"Confirmed": ' + str(df['Confirmed'][i]) 
#                    + "\n\t\t}")
#         prev_country = country
#         prev_state = state
#     json.write('\n\t}\n}\n}')

