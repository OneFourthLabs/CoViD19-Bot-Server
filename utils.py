import datetime
import smtplib, ssl

def read_date(date):
  if date[0:4] == '2021':
    date = '2020' + date[4:]
  return datetime.datetime.strptime(date[0:10], '%Y-%m-%d')

def write_date(date):
  return date.strftime("%B %d")

def unlist(var):
  if type(var) == list:
    return var[0]
  else:
    return var

def dict_stringify(entities):
  ## Converts dictionary of lists/strings to a string separated by ,
  ## TODO: Simplify using json.dumps(entities)
  str_ = ""
  for key in sorted(entities.keys()) :
    if len(entities[key]) > 0:
      str_ += key + ":["
      if type(entities[key]) == str:
        str_ += entities[key]
      elif type(entities[key]) == list:
        str_ += ','.join(sorted(entities[key]))
      str_ += "],"
  return str_

def send_email_amazon_ses(email,message):
    port = 587  # For TLS
    smtp_server = "email-smtp.ap-south-1.amazonaws.com"
    sender_email = "padhai@onefourthlabs.com"  # Enter your address
    username = 'AKIAQUZXTKQUGUPFSUTT'
    password = 'BISWYdsQVqHUJkJIY2KN4SoR3NZJ7SSp/v+cRsMbspAz'
    
    receiver_email = email  # Enter receiver address
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.sendmail(sender_email, receiver_email, message)