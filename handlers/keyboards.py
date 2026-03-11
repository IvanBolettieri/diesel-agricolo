from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Restituisce la tastiera del menu principale"""
    keyboard = [
        [KeyboardButton("⛽ Cerca Benzinai")],
        [KeyboardButton("📍 Imposta Posizione"), KeyboardButton("ℹ️ Info")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)