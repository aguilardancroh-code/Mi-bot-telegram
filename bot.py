import json
import os
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# 🔑 TOKEN (Asegúrate de que este sea el tuyo)
TOKEN = "8851946043:AAG-WoDGcmd09nzwoaXhAhGOePou0zust28"  

# 👤 ADMIN
ADMIN_ID = 8444068741       
COMANDO_SECRETO = "K9_pW2xQ7m"    

# 📂 Ruta en el servidor (Archivo en la misma carpeta)
DB_FILE = "usuarios_dancroh.json"

BLOQUEO_COMPRAS = {}

# --- BASE DE DATOS ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                datos = json.load(f)
                # Asegurar que existan las llaves
                for k in ["keys_1d", "keys_3d", "keys_7d", "keys_30d"]:
                    if k not in datos: datos[k] = []
                return datos
            except:
                pass
    return {"usuarios": {}, "sesiones_activas": {}, "keys_1d": [], "keys_3d": [], "keys_7d": [], "keys_30d": []}

def guardar_datos(datos):
    with open(DB_FILE, "w") as f:
        json.dump(datos, f, indent=4)

# --- LÓGICA BOT ---
def esta_logueado(tg_id, datos):
    str_id = str(tg_id)
    if str_id not in datos.get("sesiones_activas", {}): return False
    fecha_login = datetime.strptime(datos["sesiones_activas"][str_id]["fecha_login"], "%Y-%m-%d %H:%M:%S")
    return (datetime.now() - fecha_login) <= timedelta(days=3)

def menu_principal_buttons():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👤 Mi Cuenta", callback_data='mi_cuenta')], [InlineKeyboardButton("🛒 Comprar", callback_data='menu_comprar')]])

def menu_duracion_drip_buttons(datos):
    keyboard = [
        [InlineKeyboardButton(f"⏱️ 1 día - $0.65 ({len(datos.get('keys_1d', []))})", callback_data='opciones_1d')],
        [InlineKeyboardButton(f"⏱️ 3 días - $1.25 ({len(datos.get('keys_3d', []))})", callback_data='opciones_3d')],
        [InlineKeyboardButton(f"⏱️ 7 días - $2.70 ({len(datos.get('keys_7d', []))})", callback_data='opciones_7d')],
        [InlineKeyboardButton(f"⏱️ 30 días - $5.40 ({len(datos.get('keys_30d', []))})", callback_data='opciones_30d')],
        [InlineKeyboardButton("⬅️ Atrás", callback_data='volver_principal')]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_sub_compra_buttons(duracion):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Comprar 1 Key", callback_data=f"buy_1_{duracion}")], [InlineKeyboardButton("🔢 Comprar Varias", callback_data=f"ask_multi_{duracion}")], [InlineKeyboardButton("⬅️ Volver", callback_data='menu_comprar')]])

def start(update, context):
    tg_id = update.effective_user.id
    datos = cargar_datos()
    if esta_logueado(tg_id, datos):
        update.message.reply_text("👋 ¡Hola de nuevo! Elige una opción:", reply_markup=menu_principal_buttons())
    else:
        update.message.reply_text("👋 Bienvenido.\n/registrar usuario contraseña\n/login usuario contraseña")

def registrar(update, context):
    datos = cargar_datos()
    try:
        usuario = context.args[0].lower()
        password = context.args[1]
        if usuario in datos["usuarios"]: update.message.reply_text("❌ Usuario ya existe."); return
        datos["usuarios"][usuario] = {"password": password, "saldo": 0.0}
        guardar_datos(datos)
        update.message.reply_text("🎉 Registrado. Usa /login usuario contraseña")
    except: update.message.reply_text("💡 Uso: /registrar usuario contraseña")

def login(update, context):
    datos = cargar_datos()
    try:
        usuario = context.args[0].lower()
        password = context.args[1]
        if usuario in datos["usuarios"] and datos["usuarios"][usuario]["password"] == password:
            datos["sesiones_activas"][str(update.effective_user.id)] = {"usuario": usuario, "fecha_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            guardar_datos(datos)
            update.message.reply_text("🔓 Acceso concedido.", reply_markup=menu_principal_buttons())
        else: update.message.reply_text("❌ Datos incorrectos.")
    except: update.message.reply_text("💡 Uso: /login usuario contraseña")

def procesar_clicks(update, context):
    query = update.callback_query
    datos = cargar_datos()
    tg_id = update.effective_user.id
    if not esta_logueado(tg_id, datos): query.answer("🔒 Sesión expirada."); return
    usuario_activo = datos["sesiones_activas"][str(tg_id)]["usuario"]
    
    if query.data == 'volver_principal': query.edit_message_text("Menú:", reply_markup=menu_principal_buttons())
    elif query.data == 'menu_comprar': query.edit_message_text("🟢 Elige duración:", reply_markup=menu_duracion_drip_buttons(datos))
    elif query.data.startswith('opciones_'): query.edit_message_text("⚙️ Acción:", reply_markup=menu_sub_compra_buttons(query.data.split('_')[1]))
    elif query.data.startswith('ask_multi_'): 
        context.user_data['esperando_cantidad'] = query.data.split('_')[2]
        query.edit_message_text("🔢 Introduce la cantidad:")
    elif query.data.startswith('buy_'):
        partes = query.data.split('_')
        ejecutar_compra(tg_id, context, usuario_activo, datos["usuarios"][usuario_activo], datos, int(partes[1]), partes[2])

def manejar_mensajes_texto(update, context):
    tg_id = update.effective_user.id
    datos = cargar_datos()
    if 'esperando_cantidad' in context.user_data:
        duracion = context.user_data.pop('esperando_cantidad')
        try:
            ejecutar_compra(tg_id, context, datos["sesiones_activas"][str(tg_id)]["usuario"], datos["usuarios"][datos["sesiones_activas"][str(tg_id)]["usuario"]], datos, int(update.message.text), duracion)
        except: update.message.reply_text("❌ Error. Asegúrate de poner un número.")

def ejecutar_compra(chat_id, context, usuario, user_data, datos, cantidad, duracion):
    precios = {"1d": 0.65, "3d": 1.25, "7d": 2.70, "30d": 5.40}
    lista = f"keys_{duracion}"
    if user_data['saldo'] < (precios[duracion] * cantidad) or len(datos[lista]) < cantidad:
        context.bot.send_message(chat_id=chat_id, text="❌ Error: Saldo o stock insuficiente.")
        return
    datos["usuarios"][usuario]['saldo'] -= (precios[duracion] * cantidad)
    entregadas = [datos[lista].pop(0) for _ in range(cantidad)]
    guardar_datos(datos)
    context.bot.send_message(chat_id=chat_id, text=f"✅ Compraste {cantidad} keys:\n" + "\n".join(entregadas))

def comandos_admin(update, context):
    if update.effective_user.id != ADMIN_ID: return
    cmd = update.message.text.split()[0][1:]
    if cmd == COMANDO_SECRETO:
        datos = cargar_datos()
        datos["usuarios"][context.args[0].lower()]['saldo'] += float(context.args[1])
        guardar_datos(datos)
        update.message.reply_text("✅ Saldo añadido.")
    elif cmd == "addkey":
        datos = cargar_datos()
        datos[f"keys_{context.args[0].lower()}"].append(context.args[1])
        guardar_datos(datos)
        update.message.reply_text("📥 Key agregada.")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start)); dp.add_handler(CommandHandler("registrar", registrar)); dp.add_handler(CommandHandler("login", login))
    dp.add_handler(CommandHandler(COMANDO_SECRETO, comandos_admin)); dp.add_handler(CommandHandler("addkey", comandos_admin))
    dp.add_handler(CallbackQueryHandler(procesar_clicks)); dp.add_handler(MessageHandler(Filters.text & ~Filters.command, manejar_mensajes_texto))
    updater.start_polling(drop_pending_updates=True); updater.idle()

if __name__ == '__main__': main()