import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu
from database import get_user

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting_for_location'] = False
    await update.message.reply_text(
        "Ciao! Sono il tuo bot per i prezzi carburante.\nUsa il menu qui sotto per navigare.",
        reply_markup=get_main_menu()
    )

async def posizione(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Attiviamo la modalità "Attesa input località"
    context.user_data['waiting_for_location'] = True
    
    # Controlliamo se esiste già una posizione salvata
    user = await get_user(update.effective_user.id)

    if user:
        logger.info(f"👤 DATI UTENTE DAL DB -> ID: {user.id} | Lat: {user.latitude} | Lon: {user.longitude} | Fuel: {user.fuel_type}")
    else:
        logger.info(f"👤 UTENTE NON TROVATO NEL DB: ID={update.effective_user.id}")
    
    status_msg = ""
    if user and user.latitude and user.longitude:
        citta = user.location_name if getattr(user, 'location_name', None) else "Non definita"
        status_msg = f"✅ **POSIZIONE ATTUALE:**\nCittà: {citta}\nLat: {user.latitude:.4f}\nLon: {user.longitude:.4f}\n\n"
    else:
        status_msg = "🚫 **NESSUNA POSIZIONE SALVATA!** 🚫\n_Devi assolutamente impostarne una per cercare i benzinai._\n\n"

    # Creiamo un tasto che richiede la posizione all'utente
    # Aggiungiamo anche un tasto "Annulla" per tornare al menu
    keyboard = [
        [KeyboardButton("📍 Invia posizione attuale", request_location=True)],
        [KeyboardButton("🔙 Menu Principale")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"{status_msg}Per impostare o cambiare zona puoi:\n"
        "1. Cliccare il pulsante qui sotto per inviare il GPS\n"
        "2. Scrivere direttamente il nome della tua città (es. 'Matera')",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def info_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Diesel Agric Bot*\nVersione 1.0\n\nQuesto bot ti aiuta a trovare i prezzi migliori per il carburante nella tua zona, mostrandoti solo il carburante che hai selezionato da menù, attualmente gli unici carburanti  filtrati sono il diesel e benzina self.",
        parse_mode="Markdown"
    )

async def menu_principale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Funzione per tornare al menu principale"""
    context.user_data['waiting_for_location'] = False
    await update.message.reply_text("Menu principale:", reply_markup=get_main_menu())