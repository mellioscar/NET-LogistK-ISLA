from datetime import datetime
import pytz

def get_argentina_time():
    return datetime.now(pytz.timezone('America/Argentina/Buenos_Aires'))

def format_firestore_date(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')
