from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from services.fuel_api import search_fuel_stations
from handlers.keyboards import get_main_menu, get_fuel_menu
from database import get_user, update_user_fuel

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

    # Recuperiamo il tipo carburante (Default: 2-1 che è Diesel/Gasolio, 1-1 è Benzina)
    fuel_type = user.fuel_type if user.fuel_type else "2-1"
    fuel_label = "Diesel" if fuel_type == "2-1" else "Benzina"

    await update.message.reply_text(f"⏳ Sto cercando i prezzi migliori per: **{fuel_label}**...", parse_mode="Markdown")

    # 3. Chiamiamo l'API
    response = await search_fuel_stations(float(lat), float(lon), radius=5, fuel_type=fuel_type)

    if not response:
        await update.message.reply_text("❌ Errore durante la ricerca o servizio momentaneamente non disponibile.")
        return

    # Gestione della risposta: l'API a volte restituisce un dict con chiave 'results', a volte una lista diretta
    if isinstance(response, dict):
        results = response.get('results', [])
    elif isinstance(response, list):
        results = response
    else:
        results = []
    
    if not results:
        await update.message.reply_text("❌ Nessun distributore trovato nel raggio selezionato.")
        return

    # 4. Formattiamo i risultati (Prendiamo i primi 5 più economici)
    message = f"⛽ **Top 5 Distributori ({fuel_label})**\n\n"
    
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
    for item in stations_to_sort[:5]:
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

        message += f"🏪 *{station.get('brand', 'Sconosciuto')}* ({station.get('name', '')})\n"
        
        if matching_fuels:
            # Ordiniamo per prezzo e mostriamo tutte le opzioni (es. Self e Servito)
            matching_fuels.sort(key=lambda x: x.get('price', 999))
            for f in matching_fuels:
                price_val = f.get('price')
                is_self = f.get('isSelf', False)
                type_label = "Self" if is_self else "Servito"
                message += f"💰 {type_label}: *{price_val:.3f} €/L*\n"
        else:
            message += f"💰 Prezzo non disponibile\n"
            
        message += f"🕒 Aggiornato: {date_str}\n"
        message += f"📏 Distanza: {float(station.get('distance', 0)):.1f} km"

        # Link Google Maps per navigazione
        loc = station.get('location', {})
        if loc and 'lat' in loc and 'lng' in loc:
            message += f"\n🚗 [Avvia Navigazione](https://www.google.com/maps/dir/?api=1&destination={loc['lat']},{loc['lng']})"
        
        message += "\n\n"

    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())

async def show_fuel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra il menu per scegliere il carburante"""
    user = await get_user(update.effective_user.id)
    current = user.fuel_type if user and user.fuel_type else "2-1"
    
    label = "Diesel" if current == "2-1" else "Benzina"
    
    await update.message.reply_text(
        f"Attualmente stai cercando: *{label}*.\nSeleziona cosa vuoi cercare:",
        reply_markup=get_fuel_menu(),
        parse_mode="Markdown"
    )

async def set_fuel_benzina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imposta Benzina (codice 1-1)"""
    await update_user_fuel(update.effective_user.id, '1-1')
    await update.message.reply_text(
        "✅ Hai impostato: **Benzina**.\nLe prossime ricerche useranno questo carburante.",
        reply_markup=get_main_menu(), parse_mode="Markdown")

async def set_fuel_diesel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imposta Diesel (codice 2-1)"""
    await update_user_fuel(update.effective_user.id, '2-1')
    await update.message.reply_text(
        "✅ Hai impostato: **Diesel**.\nLe prossime ricerche useranno questo carburante.",
        reply_markup=get_main_menu(), parse_mode="Markdown")