import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from services.fuel_api import search_fuel_stations
from handlers.keyboards import get_main_menu, get_fuel_menu
from database import get_user, update_user_fuel, add_favorite, get_user_favorites, delete_favorite

logger = logging.getLogger(__name__)

async def find_gas_stations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la ricerca dei benzinai basata sulla posizione salvata nel DB"""
    
    user_id = update.effective_user.id
    user = await get_user(user_id)

    # 1. Se l'utente non esiste o non ha posizione, avvisiamo
    if not user or not user.latitude or not user.longitude:
        await update.message.reply_text(
            "⚠️ Non so dove sei! Per favore clicca su '📍 Imposta Posizione' nel menu.",
            reply_markup=get_main_menu()
        )
        return

    lat = user.latitude
    lon = user.longitude

    # Log posizione di partenza ricerca
    logger.info(f"⛽ RICERCA START | User: {user_id} | Luogo: {user.location_name} | Coord: {lat}, {lon}")

    # Recuperiamo il tipo carburante (Default: 2-1 che è Diesel/Gasolio, 1-1 è Benzina)
    fuel_type = user.fuel_type if user.fuel_type else "2-1"
    fuel_label = "Diesel" if fuel_type == "2-1" else "Benzina"

    await update.message.reply_text(f"🔎  _Analisi prezzi {fuel_label} in corso..._", parse_mode="Markdown")

    # 3. Chiamiamo l'API
    response = await search_fuel_stations(float(lat), float(lon), radius=5, fuel_type=fuel_type)

    if not response:
        await update.message.reply_text("❌  *Servizio momentaneamente non disponibile.*\nRiprova tra poco.")
        return

    # Gestione della risposta: l'API a volte restituisce un dict con chiave 'results', a volte una lista diretta
    if isinstance(response, dict):
        results = response.get('results', [])
    elif isinstance(response, list):
        results = response
    else:
        results = []
    
    if not results:
        await update.message.reply_text("😕  *Nessun distributore trovato.*\nProva ad aumentare il raggio spostandoti o cambiando città.")
        return

    # 4. Formattiamo i risultati (Prendiamo i primi 5 più economici)
    message = f"🏆  *MIGLIORI PREZZI: {fuel_label.upper()}*\n_Nel raggio di 5 km_\n\n"
    
    # Filtriamo manualmente i risultati > 5km (usiamo 'or 999' per gestire casi in cui distance è None/Null)
    valid_stations = [s for s in results if float(s.get('distance') or 999) <= 5.0]
    
    # Determiniamo l'ID numerico del carburante (1 = Benzina, 2 = Diesel) basandoci sulla stringa '1-x' o '2-x'
    target_fuel_id = 1 if fuel_type.startswith('1') else 2

    # --- ORDINAMENTO AVANZATO ---
    # Creiamo una lista temporanea con i dati necessari per l'ordinamento
    stations_to_sort = []
    for s in valid_stations:
        # Calcoliamo il prezzo minimo per questo benzinaio (per ordinare)
        fuels = [f for f in s.get('fuels', []) if f.get('fuelId') == target_fuel_id]
        
        # FILTRO COERENZA: Se il distributore non ha il carburante richiesto, lo scartiamo subito
        if not fuels:
            continue
            
        min_price = min((f.get('price', 999) for f in fuels), default=999)
        
        # Convertiamo la data in timestamp per ordinare (0 se non valida)
        try:
            dt = datetime.fromisoformat(s.get('insertDate', ''))
            ts = dt.timestamp()
        except:
            ts = 0
        stations_to_sort.append({'data': s, 'price': min_price, 'ts': ts})

    # Ordina per Prezzo Crescente (x['price']) e poi per Data Decrescente (-x['ts'])
    stations_to_sort.sort(key=lambda x: (x['price'], -x['ts']))

    # Prendiamo i primi 5 risultati ordinati
    final_list = stations_to_sort[:5]
    
    for idx, item in enumerate(final_list, 1):
        station = item['data']
        
        # Cerchiamo nella lista 'fuels' le voci che corrispondono al carburante scelto
        fuels_list = station.get('fuels', [])
        matching_fuels = [f for f in fuels_list if f.get('fuelId') == target_fuel_id]
        
        # Formattazione Data Aggiornamento
        insert_date = station.get('insertDate', '')
        try:
            # Converte la stringa ISO (es. 2026-03-11T07:32:44+01:00) in formato leggibile
            dt_obj = datetime.fromisoformat(insert_date)
            date_str = dt_obj.strftime("%d/%m/%Y %H:%M")
        except:
            date_str = "N/D"

        brand = station.get('brand', 'Sconosciuto')
        name = station.get('name', '').title() # Mette la maiuscola alle parole
        
        message += f"{idx}️⃣  ⛽  *{brand}*\n_{name}_\n"
        
        if matching_fuels:
            # Ordiniamo per prezzo e mostriamo tutte le opzioni (es. Self e Servito)
            matching_fuels.sort(key=lambda x: x.get('price', 999))
            for f in matching_fuels:
                price_val = f.get('price')
                is_self = f.get('isSelf', False)
                type_label = "🟢 Self" if is_self else "🤵 Servito"
                message += f"   {type_label}:  💶 *{price_val:.3f} €*\n"
        else:
            message += f"   🚫 Prezzo non disponibile\n"
            
        message += f"   📅 {date_str}  |  📏 {float(station.get('distance', 0)):.1f} km"

        # Link Google Maps per navigazione
        loc = station.get('location', {})
        if loc and 'lat' in loc and 'lng' in loc:
            message += f"\n   🗺️  [Apri Mappa e Naviga](https://www.google.com/maps/dir/?api=1&destination={loc['lat']},{loc['lng']})"
        
        message += "\n──────────────────\n"

    # Creiamo i bottoni per salvare nei preferiti
    # I callback data saranno: SAV|lat|lon|station_id
    keyboard = []
    for idx, item in enumerate(final_list, 1):
        st = item['data']
        st_id = st.get('id')
        lat = st.get('location', {}).get('lat')
        lon = st.get('location', {}).get('lng')
        brand = st.get('brand', 'Distributore')
        
        callback_data = f"SAV|{lat:.6f}|{lon:.6f}|{st_id}"
        # Pulsanti verticali con il nome del brand per una associazione più chiara
        keyboard.append([InlineKeyboardButton(f"⭐ Salva {brand} ({idx})", callback_data=callback_data)])
        
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

async def show_fuel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra il menu per scegliere il carburante"""
    user = await get_user(update.effective_user.id)
    current = user.fuel_type if user and user.fuel_type else "2-1"
    
    label = "Diesel" if current == "2-1" else "Benzina"
    
    await update.message.reply_text(
        f"⚙️  *IMPOSTAZIONI CARBURANTE*\n\n"
        f"Attualmente cerchi: *{label}*\n"
        "👇 _Seleziona la tua preferenza:_",
        reply_markup=get_fuel_menu(),
        parse_mode="Markdown"
    )

async def set_fuel_benzina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imposta Benzina (codice 1-1)"""
    await update_user_fuel(update.effective_user.id, '1-1')
    await update.message.reply_text(
        "✅  *Configurazione Aggiornata*\n\n"
        "Hai impostato: 🟢 **BENZINA**",
        reply_markup=get_main_menu(), parse_mode="Markdown")

async def set_fuel_diesel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imposta Diesel (codice 2-1)"""
    await update_user_fuel(update.effective_user.id, '2-1')
    await update.message.reply_text(
        "✅  *Configurazione Aggiornata*\n\n"
        "Hai impostato: ⚫ **DIESEL**",
        reply_markup=get_main_menu(), parse_mode="Markdown")

async def save_favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Salva un preferito quando si clicca sul bottone"""
    query = update.callback_query
    await query.answer()
    
    data = query.data # SAV|lat|lon|id
    _, lat, lon, st_id = data.split('|')
    
    try:
        # Recuperiamo l'utente per usare il filtro carburante corretto
        user = await get_user(update.effective_user.id)
        fuel_type = user.fuel_type if user else "2-1"
        
        # Aumentiamo il raggio a 5km per essere sicuri di ritrovare la stazione
        response = await search_fuel_stations(float(lat), float(lon), radius=5, fuel_type=fuel_type)
        
        target_station = None
        if response:
            results = response if isinstance(response, list) else response.get('results', [])
            for s in results:
                if str(s.get('id')) == str(st_id):
                    target_station = s
                    break
        
        if target_station:
            brand = target_station.get('brand', 'Distributore')
            name = target_station.get('name', 'Sconosciuto').title()
            
            success = await add_favorite(update.effective_user.id, int(st_id), name, brand, float(lat), float(lon))
            if success:
                await query.message.reply_text(f"⭐ *{brand}* ({name})\n✅ Aggiunto ai tuoi preferiti!", parse_mode="Markdown")
            else:
                await query.message.reply_text(f"⚠️ Questo distributore è già nei tuoi preferiti.")
        else:
            await query.message.reply_text("❌ Impossibile recuperare i dati del distributore (non trovato).")
            
    except Exception as e:
        logger.error(f"❌ ERRORE SALVATAGGIO PREFERITO: {e}")
        await query.message.reply_text(
            "❌ *Errore di sistema*\n"
            "Non sono riuscito a salvare il preferito.\n"
            "_Suggerimento: Se hai appena aggiornato il bot, chiedi all'admin di cancellare il file bot.db_",
            parse_mode="Markdown"
        )

async def show_favorites_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra la lista dei preferiti salvati"""
    try:
        favorites = await get_user_favorites(update.effective_user.id)
    except Exception as e:
        logger.error(f"❌ ERRORE LISTA PREFERITI: {e}")
        await update.message.reply_text("❌ Errore nel recupero dei preferiti. Database non aggiornato?")
        return
    
    if not favorites:
        await update.message.reply_text(
            "⭐ *Nessun preferito salvato.*\n\n"
            "Quando cerchi i benzinai, clicca su '⭐ Salva' sotto i risultati per aggiungerli qui.",
            parse_mode="Markdown"
        )
        return

    keyboard = []
    for fav in favorites:
        # Bottone per controllare: CHK|lat|lon|station_id
        # Bottone per cancellare: DEL|db_id
        btn_check = InlineKeyboardButton(f"🔎 {fav.brand} - {fav.name[:15]}...", callback_data=f"CHK|{fav.latitude}|{fav.longitude}|{fav.station_id}")
        btn_del = InlineKeyboardButton("❌", callback_data=f"DEL|{fav.id}")
        keyboard.append([btn_check, btn_del])

    await update.message.reply_text(
        "⭐ *I TUOI PREFERITI*\n_Clicca sul nome per vedere il prezzo aggiornato:_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_favorite_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il click nella lista preferiti (Controllo o Cancellazione)"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("DEL|"):
        fav_id = int(data.split('|')[1])
        await delete_favorite(fav_id)
        await query.answer("🗑️ Preferito rimosso!")
        # Ricarica la lista aggiornata
        await query.message.delete()
        await show_favorites_list(update, context)
        
    elif data.startswith("CHK|"):
        await query.answer("🔄 Controllo prezzi...")
        _, lat, lon, st_id = data.split('|')
        
        # Simuliamo una ricerca su quel singolo benzinaio
        # Usiamo raggio piccolissimo (1km) sulle sue coordinate esatte
        
        # Impostiamo temporaneamente le coordinate utente per questa ricerca (hack visivo)
        user = await get_user(update.effective_user.id)
        fuel_type = user.fuel_type if user else "2-1"
        
        # Chiamata API manuale
        response = await search_fuel_stations(float(lat), float(lon), radius=1, fuel_type=fuel_type)
        
        # Qui potremmo riusare la logica di visualizzazione, ma per semplicità rimandiamo un messaggio dedicato
        # O semplicemente chiamiamo find_gas_stations con le coordinate truccate?
        # Meglio chiamare find_gas_stations passandogli context modificati o copiando la logica.
        # Per non duplicare troppo codice, salviamo temporaneamente le coordinate nel DB e chiamiamo la funzione standard?
        # No, l'utente non vuole perdere la sua posizione "di casa".
        
        # Facciamo una visualizzazione rapida qui
        target = None
        if response:
            res_list = response if isinstance(response, list) else response.get('results', [])
            for s in res_list:
                if str(s.get('id')) == str(st_id):
                    target = s
                    break
        
        if target:
            # Ricostruzione rapida messaggio prezzo
            fuel_label = "Diesel" if fuel_type == "2-1" else "Benzina"
            target_fuel_id = 1 if fuel_type.startswith('1') else 2
            
            fuels = [f for f in target.get('fuels', []) if f.get('fuelId') == target_fuel_id]
            fuels.sort(key=lambda x: x.get('price', 999))
            
            msg = f"⭐ *{target.get('brand')}*\n_{target.get('name', '').title()}_\n\n"
            if fuels:
                for f in fuels:
                    p = f.get('price')
                    t = "🟢 Self" if f.get('isSelf') else "🤵 Servito"
                    msg += f"{t}:  💶 *{p:.3f} €*\n"
            else:
                msg += "⚠️ Prezzo non disponibile per il carburante selezionato."
                
            # Data
            try:
                dt = datetime.fromisoformat(target.get('insertDate', ''))
                d_str = dt.strftime("%d/%m/%Y %H:%M")
            except: d_str = "N/D"
            
            msg += f"\n📅 Aggiornato: {d_str}"
            
            await query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ Impossibile aggiornare i dati di questo distributore. Potrebbe essere chiuso o aver cambiato ID.")