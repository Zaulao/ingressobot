import requests
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def get_cinemas(theaters):
    CITY_ID = "22" # Recife
    EVENT_ID = "24985" # Twenty One Pilots Cinema Experience
    DATE = "2022-05-19" # Event Date
    API_URL = f'https://api-content.ingresso.com/v0/sessions/city/{CITY_ID}/event/{EVENT_ID}?partnership=&date={DATE}'
    HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.ingresso.com',
        'Referer': 'https://www.ingresso.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile':'?0',
        'sec-ch-ua-platform': '"Linux"'
    }

    req = requests.get(url=API_URL, headers=HEADERS).json()
    updated_theaters = req[0]['theaters']

    for theater in updated_theaters:
        theater_name = theater['name']
        if(theater_name not in theaters):
            theaters.append(theater)

def get_sections(theaters, sections):
    for theater in theaters:
        for room in theater['rooms']:
            for session in room['sessions']:
                SESSION_ID = session['id']
                API_URL = f'https://api.ingresso.com/v1/sessions/{SESSION_ID}/'
                HEADERS = {
                    'authority':'api.ingresso.com',
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'pt-BR,pt;q=0.9',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Linux"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'                    
                }
                req = requests.get(url=API_URL, headers=HEADERS).json()
                updated_sections = {'session_id': req['id'],"theatre": req['theatre'], 'sections': req['sections']}
                if updated_sections not in sections:
                    sections.append(updated_sections)


def get_occupation(lines):
    TOTAL_SEATS = 0
    UNAVAILABLE_SEATS = 0 
    for line in lines:
        line_seats = line['seats']
        TOTAL_SEATS += len(line_seats)
        for seat in line_seats:
            if seat['status'] != 'Available':
                UNAVAILABLE_SEATS += 1
    
    return f'    [+] Occupancy: {UNAVAILABLE_SEATS}/{TOTAL_SEATS}\n'


def get_seats(sections, context: CallbackContext) -> None:
    for section in sections:
        message = "```"
        theatre_name = section['theatre']['name']
        message += f'[*] {theatre_name}\n'
        
        SESSION_ID = section['session_id']
        
        for unique_section in section['sections']:
            section_name = unique_section['name']
            message += f'    [+] {section_name}\n'
            SECTION_ID = unique_section['id']
            API_URL = f'https://api.ingresso.com/v1/sessions/{SESSION_ID}/sections/{SECTION_ID}/seats'
            HEADERS = {
                'authority':'api.ingresso.com',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'pt-BR,pt;q=0.9',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'                    
            }
            req = requests.get(url=API_URL, headers=HEADERS).json()
            lines = req['lines']
            message += get_occupation(lines)
            job = context.job
            message += '```'
            context.bot.send_message(job.context, text=message, parse_mode='Markdown')


def run_tasks(context: CallbackContext) -> None:
    THEATERS = []
    SECTIONS = []

    get_cinemas(theaters=THEATERS)
    get_sections(theaters=THEATERS, sections=SECTIONS)
    get_seats(sections=SECTIONS, context=context)


def start(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:

        context.job_queue.run_repeating(run_tasks, interval=3600, first=5, context=chat_id, name=str(chat_id))

        text = 'Alright! Now I\'ll notify you every hour, starting 5 seconds from now...'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Error!')

def main():

    updater = Updater("TOKEN")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()