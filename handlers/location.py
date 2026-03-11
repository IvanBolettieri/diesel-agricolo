from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.geocoding import search_location
from handlers.keyboards import get_main_menu

async def handle_text_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce l'input testuale dell'utente per cercare una città"""
    query = update.message.text
    
    # Feedback immediato all'utente
    wait_msg = await update.message.reply_text(f"🔍 Cerco '{query}'...")
    
    results = await search_location(query)
    
    if not results:
        await wait_msg.edit_text("❌ Nessuna località trovata. Riprova con un nome più specifico.")
        return

    keyboard = []
    for place in results:
        # Creiamo un identificativo breve per il callback: "LOC|lat|lon"
        lat = place.get('lat')
        lon = place.get('lon')
        display_name = place.get('display_name').split(',')[0] # Prendiamo solo la prima parte del nome
        
        # Callback data deve essere stringa e corta
        callback_data = f"LOC|{lat}|{lon}"
        
        keyboard.append([InlineKeyboardButton(f"📍 {place.get('display_name')}", callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await wait_msg.edit_text("Ho trovato questi risultati, clicca su quello corretto:", reply_markup=reply_markup)

async def handle_gps_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la posizione GPS inviata direttamente dall'utente"""
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    
    context.user_data['latitude'] = lat
    context.user_data['longitude'] = lon
    
    await update.message.reply_text(
        f"✅ Posizione GPS acquisita!\nCoordinate: {lat:.4f}, {lon:.4f}",
        reply_markup=get_main_menu()
    )

async def confirm_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il click sul bottone della località"""
    query = update.callback_query
    await query.answer() # Conferma a Telegram che abbiamo ricevuto il click
    
    data = query.data
    if data.startswith("LOC|"):
        _, lat, lon = data.split("|")
        
        # Salviamo la posizione nei dati utente (user_data) per usarla dopo
        context.user_data['latitude'] = lat
        context.user_data['longitude'] = lon
        
        # Modifichiamo il messaggio originale per confermare
        await query.edit_message_text(
            f"✅ Posizione impostata!\n"
            f"Coordinate: {lat}, {lon}\n"
            f"Ora userò questa posizione per cercare i benzinai."
        )
        
        # Inviamo un nuovo messaggio per mostrare il menu (perché edit_message_text non può mostrare una ReplyKeyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Cosa vuoi fare adesso?", reply_markup=get_main_menu())