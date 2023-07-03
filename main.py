import functions_framework
import requests
import os

@functions_framework.http
def get_net_salary(request):
    request_json = request.get_json(silent=True)
    send_tgram_message(request_json)
    return request_json


def send_tgram_message(message):
    url = f"https://api.telegram.org/{os.getenv('TBOT_TOKEN')}/sendMessage"
    r = requests.get(url, {'chat_id': os.getenv('CHAT_ID'), 'text': message})
    if r.status_code == 200:
        return
    raise ValueError(f"Error sending message: {message}")