# Trovaparadigmi

Una GUI Python per trovare in modo semplice e veloce i paradigmi dei verbi da un testo latino

---

## Obiettivo

Fornire a tutti un’opzione più o meno precisa per **trovare rapidamente i paradigmi di un’intera versione in latino**, e salvarli in un documento di testo.

Sostanzialmente, **risparmiare tempo** alle persone che in ogni caso copierebbero i paradigmi dal Dizionario Online Olivetti.



## Scaricare

Potete scaricare l'[applicazione in formato .exe per Windows dalla landing page](https://bortox.github.io/trovaparadigmi)

## Compilare

> Se non sapete cosa vuol dire compilare, lasciate perdere e contattemi via mail a bort0x@tuta.io

Se vi interessa usare l'app su **Linux** o **Mac**, allora dovrete compilarla: le cose si fanno un po' più difficili. 

Inoltre, se non vi interessa, potete anche compilare l'app per Windows, nel modo in cui ho creato l' exe.

### Compilare su Windows

1. Installiamo [Python3 dal sito ufficiale](https://www.python.org/downloads/)

2. Installiamo [git](https://git-scm.com/downloads)

3. Apriamo Powershell oppure [Windows Terminal](https://www.microsoft.com/en-us/p/windows-terminal/9n0dx20hk701)

```powershell
pip3 install -r requirements.txt
pip3 install PyInstaller
```

4. Creiamo l'eseguibile dell'app con PyInstaller

```powershell
python3 -m PyInstaller --clean --onefile --windowed --icon="C:\full_path_to\icona.ico" gui.py
```

Adesso, aprendo l'eseguibile gui.exe nella cartella dist, possiamo avviare l'app.

5. Per creare un installer che aggiungerà la nostra app al Desktop ed al menù Start ci serviremo di [Inno Setup](https://jrsoftware.org/isdl.php#stable). Ecco come fare:
   
   - Apri Inno Setup Compiler
   
   - Clicca su **File** e sull' opzione **New** del menù aperto
   
   - Si dovrebbe aprire una finestra con scritto *Welcome to the Inno Setup Script Wizard*, clicca **Next**
   
   - **Inserisci** nome, versione, autore e sito web dell' app (Trovaparadigmi, 1.0, Andrea Bortolotti, bortox.it/trovaparadigmi), poi clicca **Next**
   
   - Nella finestra successiva, titolata **Application Folder**, possiamo cliccare **Next**
   
   - Nella finestra **Application files** seleziona gui.exe generato precedentemente da PyInstaller (./trovaparadigmi/dist/gui.exe), come *Other Application Files* scegli icona.ico e download.ico ( servono per le icone delle finestre ), presenti nella cartella del programma scaricato.
   
   - Non associare alcuna estensione alla app, deseleziona **Associate a file type to the main executable**.
   
   - **Application Shortcuts**: qui seleziona cosa preferisci, io li ho lasciati entrambi attivi
   
   - **Application Documentation**: ancora non ho creato una guida, come licenza scegli **LICENSE.md** nella cartella del programma( in ogni caso la licenza è la aGPL v3)
   
   - **Install mode**: consiglio la Non administrative install mode, non serve che la mia app sia una di sistema.
   
   - **Languages** la sezione si descrive da sé. Seleziona una o più lingue da usare nell' installazione.
   
   - **Compiler settings**: qua ho impostato solo un *Custom setup icon file*, ossia l' icona del file .exe prodotto ( icona.ico )
   
   - **Inno setup preprocessor**: studierò meglio cosa significa. Potete semplicemente cliccare su *Next*.
   
   - Adesso avete generato uno script. Rispondete *Sì* a *Would you like to compile the script now?* per avere subito l' .exe nella cartella \Output. 
   
   - Fatto!



## Compilare su Linux ( Debian based )

WIP 🚧

## Compilare su MacOS

WIP 🚧

---

Spero che questo programma vi faccia risparmiare tempo! Se avete qualche idea di miglioramento, siete liberi di aprire un _pull request_.




