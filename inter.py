import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                        MessageHandler, filters, ContextTypes, ConversationHandler)

# Secret Code for admin access
SECRET_CODE = "haxhax"
admins = set()
open_chats = set()
megas = {}
groups = {}
mega_id_counter = 0
group_id_counter = 0

# States for ConversationHandler
START, ASK_NAME, ASK_MESSAGE, CONFIRM_MESSAGE = range(4)

# Load or initialize the database
def load_database():
    global admins, open_chats, megas, groups, mega_id_counter, group_id_counter
    try:
        with open("bot_data.json", "r") as file:
            data = json.load(file)
            admins = set(data.get("admins", []))
            open_chats = set(data.get("open_chats", []))
            megas = {int(k): v for k, v in data.get("megas", {}).items()}
            groups = {int(k): v for k, v in data.get("groups", {}).items()}
            mega_id_counter = data.get("mega_id_counter", 0)
            group_id_counter = data.get("group_id_counter", 0)
    except FileNotFoundError:
        save_database()

def save_database():
    data = {
        "admins": list(admins),
        "open_chats": list(open_chats),
        "megas": megas,
        "groups": groups,
        "mega_id_counter": mega_id_counter,
        "group_id_counter": group_id_counter
    }
    with open("bot_data.json", "w") as file:
        json.dump(data, file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    open_chats.add(user_id)
    save_database()

    # Adding the new message above the buttons
    info_message = "Everything is Checked and Updated 8 Times a Day every 3 hours."

    keyboard = [
        [
            InlineKeyboardButton("Groups", callback_data="groups"),
            InlineKeyboardButton("Megas", callback_data="megas"),
        ],
        [InlineKeyboardButton("How to Open Best-links", callback_data="tutorial")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(info_message, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "groups":
        if groups:
            for group_id, msg in groups.items():
                await query.message.reply_text(f"ID {group_id}:\n{msg}")
            await query.message.reply_text("Send /start to view the menu")
        else:
            await query.message.reply_text("No group messages available.")
            await query.message.reply_text("Send /start to view the menu")

    elif query.data == "megas":
        if megas:
            for mega_id, msg in megas.items():
                await query.message.reply_text(f"ID {mega_id}:\n{msg}")
            await query.message.reply_text("Send /start to view the menu")
        else:
            await query.message.reply_text("No mega messages available.")
            await query.message.reply_text("Send /start to view the menu")

    elif query.data == "tutorial":
        tutorial_message = (
            "• Tutorial to open Best Links :\n\n"
            "1️⃣- Click on Watch a Video\n"
            "2️⃣- Fast forward the video a bit.\n"
            "3️⃣- Return to the main page, \n"
            "Wait for half a minute to turn it into green, there you go!\n\n"
            "⚠️ Use a VPN if you get any other bad task!"
        )
        await query.message.reply_text(tutorial_message)
        await query.message.reply_text("Send /start to view the menu")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if user_message == SECRET_CODE:
        admins.add(update.effective_user.id)
        save_database()
        await update.message.reply_text("You now have admin access!")
    elif user_message == "/start":
        await start(update, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in admins:
        await update.message.reply_text(f"Open chats: {len(open_chats)}")
    else:
        await update.message.reply_text("Unauthorized.")

async def addmega_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return ConversationHandler.END
    
    context.user_data['type'] = 'mega'
    await update.message.reply_text("What do you want to name the Mega?")
    return ASK_NAME

async def addgroup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return ConversationHandler.END
    
    context.user_data['type'] = 'group'
    await update.message.reply_text("What do you want to name the Group?")
    return ASK_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    item_type = "Mega" if context.user_data['type'] == 'mega' else "Group"
    await update.message.reply_text(f"Please send the {item_type} URL or message.")
    return ASK_MESSAGE

async def handle_message_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["message"] = update.message.text
    item_type = "Mega" if context.user_data['type'] == 'mega' else "Group"
    
    preview_message = (
        f"Name: {context.user_data['name']}\n"
        f"{item_type}: {context.user_data['message']}"
    )
    keyboard = [[InlineKeyboardButton("Done", callback_data="done")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(preview_message, reply_markup=reply_markup)
    return CONFIRM_MESSAGE

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mega_id_counter, group_id_counter
    
    if context.user_data['type'] == 'mega':
        mega_id_counter += 1
        megas[mega_id_counter] = (
            f"Name: {context.user_data['name']}\n"
            f"Mega: {context.user_data['message']}"
        )
        await update.callback_query.message.reply_text(f"Mega message added with ID {mega_id_counter}.")
    else:
        group_id_counter += 1
        groups[group_id_counter] = (
            f"Name: {context.user_data['name']}\n"
            f"Group: {context.user_data['message']}"
        )
        await update.callback_query.message.reply_text(f"Group message added with ID {group_id_counter}.")
    
    save_database()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# The ring command: sends a message to all open chats
async def ring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return

    message = ' '.join(context.args)
    if message:
        for user_id in open_chats:
            try:
                await context.bot.send_message(user_id, message)  # Use context.bot
            except Exception as e:
                print(f"Failed to send message to {user_id}: {e}")
        await update.message.reply_text("Announcement sent.")
    else:
        await update.message.reply_text("Please provide a message to announce.")

# The delete mega message command
async def delmega(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
    
    try:
        message_id = int(context.args[0])
        if message_id in megas:
            del megas[message_id]
            save_database()
            await update.message.reply_text(f"Mega message with ID {message_id} deleted.")
        else:
            await update.message.reply_text("Message ID not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid message ID.")

# The delete group message command
async def delgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
    
    try:
        message_id = int(context.args[0])
        if message_id in groups:
            del groups[message_id]
            save_database()
            await update.message.reply_text(f"Group message with ID {message_id} deleted.")
        else:
            await update.message.reply_text("Message ID not found.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid message ID.")

def main():
    load_database()

    application = Application.builder().token("7810214786:AAHJySBUQi4tTc-YB_96KJzJr72VP0QT1hE").build()

    # Mega conversation handler
    mega_handler = ConversationHandler(
        entry_points=[CommandHandler("addmega", addmega_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_content)],
            CONFIRM_MESSAGE: [CallbackQueryHandler(handle_confirmation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="mega_conversation",
        persistent=False,
    )

    # Group conversation handler
    group_handler = ConversationHandler(
        entry_points=[CommandHandler("addgroup", addgroup_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_content)],
            CONFIRM_MESSAGE: [CallbackQueryHandler(handle_confirmation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="group_conversation",
        persistent=False,
    )

    # Add handlers
    application.add_handler(mega_handler)
    application.add_handler(group_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("ring", ring))
    application.add_handler(CommandHandler("delmega", delmega))
    application.add_handler(CommandHandler("delgroup", delgroup))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
