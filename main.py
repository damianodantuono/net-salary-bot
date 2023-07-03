import functions_framework
import requests
import os
import re

@functions_framework.http
def get_net_salary(request):
    request_json = request.get_json(silent=True)
    request_dict = dict(request_json)
    input_message = request_dict['message']['text']
    message_pattern = r'/ral\s(\d+)'
    if match := re.search(message_pattern, input_message):
        region = os.getenv("REGION")
        ral = int(match.group(1))
        net_salary, taxes = scrape_salary(ral, region)
        message = message_builder(ral, net_salary, taxes, region)
        send_tgram_message(message)
    return 'Ok'


def message_builder(ral, net_salary, taxes, region):
    ral_print = f"{ral:,.2f} €"
    taxes_print = f"{taxes:,.2f} €"
    net_salary_print = f"{net_salary:,.2f} €"
    net_salary_12M = f"{round(net_salary / 12):,.2f} €"
    net_salary_13M = f"{round(net_salary / 13):,.2f} €"
    net_salary_14M = f"{round(net_salary / 14):,.2f} €"
    return f"""Stipendio netto in {region} con una RAL di {ral_print}.
-   Netto Annuo: {net_salary_print}
-   Tasse: {taxes_print}
-   Netto 12M: {net_salary_12M}
-   Netto 13M: {net_salary_13M}
-   Netto 14M: {net_salary_14M}
    """


def send_tgram_message(message):
    url = f"https://api.telegram.org/bot{os.getenv('TBOT_TOKEN')}/sendMessage"
    r = requests.get(url, {'chat_id': os.getenv('CHAT_ID'), 'text': message})
    if r.status_code != 200:
        raise ValueError(f"Cannot send message {message}")


def scrape_salary(ral, region):
    url = f"https://www.pmi.it/servizi/292472/calcolo-stipendio-netto.html?step=2&ral={ral}&reg={region}&com=0.8&car=no&emp=privato&hw=no&toc=ind&tow=no&child_noau=0&child_au=0&childh=0&childcharge=100&family=0&monthlypay=14&days=365"
    r = requests.get(url)
    pattern = r'<span\sid=\"netto-anno\"\sclass=\"income-net\">([\d|\.]+)\s€</span>'
    if match := re.search(pattern, r.text):
        value = match.group(1)
        cleaned_value = value.replace('.', '')
        net_salary = int(cleaned_value)
        taxes = ral - net_salary
        return net_salary, taxes
