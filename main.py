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

def create_keyboard_back():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text = 'В главное меню',callback_data='back'))
    return keyboard

def create_keyboard_del(items): 
    keyboard = telebot.types.InlineKeyboardMarkup()
    for item in items: 
        keyboard.add(telebot.types.InlineKeyboardButton(text = item[0], callback_data=f'del%{item[1]}'))
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
        try:
            bot.send_message(call.message.chat.id, "Укажите прием пищи и кбжу в формате: Обед: 500 50 20 45")
            bot.register_next_step_handler(call.message, add_meal)
        except: 
            bot.send_message(call.message.chat.id,'Неизвестная ошиибка')

    elif call.data=='back':
        try:
            bot.send_message(call.message.chat.id, "Добрый день, выберите действие:", reply_markup=create_keyboard_main())
        except:
            bot.send_message(call.message.chat.id,'Неизвестная ошибка')
            
    elif call.data == "mypr":
        try:
            date = datetime.datetime.now().strftime("_%d_%m_%y")

            with sqlite3.connect('database.db') as conn:
                cu = conn.cursor() 
                cu.execute(f"CREATE TABLE IF NOT EXISTS meals{date} (chat_id INTEGER, meal TEXT, info TEXT)")
                cu.execute(f"SELECT meal,info FROM MEALS{date} WHERE chat_id = ?", (call.message.chat.id,))
                meals = cu.fetchall()
                if len(meals)>0:
                    text = "Ваши приемы:\n"
                    k = 0 
                    b = 0 
                    zh = 0 
                    u = 0 
                    for meal in meals: 
                        text += f"{meal[0]}: {meal[1]}\n"
                        kbzhu = list(map(int,meal[1].split()))
                        k+=kbzhu[0]
                        b+=kbzhu[1]
                        zh+=kbzhu[2]
                        u+=kbzhu[3]
                    text += f'Сумма за день: {k} {b} {zh} {u}'
                    bot.send_message(call.message.chat.id, text,)
                else: 
                    bot.send_message(chat_id=call.message.chat.id,text='Приемов не найдено')
                    bot.send_message(chat_id=call.message.chat.id, text = "Добрый день, выберите действие:", reply_markup=create_keyboard_main())
        except:
            bot.send_message(call.message.chat.id,'Неизвестная ошибка')

    elif call.data == 'del': 
        try:
            date = datetime.datetime.now().strftime("_%d_%m_%y")
            ch_id = call.message.chat.id 
            with sqlite3.connect('database.db') as conn: 
                cu = conn.cursor()
                items = [*cu.execute(f'SELECT meal,rowid FROM meals{date} WHERE chat_id = ?',(ch_id,))]
                cu.close()
            bot.send_message(chat_id=ch_id, text='Выберите прием для удаления', reply_markup=create_keyboard_del(items))
        except: 
            bot.send_message(call.message.chat.id,'неизвестная ошибка')

    elif call.data[0:4]=='del%':
        try: 
            rod = call.data.split('%')[1]
            with sqlite3.connect('database.db') as conn: 
                date = datetime.datetime.now().strftime("_%d_%m_%y")
                cu = conn.cursor()
                cu.execute(f'DELETE FROM meals{date} WHERE rowid=?',(rod,))
                conn.commit()
                cu.close()
            bot.send_message(chat_id=call.message.chat.id, text = 'Прием был успешно удален',reply_markup=create_keyboard_back())
        except: 
            bot.send_message(call.message.chat.id,'неизвестная ошибка',reply_markup=create_keyboard_back())

    elif call.data == 'target':
        try: 
            bot.send_message(chat_id=call.message.chat.id,text='Напишите вашу цель кбжу через пробел\n Пример: 43 23 43 2')
            bot.register_next_step_handler(call.message,add_target)
        except:
            pass


def add_meal(message):
    try: 
         meal, info = message.text.split(":")
    except :
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, используйте формат: Обед: 500 50 20 45")
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
    
def add_target(message):
    
    kbzhu = message.text
    kbzhuch = kbzhu.split()
    if len(kbzhuch) and all(k.isdigit() for k in kbzhuch):
        with sqlite3.connect('database.db') as conn: 
            cu = conn.cursor()
            cu.execute('SELECT * FROM users WHERE chat_id=?',(message.chat.id,))
            if len([*cu.fetchall()])>0:
                cu.execute('UPDATE users SET VALUES target=? WHERE chat_id=?',(kbzhu,message.chat.id))
            else: 
                cu.execute('INSERT INTO users (chat_id,target) VALUES (?,?)',(message.chat.id,kbzhu))
            conn.commit()
            cu.close()
    else: 
        bot.send_message(chat_id=message.chat.id,text='Неверный формат данных \n Пример: 43 23 43 2')
        bot.register_next_step_handler(message,add_target)

        

bot.infinity_polling()
