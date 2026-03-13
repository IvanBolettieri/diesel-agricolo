# Diesel Agric Bot - Trova Prezzi Carburante

Un Bot Telegram avanzato scritto in Python che permette di trovare i distributori di carburante più economici nelle vicinanze, utilizzando i dati ufficiali del **MIMIT (Ministero delle Imprese e del Made in Italy)** e la geolocalizzazione di **OpenStreetMap**.

## ✨ Funzionalità Principali

*   **📍 Geolocalizzazione Intelligente:**
    *   Supporta la **Posizione GPS** in tempo reale inviata da Telegram.
    *   Supporta la ricerca testuale della città (es. "Grassano", "Matera").
    *   Filtra automaticamente le province per mostrare solo i comuni rilevanti.
*   **⛽ Ricerca Prezzi Aggiornati:**
    *   Trova i distributori nel raggio di **5 km**.
    *   Mostra i prezzi per **Diesel** e **Benzina**.
    *   Indica se il servizio è **Self** o **Servito**.
    *   Ordina i risultati per **Prezzo** (dal più basso) e per **Recenza dati** (ultimo aggiornamento).
*   **⭐ Gestione Preferiti:**
    *   Salva i tuoi distributori di fiducia.
    *   Controlla rapidamente i prezzi dei preferiti senza dover ricercare la posizione.
*   **⚙️ Impostazioni Personalizzate:**
    *   Memorizza la preferenza del carburante (Diesel o Benzina) per ogni utente.
    *   Memorizza l'ultima posizione cercata.
*   **🗺️ Navigazione:**
    *   Link diretto a **Google Maps** per avviare la navigazione verso il distributore.

---

## 🛠️ Requisiti Tecnici

*   Python 3.9 o superiore
*   Un Token Bot Telegram (ottenibile da [@BotFather](https://t.me/BotFather))

### Librerie Python
Le dipendenze principali sono:
*   `python-telegram-bot` (Interazione con Telegram)
*   `sqlalchemy` + `aiosqlite` / `asyncpg` (Gestione Database asincrono)
*   `aiohttp` (Chiamate API REST)

---

## 🚀 Installazione

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/tuo-username/diesel-agric-bot.git
    cd diesel-agric-bot
    ```

2.  **Crea un ambiente virtuale (consigliato):**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installa le dipendenze:**
    Crea un file `requirements.txt` (se non ce l'hai già) con questo contenuto:
    ```text
    python-telegram-bot
    sqlalchemy
    aiosqlite
    aiohttp
    python-dotenv
    ```
    E poi installale:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurazione Variabili d'Ambiente:**
    Crea un file `.env` nella cartella principale e inserisci i tuoi dati:
    ```env
    TELEGRAM_BOT_TOKEN=il_tuo_token_qui
    DATABASE_URL=sqlite+aiosqlite:///bot.db
    # Oppure per Postgres: postgresql+asyncpg://user:pass@host/dbname
    ```

5.  **Avvia il Bot:**
    ```bash
    python main.py
    ```

---

## 📱 Guida all'Uso

Una volta avviato il bot su Telegram:

1.  **Avvio:** Premi `/start`. Il bot inizializzerà il database se necessario.
2.  **Imposta Posizione:**
    *   Clicca su **📍 Imposta Posizione**.
    *   Puoi inviare la tua posizione attuale tramite la graffetta 📎 di Telegram.
    *   Oppure scrivere il nome della città.
3.  **Scegli Carburante:**
    *   Vai su **⚙️ Carburante** per scegliere tra Diesel (default) o Benzina.
4.  **Cerca:**
    *   Clicca su **⛽ Cerca Benzinai**.
    *   Il bot mostrerà i 5 risultati migliori ordinati per prezzo.
5.  **Preferiti:**
    *   Sotto ogni risultato della ricerca trovi un tasto **⭐ Salva**.
    *   Accedi alla lista dei salvati dal menu principale cliccando su **⭐ Preferiti**.

---

## 📂 Struttura del Progetto

*   `main.py`: Punto di ingresso. Configura il bot e gli handler.
*   `database.py`: Gestione del DB (SQLite/Postgres), modelli User e Favorite.
*   `config.py`: Gestione delle variabili d'ambiente.
*   `handlers/`: Contiene la logica di risposta ai comandi.
    *   `commands.py`: /start, menu principale.
    *   `location.py`: Gestione GPS e ricerca città (Nominatim).
    *   `fuel.py`: Ricerca prezzi e gestione preferiti.
*   `services/`:
    *   `fuel_api.py`: Interfaccia con l'API del MISE.
    *   `geocoding.py`: Interfaccia con OpenStreetMap.

---

## ⚠️ Disclaimer

I dati sui prezzi dei carburanti sono forniti dall'**Osservatorio Prezzi Carburanti** del MIMIT. Il bot funge da interfaccia di consultazione e non è responsabile per eventuali inesattezze nei prezzi o negli orari mostrati dai distributori.

---

**Sviluppato con ❤️ e Python.**
