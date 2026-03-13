import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_BOT_TOKEN
from handlers.commands import start, posizione, info_bot, menu_principale
from handlers.location import handle_text_location, confirm_location, handle_gps_location
from handlers.fuel import find_gas_stations, show_fuel_menu, set_fuel_benzina, set_fuel_diesel
from database import init_db

# Configurazione base del logging per vedere errori e info nel terminale
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Errore: Token non trovato. Controlla il file .env")
        exit(1)

    # Inizializzazione Database
    import asyncio
    asyncio.run(init_db())

    # Creazione dell'applicazione
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Aggiunta del gestore per il comando /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler('posizione', posizione))
    
    # Gestione Menu Principale (Testo esatto dei pulsanti)
    # Usiamo il regex ^...$ per assicurarci che coincida esattamente con il testo del bottone
    application.add_handler(MessageHandler(filters.Regex("^📍 Imposta Posizione$"), posizione))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ Info$"), info_bot))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Menu Principale$"), menu_principale))
    
    # Gestione Impostazioni Carburante
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Carburante$"), show_fuel_menu))
    application.add_handler(MessageHandler(filters.Regex("^🟢 Benzina$"), set_fuel_benzina))
    application.add_handler(MessageHandler(filters.Regex("^⚫ Diesel$"), set_fuel_diesel))
    
    # Gestione Posizione GPS (L'allegato di tipo Location)
    application.add_handler(MessageHandler(filters.LOCATION, handle_gps_location))
    
    # Gestione Cerca Benzinai
    application.add_handler(MessageHandler(filters.Regex("^⛽ Cerca Benzinai$"), find_gas_stations))
    
    # Gestione messaggi di testo (per la ricerca città)
    # Filtriamo via i comandi (che iniziano con /) per evitare conflitti
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_location))
    
    # Gestione dei click sui bottoni (Callback)
    application.add_handler(CallbackQueryHandler(confirm_location, pattern=r"^LOC\|"))

    print("Bot avviato... Premi Ctrl+C per fermarlo.")
    application.run_polling()