import functions_framework
import requests
import os
import re

@functions_framework.http
def get_net_salary(request):
    request_json = request.get_json(silent=True)
    region = os.getenv("REGION")
    ral = 39000
    net_salary, taxes = scrape_salary(int(ral), region)
    message = message_builder(ral, net_salary, taxes, region)
    send_tgram_message(message)
    return 'Ok'


def message_builder(ral, net_salary, taxes, region):
    return f"""Stipendio netto in {region} con una RAL di {ral:,} €.
-   Netto Annuo: {net_salary:,}
-   Tasse: {taxes:,}
-   Netto 12M: {round(net_salary / 12):,}
-   Netto 13M: {round(net_salary / 13):,}
-   Netto 14M: {round(net_salary / 14):,}
    """


def send_tgram_message(message):
    url = f"https://api.telegram.org/bot{os.getenv('TBOT_TOKEN')}/sendMessage"
    r = requests.get(url, {'chat_id': os.getenv('CHAT_ID'), 'text': message})
    if r.status_code != 200:
        raise ValueError(f"Cannot send message {message}")


def scrape_salary(ral, region):
    url = f"https://www.pmi.it/servizi/292472/calcolo-stipendio-netto.html?step=2&ral={ral}&reg={region}&com=0.8&car=no&emp=privato&hw=no&toc=ind&tow=no&child_noau=0&child_au=0&childh=0&childcharge=100&family=0&monthlypay=14&days=365"
    r = requests.get(url)
    print(url)
    print(r.text)
    pattern = r'<span\sid=\"netto-anno\"\sclass=\"income-net\">([\d|\.]+)\s€</span>'
    if match := re.search(pattern, r.text):
        value = match.group(1)
        cleaned_value = value.replace('.', '')
        net_salary = int(cleaned_value)
        taxes = ral - net_salary
        return net_salary, taxes
