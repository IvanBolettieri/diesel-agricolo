from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Restituisce la tastiera del menu principale"""
    keyboard = [
        [KeyboardButton("⛽ Cerca Benzinai")],
        [KeyboardButton("📍 Imposta Posizione"), KeyboardButton("⭐ Preferiti")],
        [KeyboardButton("⚙️ Carburante"), KeyboardButton("ℹ️ Info")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_fuel_menu():
    """Restituisce la tastiera per la scelta del carburante"""
    keyboard = [
        [KeyboardButton("🟢 Benzina"), KeyboardButton("⚫ Diesel")],
        [KeyboardButton("🔙 Menu Principale")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)