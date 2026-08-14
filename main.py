import telebot 
import dotenv
import sqlite3
import datetime


Api = dotenv.get_key('.env', 'API_KEY')

bot = telebot.TeleBot(Api)
conn = sqlite3.connect('database.db')
cu = conn.cursor() 
cu.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, target TEXT)''')
cu.close()
conn.commit()
conn.close()

def create_keyboard_main():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text="Добавить прием", callback_data="add"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить прием", callback_data="del"))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Мои приемы", callback_data="mypr")) 
    keyboard.add(telebot.types.InlineKeyboardButton(text="Настроить цель", callback_data="target")) 
    return keyboard



@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_message(message.chat.id    , """\
Добрый день, выберите действие:
""",reply_markup=create_keyboard_main())


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, "Добрый день, выберите действие:", reply_markup=create_keyboard_main())

@bot.callback_query_handler(func=lambda call: True)
def test_callback(call): 
    if call.data == "add":
        bot.send_message(call.message.chat.id, "Укажите прием пищи и кбжу в формате: Обед: 500 50 20 45")
        bot.register_next_step_handler(call.message, add_meal)
    if call.data == "mypr":
        date = datetime.datetime.now().strftime("_%d_%m_%y")

        with sqlite3.connect('database.db') as conn:
            cu = conn.cursor() 
            cu.execute(f"SELECT meal,info FROM MEALS{date} WHERE chat_id = ?", (call.message.chat.id,))
            meals = cu.fetchall()
            text = "Ваши приемы пищи:\n"
            for meal in meals: 
                text += f"{meal[0]}: {meal[1]}\n"
            bot.send_message(call.message.chat.id, text)
            
    


def add_meal(message):
    try: 
         meal, info = message.text.split(":")
    except :
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, используйте формат: Обед: 500/50/20/45")
        bot.register_next_step_handler(message, add_meal)
    date = datetime.datetime.now().strftime("_%d_%m_%y")
    conn = sqlite3.connect('database.db')
    cu = conn.cursor()
    cu.execute(f"CREATE TABLE IF NOT EXISTS meals{date} (chat_id INTEGER, meal TEXT, info TEXT)")
    cu.execute(f"INSERT INTO meals{date} (chat_id, meal, info) VALUES (?, ?, ?)", (message.chat.id, meal.strip(), info.strip()))
    conn.commit()
    cu.close()
    conn.close()
    bot.send_message(message.chat.id, 'Прием пищи успешно добавлен!')
    bot.send_message(message.chat.id, "Добрый день, выберите действие:", reply_markup=create_keyboard_main())
    
    

bot.infinity_polling()
