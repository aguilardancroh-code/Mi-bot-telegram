import json
import os
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

TOKEN = "8851946043:AAG-WoDGcmd09nzwoaXhAhGOePou0zust28"
ADMIN_ID = 8444068741
COMANDO_SECRETO = "K9_pW2xQ7m"
DB_FILE = "usuarios_dancroh.json"
BLOQUEO_COMPRAS = {}

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {"usuarios": {}, "sesiones_activas": {}, "keys_1d": [], "keys_3d": [], "keys_7d": [], "keys_30d": []}

def guardar_datos(datos):
    with open(DB_FILE, "w") as f: json.dump(datos, f, indent=4)

def esta_logueado(tg_id, datos):
    str_id = str(tg_id)
    if str_id not in datos.get("sesiones_activas", {}): return False
    fecha_login = datetime.strptime(datos["sesiones_activas"][str_id]["fecha_login"], "%Y-%m-%d %H:%M:%S")
    return (datetime.now() - fecha_login) <= timedelta(days=3)

def menu_principal_buttons():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👤 Mi Cuenta", callback_data='mi_cuenta')], [InlineKeyboardButton("🛒 Comprar", callback_data='menu_comprar')]])

def start(update, context):
    tg_id = update.effective_user.id
    datos = cargar_datos()
    if esta_logueado(tg_id, datos):
        update.message.reply_text("👋 Hola, elige:", reply_markup=menu_principal_buttons())
    else:
        update.message.reply_text("👋 Usa /registrar usuario contraseña o /login usuario contraseña")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__': main()