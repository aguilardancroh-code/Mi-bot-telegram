import json
import os
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# 🔑 TU TOKEN DE BOTFATHER
TOKEN = "8851946043:AAG-WoDGcmd09nzwoaXhAhGOePou0zust28"  

# 👤 CONTROL TOTAL COMO ADMINISTRADOR (Configurado con tu ID real)
ADMIN_ID = 8444068741       
COMANDO_SECRETO = "K9_pW2xQ7m"    

# 📂 Ruta segura en la memoria interna local del iPhone
DOCUMENTOS_DIR = os.path.expanduser("~/Documents")
DB_FILE = os.path.join(DOCUMENTOS_DIR, "usuarios_dancroh.json")

# Diccionario global para evitar doble click (Antiflood de compras)
BLOQUEO_COMPRAS = {}

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
        [InlineKeyboardButton(f"⏱️ 1 día - $0.65 ({stock_1d})", callback_data='opciones_1d')],
        [InlineKeyboardButton(f"⏱️ 3 días - $1.25 ({stock_3d})", callback_data='opciones_3d')],
        [InlineKeyboardButton(f"⏱️ 7 días - $2.70 ({stock_7d})", callback_data='opciones_7d')],
        [InlineKeyboardButton(f"⏱️ 30 días - $5.40 ({stock_30d})", callback_data='opciones_30d')],
        [InlineKeyboardButton("⬅️ Atrás", callback_data='volver_principal')]
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_sub_compra_buttons(duracion):
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar 1 Key", callback_data=f"buy_1_{duracion}")],
        [InlineKeyboardButton("🔢 Comprar Varias Keys", callback_data=f"ask_multi_{duracion}")],
        [InlineKeyboardButton("⬅️ Volver", callback_data='menu_comprar')]
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

# --- PROCESAR MENÚS Y PROCESO DE COMPRA ---
def procesar_clicks(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    tg_id = update.effective_user.id
    datos = cargar_datos()
    
    if not esta_logueado(tg_id, datos):
        query.answer("🔒 Sesión expirada.")
        query.edit_message_text("🔒 Sesión expirada. Por favor usa /login.")
        return

    usuario_activo = datos["sesiones_activas"][str(tg_id)]["usuario"]
    user_data = datos["usuarios"][usuario_activo]

    if query.data == 'volver_principal':
        query.answer()
        query.edit_message_text("Elige una opción para continuar:", reply_markup=menu_principal_buttons())
        
    elif query.data == 'menu_comprar':
        query.answer()
        query.edit_message_text("🟢 DRIP CLIENT\nElige la duración de tu acceso:", 
                                reply_markup=menu_duracion_drip_buttons(datos))
        
    elif query.data == 'mi_cuenta':
        query.answer()
        texto_cuenta = (
            f"💳 Tu Cuenta Dancroh:\n\n"
            f"👤 Usuario: {usuario_activo}\n"
            f"💰 Saldo: ${user_data['saldo']:.2f}"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data='volver_principal')]]
        query.edit_message_text(texto_cuenta, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('opciones_'):
        query.answer()
        duracion = query.data.split('_')[1]
        query.edit_message_text(f"⚙️ Opciones para DRIP CLIENT ({duracion}):\n¿Qué acción deseas realizar?", 
                                reply_markup=menu_sub_compra_buttons(duracion))

    elif query.data.startswith('ask_multi_'):
        query.answer()
        duracion = query.data.split('_')[2]
        context.user_data['esperando_cantidad'] = duracion
        query.edit_message_text(f"🔢 Introduce en un mensaje la cantidad de keys ({duracion}) que deseas comprar:")

    elif query.data.startswith('buy_'):
        ahora = time.time()
        ultimo_click = BLOQUEO_COMPRAS.get(tg_id, 0)
        
        if ahora - ultimo_click < 3:
            query.answer("⚠️ Procesando tu compra anterior...", show_alert=False)
            return
            
        BLOQUEO_COMPRAS[tg_id] = flushed_time = ahora
        query.answer("⏳ Procesando...")
        
        partes = query.data.split('_')
        cantidad = int(partes[1])
        duracion = partes[2]
        
        # Eliminamos el menú de botones viejo por completo para que no se dupliquen acciones
        try:
            query.message.delete()
        except Exception:
            pass
            
        ejecutar_compra(tg_id, context, usuario_activo, user_data, datos, cantidad, duracion)

def manejar_mensajes_texto(update: Update, context: CallbackContext) -> None:
    tg_id = update.effective_user.id
    datos = cargar_datos()
    
    if not esta_logueado(tg_id, datos):
        return

    if 'esperando_cantidad' in context.user_data:
        duracion = context.user_data.pop('esperando_cantidad')
        usuario_activo = datos["sesiones_activas"][str(tg_id)]["usuario"]
        user_data = datos["usuarios"][usuario_activo]
        
        try:
            cantidad = int(update.message.text.strip())
            if cantidad <= 0:
                update.message.reply_text("❌ La cantidad debe ser mayor a 0.")
                return
            
            ejecutar_compra(tg_id, context, usuario_activo, user_data, datos, cantidad, duracion)
            
        except ValueError:
            update.message.reply_text("❌ Por favor, introduce un número válido entero.")

def ejecutar_compra(chat_id, context, usuario_activo, user_data, datos, cantidad, duracion):
    precios_dict = {"1d": 0.65, "3d": 1.25, "7d": 2.70, "30d": 5.40}
    llave_key_dict = {"1d": "keys_1d", "3d": "keys_3d", "7d": "keys_7d", "30d": "keys_30d"}
    
    precio_unitario = precios_dict[duracion]
    precio_total = precio_unitario * cantidad
    lista_nombre = llave_key_dict[duracion]
    
    if user_data['saldo'] < precio_total:
        texto_error_saldo = f"❌ Saldo insuficiente. Necesitas ${precio_total:.2f}. Tu saldo: ${user_data['saldo']:.2f}"
        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data='menu_comprar')]]
        context.bot.send_message(chat_id=chat_id, text=texto_error_saldo, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if len(datos[lista_nombre]) < cantidad:
        texto_agotado = f"⚠️ Stock insuficiente. Solo quedan {len(datos[lista_nombre])} keys disponibles."
        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data='menu_comprar')]]
        context.bot.send_message(chat_id=chat_id, text=texto_agotado, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Deducción y procesamiento seguro de keys
    datos["usuarios"][usuario_activo]['saldo'] -= precio_total
    llaves_entregadas = [datos[lista_nombre].pop(0) for _ in range(cantidad)]
    guardar_datos(datos)
    
    # MENSAJE 1: ÚNICAMENTE LA KEY LIMPIA (Este mensaje jamás se modificará ni borrará)
    if cantidad == 1:
        texto_key = (
            f"✅ 𝘾𝙊𝙈𝙋𝙍𝘼 𝙀𝙓𝙄𝙏𝙊𝙎𝘼 (1 key)\n\n"
            f"🔑 Key: {llaves_entregadas[0]}"
        )
    else:
        lista_claves = "\n".join([f"🔑 Key: {k}" for k in llaves_entregadas])
        texto_key = (
            f"✅ 𝘾𝙊𝙈𝙋𝙍𝘼 𝙀𝙓𝙄𝙏𝙊𝙎𝘼 ({cantidad} keys)\n\n"
            f"{lista_claves}"
        )
    
    # Se envía de forma independiente
    context.bot.send_message(chat_id=chat_id, text=texto_key)

    # MENSAJE 2: MENSAJE CON LOS BOTONES DE NAVEGACIÓN TOTALMENTE APARTE
    keyboard_navegacion = [
        [
            InlineKeyboardButton("🛒 Comprar más", callback_data='menu_comprar'),
            InlineKeyboardButton("🏠 Menú", callback_data='volver_principal')
        ]
    ]
    context.bot.send_message(
        chat_id=chat_id, 
        text="🛍️ ¿Qué deseas hacer ahora?", 
        reply_markup=InlineKeyboardMarkup(keyboard_navegacion)
    )

# --- RECARGAS DE SALDO Y ENTRADA DE LLAVES (ADMIN) ---
def comandos_admin(update: Update, context: CallbackContext) -> None:
    tg_id = update.effective_user.id
    
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
            llave_key_dict = {"1d": "keys_1d", "3d": "keys_3d", "7d": "keys_7d", "30d": "keys_30d"}
            
            if tipo_dias not in llave_key_dict:
                update.message.reply_text("❌ Duración inválida. Usa: 1d, 3d, 7d o 30d.")
                return
            
            texto_completo = update.message.text
            lineas = texto_completo.split('\n')
            nuevas_keys = []
            
            if len(lineas) == 1:
                for item in context.args[1:]:
                    item_limpio = item.replace("Key:", "").replace("key:", "").strip()
                    if item_limpio:
                        nuevas_keys.append(item_limpio)
            else:
                for linea in lineas[1:]:
                    linea_limpia = linea.replace("Key:", "").replace("key:", "").strip()
                    if linea_limpia:
                        nuevas_keys.append(linea_limpia)
            
            if not nuevas_keys:
                update.message.reply_text("⚠️ No se encontraron llaves válidas.")
                return
                
            datos = cargar_datos()
            for key in nuevas_keys:
                datos[llave_key_dict[tipo_dias]].append(key)
                
            guardar_datos(datos)
            update.message.reply_text(f"📥 Se agregaron masivamente {len(nuevas_keys)} llaves a {tipo_dias}.")
            
        except IndexError:
            update.message.reply_text("💡 Formato:\n/addkey 1d\nKey: 11111\nKey: 22222")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("registrar", registrar))
    dispatcher.add_handler(CommandHandler("login", login))
    
    dispatcher.add_handler(CommandHandler(COMANDO_SECRETO, comandos_admin))
    dispatcher.add_handler(CommandHandler("addkey", comandos_admin))
    
    dispatcher.add_handler(CallbackQueryHandler(procesar_clicks))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, manejar_mensajes_texto))

    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == '__main__':
    main()