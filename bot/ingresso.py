import requests
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

global THEATERS
global SECTIONS

def get_cinemas(theaters) -> None:
    CITY_ID = "22" # Recife, 380 Caruaru
    EVENT_ID = "24985" # Twenty One Pilots Cinema Experience
    DATE = "2022-05-19" # Event Date
    API_URL = f'https://api-content.ingresso.com/v0/sessions/city/{CITY_ID}/event/{EVENT_ID}?partnership=&date={DATE}'
    HEADERS = {
        'Accept': 'application/json',
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

def get_sections(theaters, sections) -> None:
    for theater in theaters:
        for room in theater['rooms']:
            for session in room['sessions']:
                SESSION_ID = session['id']
                API_URL = f'https://api.ingresso.com/v1/sessions/{SESSION_ID}/'
                HEADERS = {
                    'authority':'api.ingresso.com',
                    'accept': 'application/json',
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


def get_occupation(lines) -> str:
    TOTAL_SEATS = 0
    UNAVAILABLE_SEATS = 0 
    for line in lines:
        line_seats = line['seats']
        TOTAL_SEATS += len(line_seats)
        for seat in line_seats:
            if seat['status'] != 'Available':
                UNAVAILABLE_SEATS += 1
    
    return f'    [+] Occupancy: {UNAVAILABLE_SEATS}/{TOTAL_SEATS}\n'


def get_seats(sections) -> str:
    message = "```\n"
    for section in sections:
        theatre_name = section['theatre']['name']
        message += f'[!] {theatre_name}\n'
        
        session_id = section['session_id']
        
        for unique_section in section['sections']:
            section_name = unique_section['name']
            message += f'    [+] {section_name}\n'
            section_id = unique_section['id']
            api_url = f'https://api.ingresso.com/v1/sessions/{session_id}/sections/{section_id}/seats'
            headers = {
                'authority':'api.ingresso.com',
                'accept': 'application/json',
                'accept-language': 'pt-BR,pt;q=0.9',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'                    
            }
            response = requests.get(url=api_url, headers=headers)
            if response.status_code == 200:
                lines = response.json()['lines']
                occupation = get_occupation(lines)
                message += occupation
            else:
                message += f'    [+] Occupancy not available\n'
        message += '\n'
    message += '```'
    return message

def get_seats_and_map(section) -> str:
    message = "```\n"
    theatre_name = section['theatre']['name']
    message += f'[!] {theatre_name}\n'
    
    session_id = section['session_id']
    
    for unique_section in section['sections']:
        section_name = unique_section['name']
        message += f'    [+] {section_name}\n'
        section_id = unique_section['id']
        api_url = f'https://api.ingresso.com/v1/sessions/{session_id}/sections/{section_id}/seats'
        headers = {
            'authority':'api.ingresso.com',
            'accept': 'application/json',
            'accept-language': 'pt-BR,pt;q=0.9',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'                    
        }
        response = requests.get(url=api_url, headers=headers)
        if response.status_code == 200:
            lines = response.json()['lines']
            occupation = get_occupation(lines)
            map = generate_map(lines)
            message += occupation
        else:
            message += f'    [+] Occupancy not available\n'
        message += '\n'
    message += map
    message += '```'
    return message    

def generate_map(lines) -> str:
    map = []
    limit = 0
    return_map = ''

    for line in lines:
        string_line = ""
        line_size = len(line['seats'])
        if line_size > limit:
            limit = line_size
        for seat in line['seats']:
            if seat['status'] == 'Available':
                string_line += 'o'
            else:
                string_line += '-'
        map.append(string_line)
    
    for line in map:
        return_map += line.center(limit) + '\n'
    return_map += '\n'
    return return_map  

def run_tasks(context: CallbackContext) -> None:
    NEW_THEATERS = []
    NEW_SECTIONS = []

    get_cinemas(theaters=NEW_THEATERS)
    get_sections(theaters=NEW_THEATERS, sections=NEW_SECTIONS)
    message = get_seats(sections=NEW_SECTIONS)

    job = context.job
    context.bot.send_message(job.context, text=message, parse_mode='Markdown')

    if len(NEW_THEATERS) > 0:
        global THEATERS
        THEATERS = NEW_THEATERS
    if len(NEW_SECTIONS) > 0:
        global SECTIONS
        SECTIONS = NEW_SECTIONS    

def get_map(update: Update, context: CallbackContext) -> None:
    local_sections = SECTIONS
    map = ''
    try:
        session = context.args[0:]
        for session_arg in session:
            for theatre in local_sections:
                theatre_name = theatre['theatre']['name']
                if session_arg.lower() in theatre_name.lower():
                    map = get_seats_and_map(theatre)
                    break
            if map:
                break
        
        if not map:
            update.message.reply_text('Sorry, I cannot find this theatre')
            return

        update.message.reply_text(map, parse_mode='Markdown')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /map <theatre_name>')


def start(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:

        context.job_queue.run_repeating(run_tasks, interval=3600, first=5, context=chat_id, name=str(chat_id))

        text = 'Alright! Now I\'ll notify you every hour, starting 5 seconds from now...'
        update.message.reply_text(text)

    except Exception as e:
        update.message.reply_text(f'Error! {str(e)}')

def status(update: Update, context: CallbackContext) -> None:
    NEW_THEATERS = []
    NEW_SECTIONS = []

    get_cinemas(theaters=NEW_THEATERS)
    get_sections(theaters=NEW_THEATERS, sections=NEW_SECTIONS)
    message = get_seats(sections=NEW_SECTIONS)

    update.message.reply_text(text=message, parse_mode='Markdown')

    if len(NEW_THEATERS) > 0:
        global THEATERS
        THEATERS = NEW_THEATERS
    if len(NEW_SECTIONS) > 0:
        global SECTIONS
        SECTIONS = NEW_SECTIONS

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Job successfully cancelled!' if job_removed else 'You have no active job.'
    update.message.reply_text(text)

def main():

    updater = Updater("TOKEN")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("stop", unset))
    dispatcher.add_handler(CommandHandler("map", get_map))


    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()