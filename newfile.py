import json
import sys
from unittest.mock import MagicMock
sys.modules['imghdr'] = MagicMock()
import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# 🔑 TU TOKEN DE BOTFATHER
TOKEN = "8851946043:AAG-WoDGcmd09nzwoaXhAhGOePou0zust28"  

# 👤 CONTROL TOTAL COMO ADMINISTRADOR (Configurado con tu ID real)
ADMIN_ID = 8444068741       
COMANDO_SECRETO = "K9_pW2xQ7m"    

# 📂 Ruta segura en la memoria interna local del iPhone
DB_FILE = "usuarios_dancroh.json"

# --- BASE DE DATOS LOCAL (JSON) ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                datos = json.load(f)
                if "keys_1d" not in datos: datos["keys_1d"] = []
                if "keys_3d" not in datos: datos["keys_3d"] = []
                if "keys_7d" not in datos: datos["keys_7d"] = []
                if "keys_30d" not in datos: datos["keys_30d"] = []
                return datos
            except json.JSONDecodeError:
                pass
                
    return {
        "usuarios": {}, 
        "sesiones_activas": {},
        "keys_1d": [],
        "keys_3d": [],
        "keys_7d": [],
        "keys_30d": []
    }

def guardar_datos(datos):
    with open(DB_FILE, "w") as f:
        json.dump(datos, f, indent=4)

# --- VALIDACIÓN DE SESIÓN EN SEGUNDO PLANO ---
def esta_logueado(tg_id, datos):
    str_id = str(tg_id)
    if str_id not in datos.get("sesiones_activas", {}):
        return False
    
    fecha_login_str = datos["sesiones_activas"][str_id]["fecha_login"]
    fecha_login = datetime.strptime(fecha_login_str, "%Y-%m-%d %H:%M:%S")
    
    if datetime.now() - fecha_login > timedelta(days=3):
        return False
    return True

# --- MENÚS DE BOTONES ---
def menu_principal_buttons():
    keyboard = [
        [InlineKeyboardButton("👤 Mi Cuenta", callback_data='mi_cuenta')],
        [InlineKeyboardButton("🛒 Comprar", callback_data='menu_comprar')]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_duracion_drip_buttons(datos):
    stock_1d = len(datos.get("keys_1d", []))
    stock_3d = len(datos.get("keys_3d", []))
    stock_7d = len(datos.get("keys_7d", []))
    stock_30d = len(datos.get("keys_30d", []))

    keyboard = [
        [InlineKeyboardButton(f"⏱️ 1 día - $0.65 [Disponibles: {stock_1d}]", callback_data='buy_1d')],
        [InlineKeyboardButton(f"⏱️ 3 días - $1.25 [Disponibles: {stock_3d}]", callback_data='buy_3d')],
        [InlineKeyboardButton(f"⏱️ 7 días - $2.70 [Disponibles: {stock_7d}]", callback_data='buy_7d')],
        [InlineKeyboardButton(f"⏱️ 30 días - $5.40 [Disponibles: {stock_30d}]", callback_data='buy_30d')],
        [InlineKeyboardButton("⬅️ Atrás", callback_data='volver_principal')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- COMANDOS DEL BOT ---
def start(update: Update, context: CallbackContext) -> None:
    tg_id = update.effective_user.id
    datos = cargar_datos()
    
    if esta_logueado(tg_id, datos):
        usuario_activo = datos["sesiones_activas"][str(tg_id)]["usuario"]
        update.message.reply_text(
            f"👋 ¡Hola de nuevo, {usuario_activo}! Tu sesión sigue activa.\nElige una opción para continuar:",
            reply_markup=menu_principal_buttons()
        )
        return

    texto_bienvenida = (
        "👋 ¡Bienvenido a Dancroh Bot!\n\n"
        "🔒 Este bot requiere inicio de sesión obligatorio para proteger tu saldo.\n\n"
        "📝 ¿No tienes cuenta? Regístrate escribiendo:\n"
        "/registrar tu_usuario tu_contraseña\n\n"
        "🔑 ¿Ya estás registrado? Inicia sesión con:\n"
        "/login tu_usuario tu_contraseña"
    )
    update.message.reply_text(texto_bienvenida)

def registrar(update: Update, context: CallbackContext) -> None:
    datos = cargar_datos()
    try:
        usuario = context.args[0].lower()
        password = context.args[1]
        
        if usuario in datos["usuarios"]:
            update.message.reply_text("❌ Ese usuario ya existe en la tienda. Elige otro.")
            return
        
        datos["usuarios"][usuario] = {
            "password": password,
            "saldo": 0.0
        }
        guardar_datos(datos)
        update.message.reply_text(f"🎉 ¡Te has registrado correctamente en Dancroh!\n\n🔑 Ahora inicia sesión usando:\n/login {usuario} tu_contraseña")
        
    except IndexError:
        update.message.reply_text("💡 Uso correcto: /registrar usuario contraseña")

def login(update: Update, context: CallbackContext) -> None:
    datos = cargar_datos()
    try:
        usuario = context.args[0].lower()
        password = context.args[1]
        tg_id = str(update.effective_user.id)
        
        if usuario in datos["usuarios"]:
            if datos["usuarios"][usuario]["password"] == password:
                datos["sesiones_activas"][tg_id] = {
                    "usuario": usuario,
                    "fecha_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                guardar_datos(datos)
                update.message.reply_text(
                    f"🔓 ¡Acceso concedido! Bienvenido {usuario}.",
                    reply_markup=menu_principal_buttons()
                )
                return
            else:
                update.message.reply_text("❌ Contraseña incorrecta.")
                return
        else:
            update.message.reply_text("❌ Ese usuario no existe.")
            
    except IndexError:
        update.message.reply_text("💡 Uso correcto: /login usuario contraseña")

# --- PROCESAR MENÚS Y COMPRA DE LLAVES ---
def procesar_clicks(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    tg_id = update.effective_user.id
    datos = cargar_datos()
    
    if not esta_logueado(tg_id, datos):
        query.edit_message_text("🔒 Sesión expirada. Por favor usa /login.")
        return

    usuario_activo = datos["sesiones_activas"][str(tg_id)]["usuario"]
    user_data = datos["usuarios"][usuario_activo]

    if query.data == 'volver_principal':
        query.edit_message_text("Elige una opción para continuar:", reply_markup=menu_principal_buttons())
        
    elif query.data == 'menu_comprar':
        query.edit_message_text("🟢 DRIP CLIENT\nElige la duración de tu acceso:", 
                                reply_markup=menu_duracion_drip_buttons(datos))
        
    elif query.data == 'mi_cuenta':
        texto_cuenta = (
            f"💳 Tu Cuenta Dancroh:\n\n"
            f"👤 Usuario: {usuario_activo}\n"
            f"💰 Saldo: ${user_data['saldo']:.2f}"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='volver_principal')]]
        query.edit_message_text(texto_cuenta, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('buy_'):
        duracion = query.data.split('_')[1]  
        
        precios_dict = {"1d": 0.65, "3d": 1.25, "7d": 2.70, "30d": 5.40}
        llave_key_dict = {"1d": "keys_1d", "3d": "keys_3d", "7d": "keys_7d", "30d": "keys_30d"}
        
        precio = precios_dict[duracion]
        lista_nombre = llave_key_dict[duracion]
        
        if user_data['saldo'] < precio:
            texto_error_saldo = (
                f"❌ Saldo Insuficiente.\n\n"
                f"Necesitas ${precio:.2f} para adquirir este acceso ({duracion}).\n"
                f"💰 Tu saldo actual es de: ${user_data['saldo']:.2f}\n\n"
                f"📲 Por favor, contacta al administrador para recargar tu cuenta."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='volver_principal')]]
            query.edit_message_text(texto_error_saldo, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if len(datos[lista_nombre]) == 0:
            texto_agotado = (
                f"⚠️ Producto temporalmente agotado\n\n"
                f"No quedan llaves disponibles en el sistema para {duracion}.\n"
                f"Por favor, notifica al administrador para que añada existencias."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data='menu_comprar')]]
            query.edit_message_text(texto_agotado, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        datos["usuarios"][usuario_activo]['saldo'] -= precio
        llave_entregada = datos[lista_nombre].pop(0)
        guardar_datos(datos)
        
        texto_exito = (
            f"✅ ¡Compra realizada con éxito!\n\n"
            f"📦 Producto: DRIP CLIENT ({duracion})\n"
            f"💸 Precio: ${precio:.2f}\n"
            f"💰 Tu saldo restante: ${datos['usuarios'][usuario_activo]['saldo']:.2f}\n\n"
            f"🔑 Tu KEY de acceso es:\n{llave_entregada}"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='volver_principal')]]
        query.edit_message_text(texto_exito, reply_markup=InlineKeyboardMarkup(keyboard))

# --- RECARGAS DE SALDO Y ENTRADA DE LLAVES (ADMIN) ---
def comandos_admin(update: Update, context: CallbackContext) -> None:
    tg_id = update.effective_user.id
    
    # FILTRO POR ID INMUTABLE: Solo tú tienes permisos
    if tg_id != ADMIN_ID:
        return  

    comando = update.message.text.split()[0][1:] 

    if comando == COMANDO_SECRETO:
        try:
            user_to_charge = context.args[0].lower()
            monto = float(context.args[1])
            datos = cargar_datos()
            
            if user_to_charge in datos["usuarios"]:
                datos["usuarios"][user_to_charge]['saldo'] += monto
                guardar_datos(datos)
                update.message.reply_text(f"✅ Añadidos ${monto:.2f} a la cuenta de {user_to_charge}.")
            else:
                update.message.reply_text("❌ Ese usuario no está registrado.")
        except (IndexError, ValueError):
            update.message.reply_text(f"💡 Formato: /{COMANDO_SECRETO} usuario cantidad")
            
    elif comando == "addkey":
        try:
            tipo_dias = context.args[0].lower() 
            nueva_key = context.args[1]
            
            llave_key_dict = {"1d": "keys_1d", "3d": "keys_3d", "7d": "keys_7d", "30d": "keys_30d"}
            
            if tipo_dias not in llave_key_dict:
                update.message.reply_text("❌ Duración inválida. Usa: 1d, 3d, 7d o 30d.")
                return
                
            datos = cargar_datos()
            datos[llave_key_dict[tipo_dias]].append(nueva_key)
            guardar_datos(datos)
            
            total_disponibles = len(datos[llave_key_dict[tipo_dias]])
            update.message.reply_text(f"🔑 ¡Llave para {tipo_dias} agregada con éxito!\n📦 Stock actual de {tipo_dias}: {total_disponibles} llaves.")
            
        except IndexError:
            update.message.reply_text("💡 Formato: /addkey [1d/3d/7d/30d] la_llave_aqui")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("registrar", registrar))
    dispatcher.add_handler(CommandHandler("login", login))
    
    dispatcher.add_handler(CommandHandler(COMANDO_SECRETO, comandos_admin))
    dispatcher.add_handler(CommandHandler("addkey", comandos_admin))
    
    dispatcher.add_handler(CallbackQueryHandler(procesar_clicks))

    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == '__main__':
    main()