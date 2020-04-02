CORONA_QA_JSON = 'coronabot_qa_data.json'

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
