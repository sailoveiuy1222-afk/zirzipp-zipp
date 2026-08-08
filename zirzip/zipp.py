import asyncio
import aiohttp
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8766056170:AAFcp4brmg106A2JrDzbSX6T14gRCC9N07w"

# State & Data သိုလှောင်ရန် Global Variables
scanning = False
stats = {
    "tried": 0,
    "hits": 0,
    "speed": 0,
    "hit_codes": []
}

# ၁။ Server သို့ စာပို့ပြီး Code မှန်မမှန် စစ်ဆေးပေးသည့် Function
async def check_code_api(session, code):
    # စစ်ဆေးလိုသော Web API / Endpoint URL ကို ဒီနေရာမှာ ထည့်ရပါမည်
    target_url = f"https://example.com/api/verify?code={code}"
    
    try:
        # Request အား Timeout 5 စက္ကန့် သတ်မှတ်၍ ပို့ခြင်း
        async with session.get(target_url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                # Server တုံ့ပြန်မှုပေါ်မူတည်၍ True / False ပြန်ပေးခြင်း
                return data.get("status") == "success"
    except Exception:
        pass
    return False

# ၂။ Telegram Message ကို ၁.၅ စက္ကန့်တိုင်း UI Update လုပ်ပေးသည့် Function
async def update_ui_loop(query):
    global scanning, stats
    start_time = time.time()
    
    while scanning:
        elapsed = time.time() - start_time
        # Speed တွက်ချက်ခြင်း (Checks per minute - c/m)
        stats["speed"] = int((stats["tried"] / elapsed) * 60) if elapsed > 0 else 0
        
        # ရရှိထားသော Hit Code များကို စာရင်းထုတ်ခြင်း
        hits_text = "\n".join([f"• `{c}`" for c in stats["hit_codes"][-5:]]) if stats["hit_codes"] else "Waiting..."
        
        message_text = (
            f"⚡ **Scanner Running** ⚡\n\n"
            f"🎯 **Tried:** {stats['tried']}\n"
            f"✅ **Hits:** {stats['hits']}\n"
            f"⚡ **Speed:** {stats['speed']} c/m\n\n"
            f"🔥 **Hit Codes:**\n{hits_text}"
        )
        
        stop_button = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop", callback_data="stop_scan")]])
        
        try:
            await query.edit_message_text(text=message_text, reply_markup=stop_button, parse_mode="Markdown")
        except Exception:
            pass # Message တူနေပါက Error မတက်စေရန်
            
        await asyncio.sleep(1.5)

# ၃။ Code များကို အစဉ်လိုက် ပတ်စစ်ပေးသည့် Main Engine
async def start_scanner_engine(query):
    global scanning, stats
    scanning = True
    stats = {"tried": 0, "hits": 0, "speed": 0, "hit_codes": []}
    
    # UI ပြောင်းလဲခြင်းကို Background Task အဖြစ် စတင်မည်
    asyncio.create_task(update_ui_loop(query))
    
    async with aiohttp.ClientSession() as session:
        # ဂဏန်း ၆ လုံးပါသော Code များကို စမ်းသပ်သည့် Loop
        for number in range(100000, 999999):
            if not scanning:
                break
                
            code_str = str(number)
            stats["tried"] += 1
            
            # API သို့ စစ်ဆေးရန် ပို့ခြင်း
            is_valid = await check_code_api(session, code_str)
            if is_valid:
                stats["hits"] += 1
                stats["hit_codes"].append(code_str)
                
            await asyncio.sleep(0.01) # Server အား မပြိုကျစေရန် စက္ကန့်ပိုင်း ပိုင်းခြားထားခြင်း

# Command & Button Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Start Scan", callback_data="start_scan")]])
    await update.message.reply_text("⚡ **Code Scanner Bot**\nစတင်ရန် ခလုတ်ကို နှိပ်ပါ။", reply_markup=keyboard, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scanning
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_scan":
        asyncio.create_task(start_scanner_engine(query))
    elif query.data == "stop_scan":
        scanning = False
        await query.edit_message_text("🛑 **Scanner ရပ်တန့်လိုက်ပါပြီ။**")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot starting...")
    app.run_polling()
