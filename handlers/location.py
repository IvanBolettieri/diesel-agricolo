import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.geocoding import search_location
from handlers.keyboards import get_main_menu
from database import update_user_location

logger = logging.getLogger(__name__)

async def handle_text_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce l'input testuale dell'utente per cercare una città"""
    
    # Se non stiamo aspettando una posizione (l'utente non ha cliccato "Imposta Posizione"), ignoriamo il messaggio
    if not context.user_data.get('waiting_for_location'):
        return

    query = update.message.text
    
    # Feedback immediato all'utente
    wait_msg = await update.message.reply_text(f"🌍  _Sto cercando \"{query}\"..._")
    logging.info(f"🔍 Ricerca località per User {update.effective_user.id}: '{query}'")
    results = await search_location(query)
    
    if not results:
        await wait_msg.edit_text("❌  *Località non trovata.*\nProva a scrivere il nome in modo più specifico (es. _Matera, Basilicata_).", parse_mode="Markdown")
        return

    keyboard = []
    for place in results:
        # FILTRO ANTI-DUPLICATI: Saltiamo le province ("county")
        # L'utente vuole vedere solo città/comuni e non l'area amministrativa provinciale
        if place.get('addresstype') == 'county':
            continue

        # Creiamo un identificativo breve per il callback: "LOC|lat|lon"
        lat = place.get('lat')
        lon = place.get('lon')
        
        # Prendiamo le prime 2 parti del nome per dare più contesto ed evitare duplicati visivi
        # Esempio: Invece di "Matera", mostrerà "Matera, Basilicata"
        parts = place.get('display_name', '').split(',')
        label_name = ", ".join(parts[:2]).strip()
        
        # Icona in base al tipo di luogo
        p_class = place.get('class', '')
        p_type = place.get('type', '')
        
        if p_class == 'place' and p_type in ('city', 'town', 'village'):
            icon = "🏙️"
        elif p_class == 'boundary':
            icon = "🗺️"
        else:
            icon = "📍"
        
        # Callback data deve essere stringa e corta
        callback_data = f"LOC|{lat}|{lon}"
        
        keyboard.append([InlineKeyboardButton(f"{icon} {label_name}", callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await wait_msg.edit_text("👇  *Ho trovato questi risultati:*\n_Clicca su quello corretto per confermare._", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_gps_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la posizione GPS inviata direttamente dall'utente"""
    try:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        
        await update_user_location(update.effective_user.id, lat, lon, "📍 Posizione GPS")
        # Abbiamo ottenuto la posizione, smettiamo di ascoltare
        context.user_data['waiting_for_location'] = False
        
        await update.message.reply_text(
            "✅  *Posizione Acquisita!*\n\n"
            "🛰️  *Rilevamento GPS completato*\n"
            f"🌐  `{lat:.4f}, {lon:.4f}`\n"
            "_Tutto pronto per cercare i benzinai._",
            parse_mode="Markdown"
        )
        
        # Mostriamo la mappa per conferma visiva
        await context.bot.send_location(chat_id=update.effective_chat.id, latitude=lat, longitude=lon)
        
        # Mostriamo il menu
        await update.message.reply_text("👇 Usa il menu per continuare:", reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"❌ ERRORE GPS: {e}")
        await update.message.reply_text(
            "❌  *Errore di sistema*\n"
            "Non sono riuscito a salvare la tua posizione.\n"
            "_Consiglio: Riprova tra qualche minuto o contatta l'amministratore._",
            parse_mode="Markdown"
        )

async def confirm_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logging.info(f"📍 Callback Posizione ricevuta: {update, context}")
    """Gestisce il click sul bottone della località"""
    query = update.callback_query
    await query.answer() # Conferma a Telegram che abbiamo ricevuto il click
    
    data = query.data
    logger.info(f"📍 Callback Posizione ricevuta: {data}")

    if data.startswith("LOC|"):
        _, lat, lon = data.split("|")
        
        # Recuperiamo il nome del luogo dal bottone cliccato
        location_name = "Posizione selezionata"
        if query.message and query.message.reply_markup:
            for row in query.message.reply_markup.inline_keyboard:
                for btn in row:
                    if btn.callback_data == data:
                        # Rimuoviamo le icone se presenti per avere solo il nome pulito
                        location_name = btn.text.replace("📍 ", "").replace("🏙️ ", "").replace("🗺️ ", "")
                        break

        logger.info(f"💾 Salvataggio Coordinate per User {update.effective_user.id}: Luogo='{location_name}' | Lat={lat}, Lon={lon}")
        # Salviamo la posizione nel DB
        await update_user_location(update.effective_user.id, float(lat), float(lon), location_name)
        # Abbiamo impostato la posizione, smettiamo di ascoltare
        context.user_data['waiting_for_location'] = False
        
        # Modifichiamo il messaggio originale per confermare
        await query.edit_message_text(
            f"✅  *Posizione Salvata!*\n\n"
            f"📍  **{location_name}**\n"
            f"_Tutto pronto per cercare i benzinai._",
            parse_mode="Markdown"
        )
        
        # Invia la mappa visiva per confermare all'utente dove ha piazzato il pin
        await context.bot.send_location(chat_id=update.effective_chat.id, latitude=float(lat), longitude=float(lon))
        
        # Inviamo un nuovo messaggio per mostrare il menu (perché edit_message_text non può mostrare una ReplyKeyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="👇 Usa il menu per continuare:", reply_markup=get_main_menu())