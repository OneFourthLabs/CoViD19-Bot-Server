import smtplib, ssl

AWS_SES_SMTP_SERVER = "email-smtp.ap-south-1.amazonaws.com"
DEFAULT_SENDER_EMAIL = "covid19@onefourthlabs.com"
AWS_SES_USERNAME = 'AKIAQUZXTKQUGUPFSUTT'
AWS_SES_SECRET_KEY = 'BISWYdsQVqHUJkJIY2KN4SoR3NZJ7SSp/v+cRsMbspAz'

def send_email_amazon_ses(email, message):
    return send_email(email, message, DEFAULT_SENDER_EMAIL,
                      AWS_SES_USERNAME, AWS_SES_SECRET_KEY, AWS_SES_SMTP_SERVER)


def send_email(to_email, message, sender_email,
                username, password, smtp_server):
    port = 587  # For TLS
    
    receiver_email = to_email  # Enter receiver address
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.sendmail(sender_email, receiver_email, message)
