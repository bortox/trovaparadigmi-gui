print('Benvenut@ in Trovaparadigmi sviluppato da bortox.it (Andrea Bortolotti)!\nSpero di farti risparmiare tempo e fatica!')
import PySimpleGUI as sg
sg.theme("Material1")
font = ("Arial, 12")
from pathlib import Path
home_path = Path.home()
temp_html_path = home_path.joinpath('.latin_paradigm_finder')
temp_html_path.mkdir(parents=True, exist_ok=True)
sg.set_options(font=font)
import configparser
import urllib.request, urllib.error, urllib.parse, webbrowser, sys, clipboard
from re import sub
import aiohttp
from bs4 import BeautifulSoup as bs
from pathvalidate import sanitize_filepath
from unidecode import unidecode as rimuovi_accenti

# From: https://github.com/aws/aws-cli/blob/1.16.277/awscli/clidriver.py#L55 ( per sicurezza anche qui )
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

parolancora = True
formeflesse = False
smartest = True
paradigmasemplice = False
accenti = False
baseurl = 'https://www.dizionario-latino.com/'
baseurl2 = baseurl + 'dizionario-latino-italiano.php'
baseurl_parola = baseurl2 + '?parola='
titolo = 'Arial 20'
titolograssetto = 'Arial 20 bold'
sottotitolo = 'Arial 14'
paragrafo = 'Arial 12'


def load_preferences(filename):
    x = temp_html_path / filename
    if x.is_file() == True:
        config = configparser.ConfigParser()
        config.read(x, encoding='utf-8' )
        y = config.get('preferences', 'ff', fallback=False)
        global formeflesse,smartest,accenti,paradigmasemplice
        if y == False:
            formeflesse = False
        else:
            formeflesse = True
        y = config.get('preferences', 'smartest', fallback=False)
        if y == False:
            smartest = False
        else:
            smartest = True
        y = config.get('preferences', 'accenti', fallback=False)
        if y == False:
            accenti = False
        else:
            accenti = True
        y = config.get('preferences', 'paradigmasemplice', fallback=False)
        if y == False:
            paradigmasemplice = False
        else:
            paradigmasemplice = True



def parse_filename_from_nome_and_formeflesse(nome, formeflesse):
    if formeflesse == True:
        fname = f"{nome}.ff.ini"
    else:
        fname = f"{nome}.ini"
    return fname

def parse_filename_from_url(url):  # Ritorna il nome del file di configurazione dall'URL fornito
    removeuseless = url.rsplit('&', 1)[0]
    endurl = removeuseless.rsplit('=', 1)[1]
    if url == removeuseless:
        lptpath = endurl + '.ini'
    else:
        lptpath = endurl + '.ff.ini'
    return lptpath


def parse_html_to_ini(html, url):  # Analizza il codice HTML e lo scrive in un file INI di configurazione
    x = temp_html_path / parse_filename_from_url(url)
    if x.is_file() == False:
        soup = bs(html, 'lxml')
        grammatica = soup.find_all('span', {'class': 'grammatica'})
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
                    texts, links, verbs = [], [], []
                    for tag in tags:
                        texts.append(tag.get_text())
                        links.append(baseurl + str(tag.find_all('a', href=True)[0]['href']))
                        if 'verbo' in str(tag) or 'coniug' in str(tag):
                            verbs.append("True")
                        else:
                            verbs.append("False")
                    if 'True' not in verbs:
                        config.set("disambigua", "nessunverbo", 'True')
                    else:
                        config.set("disambigua", "nessunverbo", 'False')
                    config.set("disambigua", "links", '#'.join(links))
                    config.set("disambigua", "texts", '#'.join(texts))
                    config.set("disambigua", "verbs", '#'.join(verbs))
                    with open(x, 'w', encoding="utf-8") as cfile:
                        config.write(cfile)


def download_webpage_from_url(url):  # Scarica pagina da url
    while True:
        try:
            html = urllib.request.urlopen(url).read()
            return html
        except ConnectionError:
            sg.Popup('Errore di connessione', 'Controlla la connessione, poi clicca OK per riprovare..')
        except urllib.error.HTTPError as e:
            sg.Popup('Errore di connessione', 'Controlla la connessione, poi clicca OK per riprovare. (' + str(e) + ')')
        except urllib.error.URLError as e:
            sg.Popup('Errore di connessione', 'Controlla la connessione, poi clicca OK per riprovare. (' + str(e) + ')')



def check_config_file_if_not_exist_download(
        fname):  # Controlla se il file di configurazione esiste, se non esiste scaricalo
    x = temp_html_path / fname
    if x.is_file() == False:
        if '.ff' in fname:
            url = baseurl_parola + fname.split('.', 1)[0] + '&md=ff'
        else:
            url = baseurl_parola + fname.split('.', 1)[0]
        html = download_webpage_from_url(url)
        parse_html_to_ini(html, url)
    return x


def analyze_config_file_return_troppe_cose(fname):
    path = check_config_file_if_not_exist_download(fname)
    config = configparser.ConfigParser()
    config.read(path, encoding='utf-8' )
    y = config.get('exceptions', '404', fallback=False)
    if y == True or y == "True":
        return 404
    paradigma = config.get('parola', 'paradigma', fallback=False)
    if paradigma != False:
        tipo = config.get('parola', 'tipo', fallback='Nessun tipo')
        if paradigma == "indeclinabile":
            lemma = config.get('parola', 'lemma', fallback='Nessun lemma')
            return (None, tipo, lemma)
        else:
            global paradigmasemplice
            if paradigmasemplice == True and len(paradigma.split(', ')) > 3:
                l = paradigma.split(', ')
                li = [l[0],l[1],l[-1]]
                return ','.join(li),tipo
            else: return paradigma,tipo
    else:
        links = config.get('disambigua', 'links').split('#')
        texts = config.get('disambigua', 'texts').split('#')
        verbs = config.get('disambigua', 'verbs').split('#')
        return (texts, links, verbs)


def analyze_config_file_return_paradigma(fname,autodisambigua):
    global paradigmasemplice
    path = check_config_file_if_not_exist_download(fname)
    config = configparser.ConfigParser()
    config.read(path, encoding='utf-8' )
    y = config.get('exceptions', '404', fallback=False)
    if y == True or y == "True": return 404  # Codice d'errore se la pagina per la parola cercata non esiste
    y = config.get('parola', 'paradigma', fallback=False)
    if y != False and y != "indeclinabile":
        z = config.get('parola', 'verbo', fallback=False)
        if z == "True":
            if paradigmasemplice == True:
                l = y.split(',')
                li = [l[0],l[1],l[-1]]
                return ','.join(li)
            else: return y
        else:
            return 1  # Codice d'errore se la parola ha un paradigma ma non è un verbo
    if y == "indeclinabile": return 2  # Codice d'errore se la parola è indeclinabile e non ha un paradigma
    y = config.get('disambigua', 'nessunverbo', fallback='v')
    if y == 'v':
        return 3  # Codice d'errore strano, non dovrebbe succedere in realtà, questo accade quando c'è qualcosa di inaspettato
    elif y == True or y == 'True':
        return 4  # La parola può essere disambiguata, ma nessun verbo viene incluso
    participiolink = (config.get('parola', 'participio', fallback=False))
    if participiolink != False:
        tipo = config.get('parola', 'tipo', fallback='participio')
        if autodisambigua != 'Yes':
            fverbale = sg.PopupYesNo(f'Questo è un {tipo}', 'Ha funzione verbale ( ossia non può essere interpretato come nome oppure aggettivo ) ?\nIn caso affermativo, rispondi "Yes" e ne sarà aggiunto il paradigma alla lista finale!')
            if fverbale == 'Yes':
                fname = parse_filename_from_url(participiolink)
                return analyze_config_file_return_paradigma(fname,True)
        else:
            fname = parse_filename_from_url(participiolink)
            return analyze_config_file_return_paradigma(fname,True)
    else:
        links = config.get('disambigua', 'links').split('#')
        texts = config.get('disambigua', 'texts').split('#')
        verbs = config.get('disambigua', 'verbs').split('#')
        url = disambigua_verb_window(texts, links, verbs, fname.split('.', 1)[0], autodisambigua)
        fname = parse_filename_from_url(url)
        check_config_file_if_not_exist_download(fname)
        return analyze_config_file_return_paradigma(fname,True) #paradigma


def popup_err_generico():
    sg.Popup('Errore Generico',
             'Errore strano. Il programma si chiuderà.\nPer aiutarmi nel rimuoverlo, mandami una mail a bort0x@tuta.io')
    sys.exit(0)


def check_preferences():
    config = configparser.ConfigParser()
    config.add_section("preferences")
    layout = [[sg.Text('Seleziona le tue preferenze.', font=(titolograssetto), justification='center')],
                [sg.Text('Ricorderò tutte le volte che aprirai il programma le preferenze impostate in questa schermata.',
                        font=("Arial", 16))],
                [sg.HorizontalSeparator()],
                [sg.Text("Scrittura dei paradigmi: semplificata?", font=(paragrafo))],
                [sg.Radio('facio, facis, facere', "stileparadigma", key="paradigmasemplice", enable_events=True)],
                [sg.Radio('facio, facis, feci, factum, facere', "stileparadigma", key="paradigmacomplesso", enable_events=True, default=True)],
                [sg.HorizontalSeparator()],
                [sg.Checkbox('Rimuovi accenti', default=True, font=(paragrafo), key="accenti", pad=(0, 0))],
                [sg.Text(
                    'Rimuove gli accenti dai paradigmi trovati, potresti essere meno sgamabile per averli copiati online.',
                    pad=(12, 12))],
                [sg.HorizontalSeparator()],
                [sg.Checkbox('Riconoscimento intelligente ausiliare', default=True, font=(paragrafo), key="smartest", pad=(0, 0))],
                [sg.Text(
                    'Con questa opzione quando traduci una versione sarà automaticamente riconosciuta la presenza del verbo essere come ausiliare.\nAd esempio, in "factum erat" il verbo essere (sum,es,fui,esse) non sarà aggiunto alla lista dei paradigmi. ',
                    pad=(12, 12))],
                [sg.HorizontalSeparator()],
                [sg.Checkbox('Forme flesse', default=False, font=(paragrafo), key="ff", pad=(0, 0))],
                [sg.Text(
                    'Con questa opzione raramente puoi avere la possibilità di trovare verbi altrimenti riconosciuti come sostantivi.\nNon la consiglio, è scomoda ed irritante, perché porta alla creazione di numerose finestre di disambiguazione.\n\nPossibili vantaggi durante la traduzione della versione:\n-maggiore precisione nel riconoscimento dei verbi\n-riconoscimento e disambiguazione participi.\n\nUsandola a lungo, migliorerà.',
                    pad=(12, 12))],
                [sg.HorizontalSeparator()],
                [sg.Button('Continua')]]
    window = sg.Window('Imposta preferenze programma', layout, icon='icona.ico')

    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Continua':
            global formeflesse,smartest,accenti,paradigmasemplice
            if values["ff"] == True:
                formeflesse = True
                config.set("preferences", "ff", "True")
            else:
                formeflesse = False
            if values["smartest"] == True:
                smartest = True
                config.set("preferences", "smartest", "True")
            else:
                smartest = False
            if values["accenti"] == True:
                accenti = False
            else:
                accenti = True
                config.set("preferences", "accenti", "True")
            if values["paradigmasemplice"] == True:
                paradigmasemplice = True
                config.set("preferences", "paradigmasemplice", "True")
            else:
                paradigmasemplice = False
            x = temp_html_path / 'config'
            with open(x, 'w', encoding="utf-8") as cfile:
                config.write(cfile)
            break
        elif event == sg.WINDOW_CLOSED:
            break
    window.close()


def create_generic_window(title, layout, continue_event, close_event, prefs_event):
    # Load program preferencies:
    load_preferences('config')
    # Create the window
    window = sg.Window(title, layout, element_justification='c', icon='icona.ico')
    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == close_event:
            sys.exit(0)
        elif event == continue_event:
            break
        elif event == prefs_event:
            check_preferences()
    window.close()


def cercare_parola():
    layout = [[sg.Text('Cosa vuoi fare:', font=(titolograssetto), justification='center')],
                [sg.Button('Trova paradigma di una parola',size=(25,1))],
                [sg.Button('Trova paradigmi di una versione', size=(25,1))],
                [sg.Text('Semplice e veloce!', font=('Arial 8'), justification='center')]]
    window = sg.Window('Trovaparadigmi by bort0x', layout, icon='icona.ico')

    while True:  # Event Loop
        event, values = window.Read()
        parola = True
        if event == 'Trova paradigma di una parola':
            break
        elif event == 'Trova paradigmi di una versione':
            parola = False
            break
        elif event == sg.WINDOW_CLOSED:
            sys.exit(0)

    window.close()
    return parola


def seleziona_parola():
    parola = ''
    ff = False
    layout = [[sg.Text('Trovaparadigma', font=(titolo), justification='center')],
              [sg.HorizontalSeparator()],
              [sg.Text(
                  'Inserisci qua sotto la parola di cui estrarre il paradigma latino\npoi clicca su "Trova il paradigma"')],
              [sg.Text('Parola'), sg.InputText()],
              [sg.Checkbox('Forme flesse', default=False, key="ff"),
               sg.Button('Trova il paradigma', bind_return_key=True)]]

    window = sg.Window('Paradigma da parola', layout, icon='icona.ico')

    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Trova il paradigma':
            parola = filter_versione(values.get(1))
            ff = values['ff']
            if len(parola)<1:
                sg.Popup('Inserisci una parola', 'Non hai inserito nessuna parola, per trovare il paradigma prima scrivi qualcosa')
            elif len(parola[0])<1:
                sg.Popup('Inserisci una parola', 'Non hai inserito nessuna parola, per trovare il paradigma prima scrivi qualcosa')
            else:
                break
        elif event == sg.WINDOW_CLOSED:
            sys.exit(0)
    window.close()
    return parola[0] , ff


def no_paradigma_window(tipo, lemma):
    global accenti
    if accenti == False:
        to,la = rimuovi_accenti(tipo), rimuovi_accenti(lemma)
    else:
        to,la = tipo, lemma
    layout = [[sg.Text(la, font=(titolograssetto))],
              [sg.HorizontalSeparator()],
              [sg.Text(f"Nessun paradigma trovato per {la}, poiché è un")],
              [sg.Text(to, font=(sottotitolo))],
              [sg.Button('Cerca un\'altra parola')],
              [sg.Button('Cerca un\'intera versione'), sg.Button('Chiudi')]]
    window = sg.Window(f'{la} è indeclinabile', layout, icon='icona.ico')
    versione = False
    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Cerca un\'intera versione':
            global parolancora
            parolancora = False
            versione = True
            break
        elif event == 'Cerca un\'altra parola':
            break
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
            sys.exit(0)
    window.close()
    if versione == True: return 'Versione'

def paradigma_window(paradigma, tipo):
    if accenti == False:
        to,pa = rimuovi_accenti(tipo), rimuovi_accenti(paradigma)
    else:
        to,pa = tipo, paradigma
    layout = [[sg.Text(f"Paradigma di", font=(titolo)), sg.Text(pa.split(',')[0], font=(titolograssetto))],
              [sg.HorizontalSeparator()],
              [sg.Text(to,
                       font=(sottotitolo))],
              [sg.Text(pa, font=("Arial 12 bold italic"), key='-PARADIGMA-')],
              [sg.Button('Copia negli appunti'), sg.Button('Cerca un\'altra parola')],
              [sg.Button('Cerca un\'intera versione'), sg.Button('Chiudi')]]
    window = sg.Window(f'Scheda paradigma di {pa.split(",")[0]}', layout, icon='icona.ico')
    versione = False
    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Copia negli appunti':
            clipboard.copy(pa)
            sg.Popup('Paradigma copiato', pa, 'copiato negli appunti')
        elif event == 'Cerca un\'intera versione':
            global parolancora
            parolancora = False
            versione = True
            break
        elif event == 'Cerca un\'altra parola':
            break
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
            sys.exit(0)
    window.close()
    if versione == True: return 'Versione'


def disambigua_window(texts, links, verbs, nome):
    c, radio = 0, []
    for text in texts:
        if verbs[c] == True or verbs[c] == 'True':
            radio.append([sg.Button(text, button_color=('darkslateblue', 'gainsboro'))])
        else:
            radio.append([sg.Button(text, button_color=('darkslategray', 'gainsboro'))])
        c += 1
    layout = [[sg.Text('Seleziona una possibilità di traduzione per', font=(titolo)),
               sg.Text(nome, font=(titolograssetto))]] + radio
    window = sg.Window('Disambiguazione', layout, icon='icona.ico')
    x = None
    while True:  # Event Loop
        event, values = window.Read()
        if event in texts:
            x = links[texts.index(event)]
            break
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
            sys.exit(0)
    window.close()
    return x

def check_disambigua_exists(nome):
    fname = nome + '.disambigua'
    x = temp_html_path / fname
    return x

def pagina_non_esistente_window(nome):
    versione = False
    layout = [[sg.Text('Pagina non esistente', font=(titolograssetto))],
                [sg.Text(f"Nessun risultato trovato per {nome} su dizionario-latino.com")],
                [sg.HorizontalSeparator()],
                [sg.Text("- Per favore, controlla l' ortografia")],
                [sg.Text(
                    "- Se hai cercato più parole insieme, usa l' opzione 'Trova paradigmi di una versione':\ndopo aver incollato il testo, più di 100 parole possono essere scaricate in meno di un minuto.")],
                [sg.HorizontalSeparator()],
                [sg.Button('Cerca un\'altra parola'), sg.Button('Trova paradigmi di una versione'),
                sg.Button('Chiudi')]]
    window = sg.Window(f'Nessun risultato trovato', layout, icon='icona.ico')
    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Trova paradigmi di una versione':
            global parolancora
            parolancora = False
            versione = True
            break
        elif event == 'Cerca un\'altra parola':
            break
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
            sys.exit(0)
    window.close()
    if versione==True:
        return 'Versione'
    else:
        return 'Parola'
    
def disambigua_verb_window(texts, links, verbs, nome, autodisambigua):
    disambiguapath = check_disambigua_exists(nome)
    if disambiguapath.is_file() == False:
        c = 0
        radio = []
        if autodisambigua == 'Yes':
            return links[0]
        for text in texts:
            if verbs[c] == True or verbs[c] == 'True':
                
                radio.append([sg.Button(text, button_color=('darkslateblue', 'gainsboro'))])
            else:
                radio.append([sg.Button(text, button_color=('darkslategray', 'gainsboro'))])
            c += 1
        layout = [[sg.Text('Seleziona una possibilità di traduzione per', font=(titolo)),
                sg.Text(nome, font=(titolograssetto))], [sg.Checkbox('Non chiedere più', default=False, font=(paragrafo), key="ff", pad=(0, 0))]] + radio
        window = sg.Window('Disambiguazione', layout, icon='icona.ico')
        x = None
        verbo = False
        while True:  # Event Loop
            event, values = window.Read()
            if event in texts:
                if values["ff"] == True:
                    with open(disambiguapath, "w") as file:
                        file.write(links[texts.index(event)])
                x = links[texts.index(event)]
                verbo = verbs[texts.index(event)]
                break
            elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
                sys.exit(0)
        window.close()
        if verbo == False:
            return 5 # Codice d'errore se la parola potrebbe avere un paradigma ma non è un verbo
        else:
            return x
    else:
        with open(disambiguapath, "r") as file:
            url = file.read()
        return url


def search_word():
    paradigma = None
    x = None
    while True:
        nome, formeflesse = seleziona_parola()
        fname = parse_filename_from_nome_and_formeflesse(nome, formeflesse)
        path = check_config_file_if_not_exist_download(fname)
        paradigma = analyze_config_file_return_troppe_cose(path)
        if paradigma == 404:
            x = pagina_non_esistente_window(nome)
            break
        elif paradigma != None:
            break
    if x == None:
        if type(paradigma[0]) is list:
            url = disambigua_window(paradigma[0], paradigma[1], paradigma[2], nome)
            fname = parse_filename_from_url(url)
            path = check_config_file_if_not_exist_download(fname)
            paradigma = analyze_config_file_return_troppe_cose(path)
            if paradigma != None and paradigma[0] != None:
                x = paradigma_window(paradigma[0], paradigma[1])
            elif paradigma != None and paradigma[0] is None:
                x = no_paradigma_window(paradigma[1], paradigma[2])
        elif paradigma != None and paradigma[0] != None:
            x = paradigma_window(paradigma[0], paradigma[1])
        elif paradigma != None and paradigma[0] is None:
            x = no_paradigma_window(paradigma[1], paradigma[2])
    if x == 'Versione':
        traduci_versione()


def filter_versione(text):  # Filter a text, leave only words; replace accents and remove text in brackets.
    text = " ".join(text.split()).lower()  # togli spazi extra e salva testo in minuscolo
    text = text.replace('\n', '').replace('.', ' ').replace(',', ' ').replace('«', '').replace('»',
                                                                                               '')  # sostituisci simboli
    text = sub("[\(\[].*?[\)\]]", "", text)  # elimina testo tra parentesi quadre e tonde
    text = "".join(c for c in text if c.isalpha() or c == " ").split()  # lascia solo i caratteri
    return text


def inserisci_testo_versione_window():
    layout = [[sg.Text('Trovaparadigmi da versione', font=(titolo))],
              [sg.HorizontalSeparator()],
              [sg.Text(f"Cerca tutti i verbi presenti in un testo latino,\nper poi estrarne i paradigmi",
                       font=("Arial 14 bold"), text_color="darkslateblue")],
              [sg.Text("Incolla nell'area qui sotto la versione.",
                       font=(sottotitolo))],
              [sg.Multiline(enter_submits=False, size=(60, 5), font=('Arial 10 bold'), autoscroll=True, visible=True,
                            key='testoversione')],
              [sg.Button('Analizza testo', bind_return_key=True), sg.Button('Tutorial su YouTube'),
               sg.Button('Chiudi')]]
    window = sg.Window(f'Trovaparadigmi da Versione', layout, icon='icona.ico')
    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Tutorial su YouTube':
            webbrowser.open('https://bortox.github.io/redirect_youtube_tutorial_trova_versione')
        elif event == 'Analizza testo':
            testocompleto = ""
            for parola in values["testoversione"]:
                testocompleto = testocompleto + parola
            if len(filter_versione(testocompleto)) < 1:
                sg.Popup('Nessuna parola inserita',
                        'Per dover analizzare una versione, ho bisogno del testo latino. Non hai incollato nessuna parola. Se non sai come fare, clicca il pulsante "Tutorial su Youtube" invece di "Analizza Testo".')
            else:
                break
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi':
            sys.exit(0)
    window.close()
    return filter_versione(testocompleto)


def run_download(urllist):
    from download import download
    while True:
        try:
            download(urllist)
            break
        except aiohttp.ClientConnectionError:
            sg.popup('No Internet',
                     'Il tuo computer adesso non è connesso ad internet, quindi non ho potuto finire di scaricare le parole latine rimanenti. Per continuare, appena ti sei riconess@, clicca "OK"')


def buildurllist(formeflesse, listaparole):
    urllist = []
    if formeflesse == False:
        for parola in listaparole:
            urllist.append(baseurl_parola + parola)
    else:
        for parola in listaparole:
            urllist.append(baseurl_parola + parola + '&md=ff')
    return urllist
def buildfnamelist(formeflesse,listaparole):
    flist = []
    if formeflesse == False:
        for parola in listaparole:
            flist.append(parola + '.ini')
    else:
        for parola in listaparole:
            flist.append(parola + '.ff.ini')
    return flist

create_generic_window('Trovaparadigmi', [[sg.Text('Trovaparadigmi per versioni e testi in latino')],
                                         [sg.Button('Chiudi',size=(18,1)), sg.Button('Impostazioni',size=(18,1))],
                                         [sg.Button('Avvia',size=(40,2))],
                                         [sg.Text("Creato da bortox.it (Andrea Bortolotti)", font=("Arial 10"))]], 'Avvia', 'Chiudi','Impostazioni')
parola = cercare_parola()
def file_save_window(paradigmastr):
    nparadigmi = len(paradigmastr.split("\n"))
    layout = [[sg.T('Cartella:')],
              [sg.In(default_text=str(home_path),key='path')],
              [sg.FolderBrowse('Seleziona cartella',target='path',initial_folder=str(home_path))],
              [sg.T('Nome file + estensione:')],
              [sg.InputText(default_text='paradigmi.txt',key='filename')],
              [sg.Text(f'Nel file sarà scritto un paradigma per riga.\Totale: {nparadigmi} righe.', font=("Arial", 10))],
              [sg.OK(),sg.Button('Annulla')]]
    window = sg.Window('Salva paradigmi', layout, finalize=True, icon='icona.ico')
    while True:  # Event Loop
        event, values = window.Read()
        if event == sg.WINDOW_CLOSED or event == 'Annulla':
            break
        elif event == 'OK':
            path = Path(values['path'])/Path(values['filename'])
            f = sanitize_filepath(path,platform='auto')
            try:
                with open(f,'w') as file:
                    file.write(paradigmastr)
                sg.Popup('Fatto!', f'Percorso del file: {f}')
                break
            except IOError as e:
                sg.Popup('Errore nella scrittura', 'Controlla se:\n- Hai il permesso per scrivere nella cartella selezionata e quindi là puoi creare un file.\n- Il file esiste ed è contrassegnato come di sola lettura.\n- Il file è già aperto da un altro programma.')
                window['path'].update(str(home_path))
            except Exception as e:
                sg.Popup('Errore', e)
    window.close()
def final_window(listaparadigmi,numeroparole):
    paradigmistr = '\n'.join(listaparadigmi)
    global accenti
    if accenti == False:
        paradigmistr = rimuovi_accenti(paradigmistr)
    layout = [[sg.Text(f'{len(listaparadigmi)} Paradigmi verbali estratti', font=(titolograssetto))],
                  [sg.Text(f'su {numeroparole} parole totali analizzate')],
                  [sg.Button('Copia negli appunti',size=(40,1))],
                  [sg.Button('Salva su file',size=(40,1))],
                  [sg.Button('Visita il mio sito web',size=(40,1))],
                  [sg.Button('Trovaparadigmi da parola',size=(40,1))],
                  [sg.Button('Trovaparadigmi da versione',size=(40,1))],
                  [sg.Button('Imposta preferenze',size=(40,1))],
                  [sg.Button('Chiudi il programma',size=(40,1))]]
    
    window = sg.Window('Paradigmi estratti', layout, finalize=True, icon='icona.ico')
    altraparola,altraversione = False, False
    while True:  # Event Loop
        event, values = window.Read()
        if event == 'Copia negli appunti':
            if len(paradigmistr) > 0:
                clipboard.copy(paradigmistr)
                sg.Popup('Elenco copiato', f'{len(listaparadigmi)} paradigmi copiati negli appunti. Adesso puoi incollarli.')
            else:
                sg.Popup('Ehy', f'Non è presente nessun paradigma nelle {numeroparole} parole analizzate, la prossima volta prova ad inserire una versione nell\' input di testo!')
        elif event =='Salva su file':
            if len(paradigmistr) > 0:
                file_save_window(paradigmistr)
            else:
                sg.Popup('Ehy', f'Non è presente nessun paradigma nelle {numeroparole} parole analizzate, la prossima volta prova ad inserire una versione nell\' input di testo!')
        elif event == 'Visita il mio sito web':
            webbrowser.open('https://bortox.github.io/')
        elif event == 'Trovaparadigmi da parola':
            altraparola = True
            break
        elif event == 'Trovaparadigmi da versione':
            altraversione = True
            break
        elif event == 'Imposta preferenze':
            check_preferences()
        elif event == sg.WINDOW_CLOSED or event == 'Chiudi il programma':
            sys.exit(0)
    window.close()
    if altraparola == True:
        search_word()
    if altraversione == True:
        traduci_versione()
def traduci_versione():
    testo = inserisci_testo_versione_window()
    global formeflesse
    autodisambigua = sg.PopupYesNo('Disambiguazione automatica',
                                   'Con la disambiguazione automatica risparmierai tempo non scegliendo le varie possibilità, ma potrebbero essere presenti errori nella lista finale dei paradigmi. Usala per risparmiare tempo se ti stufa selezionare diverse opzioni possibili per la traduzione di una parola ( es. se come verbo o nome ).')
    if autodisambigua == 'Yes':
        # non mettere qua global formeflesse perché se uno imposta disambigua e lo vuole rifare senza global resta true.
        formeflesse = False
    urllist = buildurllist(formeflesse, testo)
    flist = buildfnamelist(formeflesse, testo)
    run_download(urllist)
    plist = []
    layout = [[sg.Text('Analisi in corso', font=(titolo))],
                  [sg.Text('Costruzione lista paradigmi.',font=(sottotitolo))],
                  [sg.HorizontalSeparator()],
                  [sg.Text('Inizializzazione...', key='conto', text_color='darkslateblue' , size=(50,1), font=("Arial 15 bold"))],
                  [sg.ProgressBar(1, orientation='h', size=(50, 30), key='progress')
                  ]]
    window = sg.Window('ちょっと待って', layout, finalize=True, icon='icona.ico')
    barra_progresso = window.FindElement('progress')
    conto_fatti = window.FindElement('conto')
    c = 0
    count_paradigmi = 0
    parola_precedente = None
    for fname in flist:
        c += 1
        paradigma = analyze_config_file_return_paradigma(fname,autodisambigua)
        barra_progresso.UpdateBar(c,len(flist)) # parole analizzate
        if type(paradigma) is not int:
            if type(parola_precedente) is not int and paradigma == 'sum, es, fui, esse' and smartest == True:
                pass # In questo caso il verbo essere avrà funzione di ausiliare, quindi non includiamolo nella lista dei paradigmi, sarebbe stupido
            else:
                plist.append(paradigma)
                count_paradigmi += 1
                conto_fatti.update(f"{c} parole analizzate su {len(flist)}, {count_paradigmi} paradigmi estratti.")
        parola_precedente = paradigma
        window.set_title(f'Trovati {len(plist)} paradigmi')
    window.close()
    final_window(plist,c)
if parola == True:
    while parolancora == True:
        search_word()
elif parola == False:
    traduci_versione()
