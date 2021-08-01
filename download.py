import aiohttp, asyncio, sys
from base64 import b64encode
from pathlib import Path
from time import sleep
import PySimpleGUI as sg
import configparser
home_path = Path.home()
temp_html_path = home_path.joinpath('.latin_paradigm_finder')
temp_html_path.mkdir(parents=True, exist_ok=True)
sg.theme("Material1")
npar = 0
done = 0
baseurl = 'https://www.dizionario-latino.com/'
baseurl2 = 'https://www.dizionario-latino.com/dizionario-latino-italiano.php'
layout = [[sg.Text('Scaricamento ed analisi iniziale in corso', font=("Arial", 20))],
                  [sg.Text('su ogni parola presente nella versione.',font=("Arial", 16))],
                  [sg.HorizontalSeparator()],
                  [sg.Text('Inizializzazione...', key='conto', text_color='darkslateblue' , size=(50,1), font=("Arial 15 bold"))],
                  [sg.ProgressBar(1, orientation='h', size=(50, 30), key='progress')
                  ],
                  [sg.Text('Suggerimento: il programma salva i file nella cartella .latin_paradigm_finder.\nPiù volte lo userai, più diventerà veloce grazie ai file già salvati.')]]
window = sg.Window('ちょっと待って [Scaricando]', layout, icon='download.ico', finalize=True)
from bs4 import BeautifulSoup as bs
barra_progresso = window.FindElement('progress')
conto_fatti = window.FindElement('conto')

# From: https://github.com/aws/aws-cli/blob/1.16.277/awscli/clidriver.py#L55
# Don't remove this line.  The idna encoding
# is used by getaddrinfo when dealing with unicode hostnames,
# and in some cases, there appears to be a race condition
# where threads will get a LookupError on getaddrinfo() saying
# that the encoding doesn't exist.  Using the idna encoding before
# running any CLI code (and any threads it may create) ensures that
# the encodings.idna is imported and registered in the codecs registry,
# which will stop the LookupErrors from happening.
# See: https://bugs.python.org/issue29288
u''.encode('idna')

def updatewindow(done,npar, endurl):
    global barra_progresso, conto_fatti,window
    barra_progresso.UpdateBar(done,npar)
    conto_fatti.update(f'{round(done*100/npar)}% ({done}/{npar}) [{endurl.title()}]')


async def task(name, work_queue):
    async with aiohttp.ClientSession() as session:
        while not work_queue.empty():
            global done, npar
            url = await work_queue.get()
            removeuseless = url.rsplit('&',1)[0]
            endurl = removeuseless.rsplit('=', 1)[1]
            if url == removeuseless:
                lptpath = endurl + '.ini'
            else:
                lptpath = endurl + '.ff.ini'
            x = temp_html_path / lptpath
            if x.is_file() == False:
                async with session.get(url) as response:
                    html = await response.text()
                    soup = bs(html, 'lxml')
                    grammatica = soup.find_all('span', {'class': 'grammatica'})  # [0].get_text()
                    config = configparser.ConfigParser()
                    if "Si prega di controllare l'ortografia" in str(soup):
                        config.add_section("exceptions")
                        config.set("exceptions", "404", "True")
                        with open(x, 'w', encoding="utf-8") as cfile:
                            config.write(cfile)
                    elif len(grammatica) > 0:  # Questo significa che la pagina web è presente ed è quella di una parola
                        tipo = grammatica[0].get_text()
                        paradigmal = soup.findAll('span', {"class": "paradigma"})
                        if len(paradigmal) > 0:
                            config.add_section("parola")
                            paradigma = paradigmal[0].get_text()
                            paradigma = paradigma.replace("[", "").replace("]", "")
                            itatrad = soup.findAll('span', {"class": "italiano"})[0]
                            if 'participio' in itatrad.get_text():
                                participiolink = baseurl2 + itatrad.findAll('span', {"class": "paradigma"})[0].findAll('a', href=True)[0]['href']
                                config.set("parola", "participio", participiolink)
                            config.set("parola", "paradigma", paradigma)
                            config.set("parola", "tipo", tipo)
                            if 'verbo' in tipo or 'coniug' in tipo:
                                config.set("parola", "verbo", "True")
                            else:
                                config.set("parola", "verbo", "False")
                            with open(x, 'w', encoding="utf-8") as cfile:
                                config.write(cfile)
                        else:
                            if len(soup.findAll('div', {"id": "myth"})) > 0: # Parola indeclinabile
                                config.add_section("parola")
                                lemma = soup.findAll('span', {"class": "lemma"})[0].get_text()
                                config.set("parola", "lemma", lemma)
                                config.set("parola", "paradigma", "indeclinabile")
                                config.set("parola", "tipo", tipo)
                                config.set("parola", "verbo", "False")
                                with open(x, 'w', encoding="utf-8") as cfile:
                                    config.write(cfile)
                            else:
                                tags = soup.find_all('td', {'width': '80%'})
                                config.add_section("disambigua")
                                texts,links,verbs = [],[],[]
                                for tag in tags:
                                    texts.append(tag.get_text())
                                    links.append(baseurl + str(tag.find_all('a', href=True)[0]['href']))
                                    if 'verbo' in str(tag) or 'coniug' in str(tag):
                                        verbs.append("True")
                                    else:
                                        verbs.append("False")
                                if 'True' not in verbs:
                                    config.set("disambigua", "nessunverbo",'True')
                                else: 
                                    config.set("disambigua", "nessunverbo",'False')
                                config.set("disambigua", "links",'#'.join(links))
                                config.set("disambigua", "texts",'#'.join(texts))
                                config.set("disambigua", "verbs",'#'.join(verbs))
                                with open(x, 'w', encoding="utf-8") as cfile:
                                    config.write(cfile)
                    else:
                        raise ErroreGenerico
            done += 1
            updatewindow(done,npar,endurl)
            
async def main(lista):
    # Update window title
    # This is the main entry point for the webpage downloader
    # Create the queue of work
    work_queue = asyncio.Queue()
    # Put some work in the queue
    for url in lista:
        await work_queue.put(url)
    # Run the tasks
    await asyncio.gather(
        asyncio.create_task(task("One", work_queue)),
        asyncio.create_task(task("Two", work_queue)),
        asyncio.create_task(task("Three", work_queue)),
        asyncio.create_task(task("Four", work_queue)),
        asyncio.create_task(task("Five", work_queue)),
        asyncio.create_task(task("Six", work_queue)),
        asyncio.create_task(task("Seven", work_queue)),
        asyncio.create_task(task("Eight", work_queue)),
        asyncio.create_task(task("Nine", work_queue)),
        asyncio.create_task(task("Ten", work_queue)),
        asyncio.create_task(task("Eleven", work_queue)),
        asyncio.create_task(task("Twelve", work_queue)),
        asyncio.create_task(task("Thirteen", work_queue)),
        asyncio.create_task(task("Fourteen", work_queue)),
        asyncio.create_task(task("Fifteen", work_queue)),
        asyncio.create_task(task("Sixteen", work_queue))
    )


def download(lista):  # Dowload a list of urls asynchronously
    global npar, done
    npar = len(lista)
    done = 0
    asyncio.run(main(lista))
    window.close()