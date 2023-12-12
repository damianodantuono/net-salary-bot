import functions_framework
import re
import requests
import json
import firebase_admin
from firebase_admin import firestore

regions = {
    "Abruzzo": "abruzzo",
    "Basilicata": "basilicata",
    "Provincia Autonoma di Bolzano": "bolzano",
    "Calabria": "calabria",
    "Campania": "campania",
    "Emilia Romagna": "emiliaRomagna",
    "Friuli Venezia Giulia": "friuliVenezia",
    "Lazio": "lazio",
    "Liguria": "liguria",
    "Lombardia": "lombardia",
    "Marche": "marche",
    "Molise": "molise",
    "Piemonte": "piemonte",
    "Puglia": "puglia",
    "Sardegna": "sardegna",
    "Sicilia": "sicilia",
    "Toscana": "toscana",
    "Provincia Autonoma di Trento": "trentino",
    "Umbria": "umbria",
    "Valle d'Aosta": "aosta",
    "Veneto": "veneto",
}

firebase_admin.initialize_app()


@functions_framework.http
def get_net_salary(request):
    request_json = request.get_json(silent=True)
    request_dict = dict(request_json)
    is_callback: bool = False

    commands = ['/set_region']
    
    if "callback_query" in request_dict:
        is_callback: bool = True
        request_dict: dict = request_dict['callback_query']
        region = request_dict['data']

    message_id = request_dict['message']['message_id']
    chat_id = request_dict['message']['chat']['id']
    text = str.strip(request_dict['message']['text'])

    is_command: bool = text in commands
    is_ral: bool = text.isdigit()

    valid_input: bool = is_callback or is_command or is_ral

    if valid_input:
        if is_command:
            if text == '/set_region':
                reply_markup: dict = {
                "inline_keyboard": [[{"text": region, "callback_data": regions[region]}] for region in regions]
                }
                send_tgram_message("Imposta la regione", chat_id, reply_markup=json.dumps(reply_markup))
        elif is_callback:
            add_or_update_firestore_document(chat_id, region)
            edit_tgram_message(f"{region} impostata", chat_id, message_id)
        elif is_ral:
            ral = int(text)
            region = get_firestore_data(chat_id)
            if region is None:
                send_tgram_message("Please first set your region with /set_region", chat_id)
                return 'MISSING_REGION'
            net_salary, taxes = scrape_salary(ral, region)
            message = message_builder(ral, net_salary, taxes, region)
            send_tgram_message(message, chat_id)
    return 'OK'


def send_tgram_message(message, chat_id, reply_markup=None):
    url = f"https://api.telegram.org/bot5816345244:AAEt49SGqstBCmB-RRaAtvqZi7BQQ5XPkaU/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
    }
    if reply_markup is not None:
        params['reply_markup'] = reply_markup

    r = requests.get(url, params)
    print(r.text)


def edit_tgram_message(message: str, chat_id: int, message_id: int):
    url = f"https://api.telegram.org/bot5816345244:AAEt49SGqstBCmB-RRaAtvqZi7BQQ5XPkaU/editMessageText"
    params = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": message,
    }

    r = requests.get(url, params)

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

def add_or_update_firestore_document(chat_id, region):
    db = firestore.client()

    # Define the data to be added or updated in the document
    data = {
        'region': region,
    }

    # Set the document with CHAT_ID as the document ID
    db.collection('regions').document(str(chat_id)).set(data)

def get_firestore_data(chat_id):
    db = firestore.client()

    # Retrieve the document with the specified CHAT_ID
    doc_ref = db.collection('regions').document(str(chat_id))
    doc = doc_ref.get()

    # Check if the document exists
    if doc.exists:
        # Retrieve the data from the document
        data = doc.to_dict()
        return data['region']
    else:
        return None
