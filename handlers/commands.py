import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu
from database import get_user

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting_for_location'] = False
    await update.message.reply_text(
        "👋 *Benvenuto su Diesel Agric Bot!*\n\n"
        "👇 *Usa il menu qui sotto per iniziare:*",
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
        status_msg = (
            "📍 *TU SEI QUI:*\n"
            f"🏙️  *{citta}*\n"
            f"🌐  `{user.latitude:.4f}, {user.longitude:.4f}`\n"
            "──────────────────\n"
        )
        # Mostra la mappa della posizione salvata
        await context.bot.send_location(chat_id=update.effective_chat.id, latitude=user.latitude, longitude=user.longitude)
    else:
        status_msg = "⚠️ *ATTENZIONE: Nessuna posizione impostata!*\n_Per cercare i prezzi, devo sapere dove ti trovi._\n\n"

    # Creiamo un tasto che richiede la posizione all'utente
    # Aggiungiamo anche un tasto "Annulla" per tornare al menu
    keyboard = [
        [KeyboardButton("📍 Invia posizione attuale", request_location=True)],
        [KeyboardButton("🔙 Menu Principale")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"{status_msg}🎯 *Vuoi cambiare zona?*\n\n"
        "1️⃣  Clicca il tasto *Invia posizione attuale*\n"
        "2️⃣  Oppure scrivi il *nome della tua città* (es. _Matera_)",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def info_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️  *INFO BOT*\n\n"
        "🛠  *Versione:* 1.0\n"
        "⛽  *Carburanti:* Diesel & Benzina\n\n"
        "Questo bot ti aiuta a risparmiare trovando i distributori più economici e aggiornati vicino a te.\n"
        "_I dati sono forniti dall'Osservatorio Carburanti del MIMIT._",
        parse_mode="Markdown"
    )

async def menu_principale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Funzione per tornare al menu principale"""
    context.user_data['waiting_for_location'] = False
    await update.message.reply_text("🏠 *Menu Principale*", reply_markup=get_main_menu(), parse_mode="Markdown")