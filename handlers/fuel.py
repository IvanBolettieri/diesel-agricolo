from telegram import Update
from telegram.ext import ContextTypes
from services.fuel_api import search_fuel_stations
from handlers.keyboards import get_main_menu

async def find_gas_stations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la ricerca dei benzinai basata sulla posizione salvata"""
    
    # 1. Recuperiamo la posizione salvata nei dati utente
    lat = context.user_data.get('latitude')
    lon = context.user_data.get('longitude')

    # 2. Se non c'è posizione, avvisiamo l'utente
    if not lat or not lon:
        await update.message.reply_text(
            "⚠️ Non so dove sei! Per favore clicca su '📍 Imposta Posizione' nel menu.",
            reply_markup=get_main_menu()
        )
        return

    await update.message.reply_text("⏳ Sto cercando i prezzi migliori per il Gasolio in zona...")

    # 3. Chiamiamo l'API
    response = await search_fuel_stations(float(lat), float(lon))

    if not response or not response.get('success'):
        await update.message.reply_text("❌ Errore durante la ricerca o servizio momentaneamente non disponibile.")
        return

    results = response.get('results', [])
    
    if not results:
        await update.message.reply_text("❌ Nessun distributore trovato nel raggio selezionato.")
        return

    # 4. Formattiamo i risultati (Prendiamo i primi 5 più economici)
    message = "⛽ **Top 5 Distributori (Gasolio)**\n\n"
    for station in results[:5]:
        # L'API restituisce 'price' direttamente quando si filtra per tipo carburante
        message += f"🏪 *{station.get('brand', 'Sconosciuto')}* ({station.get('name', '')})\n"
        message += f"💰 *{station.get('price')} €/L*\n"
        message += f"📏 Distanza: {station.get('distance')} km\n\n"

    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())