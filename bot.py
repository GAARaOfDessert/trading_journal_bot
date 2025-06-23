import json
import bcrypt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Bot
from telegram.ext import CallbackQueryHandler

# Telegram bot token
BOT_TOKEN = "7613652813:AAFnKLGASHpx7thBOs48eIt4eSyGFbiFO7c"
bot = Bot(token=BOT_TOKEN)

# States
CHOOSING, REGISTER_NAME, REGISTER_PW, REGISTER_CONFIRM, LOGIN_NAME, LOGIN_PW = range(6)
MENU, JOURNAL, VIEW_TRADES, PERFORMANCE = range(6, 10)
PHOTO, RRR_ENTRY, OUTCOME = range(10, 13)

# Load user data
def load_data():
    try:
        with open("user_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=4)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(
        [["📘 Register", "🔐 Sign In"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text("Welcome to Trading Journal Bot!\nChoose an option:", reply_markup=reply_markup)
    return CHOOSING

# Choose Register or Sign In
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if "Register" in choice:
        await update.message.reply_text("Enter a journal name to register:")
        return REGISTER_NAME
    elif "Sign In" in choice:
        await update.message.reply_text("Enter your journal name:")
        return LOGIN_NAME
    else:
        await update.message.reply_text("Invalid choice. Please use /start again.")
        return await show_main_menu(update, context)

# Register flow
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text
    await update.message.reply_text("Enter a password:")
    return REGISTER_PW

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_password"] = update.message.text
    await update.message.reply_text("Confirm your password:")
    return REGISTER_CONFIRM

async def register_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirm = update.message.text
    name = context.user_data["reg_name"]
    pw = context.user_data["reg_password"]
    data = load_data()

    if confirm != pw:
        await update.message.reply_text("❌ Passwords do not match. Start again with /start.")
        return ConversationHandler.END

    if name in data:
        await update.message.reply_text("❌ Journal name already exists. Use /start to try again.")
        return ConversationHandler.END

    # Hash and save
    hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    data[name] = {
        "user_id": update.effective_user.id,
        "password": hashed,
        "trades": []
    }
    save_data(data)
    await update.message.reply_text(f"✅ Registered journal '{name}'. Use /start to log in.")
    return ConversationHandler.END

# Login flow
async def login_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_name"] = update.message.text
    await update.message.reply_text("Enter your password:")
    return LOGIN_PW

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("login_name")
    password = update.message.text
    data = load_data()

    # Check if journal name exists
    if name not in data:
        await update.message.reply_text("❌ Journal not found. Please register using /start.")
        return ConversationHandler.END

    stored_user = data[name]
    hashed_password = stored_user.get("password")

    # Check if password is correct
    if not bcrypt.checkpw(password.encode(), hashed_password.encode()):
        await update.message.reply_text("❌ Incorrect password. Try again using /start.")
        return ConversationHandler.END

    # Success
    context.user_data["logged_in"] = True
    context.user_data["journal_name"] = name
    await update.message.reply_text(f"✅ Welcome back, {name}!")
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        ["📊 View Performance", "📁 View Trades"],
        ["📝 Journal Today", "🚪 Log Out"]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("📋 Main Menu:", reply_markup=reply_markup)
    return MENU 

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == "📝 Journal Today":
        await update.message.reply_text("📷 Please send a screenshot of the trade at execution.")
        return PHOTO
    elif choice == "📊 View Performance":
        return await view_performance(update, context)
    elif choice == "📁 View Trades":
        return await view_trades(update, context)
    elif choice == "🚪 Log Out":
        context.user_data.clear()
        await update.message.reply_text("🚪 Logged out successfully. Type /start to begin again.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❓ Unknown option. Please use the menu.")
        return MENU
    
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo
    if not photo:
        await update.message.reply_text("❌ Please send a photo.")
        return PHOTO

    # Save Telegram file ID
    file_id = photo[-1].file_id
    context.user_data["journal_photo"] = file_id

    await update.message.reply_text("📏 What was the RRR at trade entry? (e.g. 1:2)")
    return RRR_ENTRY

async def receive_rrr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rrr = update.message.text.strip()

    if ":" not in rrr:
        await update.message.reply_text("❌ Format should be like 1:2")
        return RRR_ENTRY

    context.user_data["rrr_entry"] = rrr
    await update.message.reply_text("📈 What was the outcome of the trade?\nSend:\n• `w` for Win\n• `l` for Lose\n• `b` for Break-even")
    return OUTCOME

async def receive_outcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    outcome = update.message.text.strip().lower()
    valid_outcomes = ['w', 'l', 'b']
    if outcome not in valid_outcomes:
        await update.message.reply_text("⚠️ Invalid input. Please enter:\n• W for Win\n• L for Loss\n• B for Breakeven")
        return OUTCOME

    journal_name = context.user_data["journal_name"]
    data = load_data()

    # Save journal entry
    user_trades = data[journal_name].get("trades", [])
    trade_num = len(user_trades) + 1
    trade_name = f"Trade {trade_num}"

    new_entry = {
        "trade": trade_name,
        "photo_file_id": context.user_data["journal_photo"],
        "rrr_entry": context.user_data["rrr_entry"],
        "outcome": outcome
    }

    user_trades.append(new_entry)
    data[journal_name]["trades"] = user_trades
    save_data(data)

    await update.message.reply_text(f"✅ Trade saved as '{trade_name}'!")
    await show_main_menu(update, context)
    return MENU 

async def view_performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    journal_name = context.user_data.get("journal_name")
    if not journal_name:
        await update.message.reply_text("⚠️ You're not logged in. Use /start to begin.")
        return

    data = load_data()
    user_data = data.get(journal_name)
    trades = user_data.get("trades", [])

    if not trades:
        await update.message.reply_text("📭 No trades found in your journal yet.")
        return

    win_count = 0
    loss_count = 0
    breakeven_count = 0
    total_rr = 0.0  # total reward

    for trade in trades:
        outcome = trade.get("outcome", "").strip().lower()

        if "w" in outcome:
            win_count += 1
        elif "l" in outcome:
            loss_count += 1
        elif "b" in outcome:
            breakeven_count += 1
        else:
            return receive_rrr(update, context)

    total_trades = len(trades)
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
    avg_rr = total_rr / total_trades if total_trades > 0 else 0

    summary = (
        f"📊 *Your Performance Summary:*\n\n"
        f"📌 Total Trades: {total_trades}\n"
        f"✅ Wins: {win_count}\n"
        f"❌ Losses: {loss_count}\n"
        f"➖ Breakevens: {breakeven_count}\n\n"
        f"📈 *Win Rate:* {win_rate:.2f}%\n"
    )

    await update.message.reply_text(summary, parse_mode="Markdown")

async def view_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    journal_name = context.user_data.get("journal_name")
    if not journal_name:
        await update.message.reply_text("⚠️ You're not logged in. Use /start to begin.")
        return

    data = load_data()
    user_data = data.get(journal_name)
    trades = user_data.get("trades", [])

    if not trades:
        await update.message.reply_text("📭 No trades found in your journal.")
        return

    trade_buttons = []
    emoji_map = {"w": "🟢", "l": "🔴", "b": "⚪"}

    for i, trade in enumerate(trades):
        outcome = trade.get("outcome", "").lower()
        emoji = emoji_map.get(outcome, "❓")
        trade_label = f"{emoji} {trade['trade']}"
        trade_buttons.append([InlineKeyboardButton(trade_label, callback_data=f"view_trade_{i}")])

    # Show delete option
    trade_buttons.append([InlineKeyboardButton("🗑️ Delete a Trade", callback_data="delete_trade")])

    reply_markup = InlineKeyboardMarkup(trade_buttons)
    await update.message.reply_text("📒 Your Trades:", reply_markup=reply_markup)

    return MENU

async def handle_trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    journal_name = context.user_data.get("journal_name")
    data = load_data()
    trades = data[journal_name]["trades"]

    if query.data.startswith("view_trade_"):
        index = int(query.data.split("_")[-1])
        if 0 <= index < len(trades):
            trade = trades[index]
            caption = (
                f"*{trade['trade']}*\n"
                f"📸 Photo below\n"
                f"⚖️ RRR at Entry: {trade['rrr_entry']}\n"
                f"📊 Outcome: {trade['outcome'].upper()}"
            )
            await query.message.reply_photo(
                photo=trade['photo_file_id'],
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("⚠️ Trade not found.")
    elif query.data == "delete_trade":
        await list_trades_for_deletion(update, context)

async def list_trades_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    journal_name = context.user_data.get("journal_name")
    data = load_data()
    trades = data[journal_name]["trades"]

    delete_buttons = [
        [InlineKeyboardButton(f"Delete {trade['trade']}", callback_data=f"confirm_delete_{i}")]
        for i, trade in enumerate(trades)
    ]
    markup = InlineKeyboardMarkup(delete_buttons)
    await query.message.reply_text("Select a trade to delete:", reply_markup=markup)

async def confirm_trade_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[-1])
    journal_name = context.user_data.get("journal_name")
    data = load_data()

    try:
        removed_trade = data[journal_name]["trades"].pop(index)
        save_data(data)
        await query.message.reply_text(f"✅ {removed_trade['trade']} deleted.")
    except:
        await query.message.reply_text("❌ Failed to delete trade.")

# Main entry
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
    CHOOSING: [MessageHandler(filters.TEXT, choose_action)],
    REGISTER_NAME: [MessageHandler(filters.TEXT, register_name)],
    REGISTER_PW: [MessageHandler(filters.TEXT, register_password)],
    REGISTER_CONFIRM: [MessageHandler(filters.TEXT, register_confirm)],
    LOGIN_NAME: [MessageHandler(filters.TEXT, login_name)],
    LOGIN_PW: [MessageHandler(filters.TEXT, login_password)],
    MENU: [MessageHandler(filters.TEXT, handle_menu_choice)],
    PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
    RRR_ENTRY: [MessageHandler(filters.TEXT, receive_rrr)],
    OUTCOME: [MessageHandler(filters.TEXT, receive_outcome)],
},
    fallbacks=[],
)
    app.add_handler(conv_handler)

    app.add_handler(CallbackQueryHandler(handle_trade_callback, pattern="^view_trade_.*|delete_trade|confirm_delete_.*$"))
    
    print("Bot running...")
    app.run_polling()
   
def broadcast_prediction(message: str):
    with open("user_data.json", "r") as f:
        data = json.load(f)

    for username, info in data.items():
        chat_id = info.get("user_id")
        if chat_id:
            try:
                bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"❌ Failed to send to {username}: {e}")