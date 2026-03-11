from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono il tuo bot per i prezzi carburante.\nUsa il menu qui sotto per navigare.",
        reply_markup=get_main_menu()
    )

async def posizione(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Creiamo un tasto che richiede la posizione all'utente
    # Aggiungiamo anche un tasto "Annulla" per tornare al menu
    keyboard = [
        [KeyboardButton("📍 Invia posizione attuale", request_location=True)],
        [KeyboardButton("🔙 Menu Principale")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Per trovare i benzinai vicini puoi:\n"
        "1. Cliccare il pulsante qui sotto per inviare il GPS\n"
        "2. Scrivere direttamente il nome della tua città (es. 'Matera')",
        reply_markup=reply_markup
    )

async def info_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Diesel Agric Bot*\nVersione 1.0\n\nQuesto bot ti aiuta a trovare i prezzi migliori per il carburante nella tua zona.",
        parse_mode="Markdown"
    )

async def menu_principale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Funzione per tornare al menu principale"""
    await update.message.reply_text("Menu principale:", reply_markup=get_main_menu())