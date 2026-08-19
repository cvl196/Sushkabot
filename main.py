import telebot 
import dotenv
import sqlite3
import datetime
import os 

Api = os.getenv('API_KEY')

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
        keyboard.add(telebot.types.InlineKeyboardButton(text = item[0] + ' ' + item[2], callback_data=f'del%{item[1]}'))
    keyboard.add(telebot.types.InlineKeyboardButton(text = 'В главное меню',callback_data='back'))
    return keyboard


def create_today_table():
    date = datetime.datetime.now().strftime('_%d_%m_%y')
    with sqlite3.connect('database.db') as conn: 
        cu = conn.cursor()
        cu.execute(f'CREATE TABLE IF NOT EXISTS meals{date} (chat_id INTEGER, meal TEXT, info TEXT)')
        conn.commit()
        cu.close



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
            bot.edit_message_text(chat_id=call.message.chat.id, text = "Укажите прием пищи и кбжу в формате:\nОбед 500 50 20 45", message_id=call.message.id,reply_markup=create_keyboard_back())
            bot.register_next_step_handler(call.message, add_meal)
        except Exception as e: 
            print(e)

    elif call.data=='back':
        try:
            bot.edit_message_text(message_id=call.message.id,chat_id = call.message.chat.id, text = "Добрый день, выберите действие:", reply_markup=create_keyboard_main())
        except Exception as e :
            print(e)
            
    elif call.data == "mypr":
        try:
            date = datetime.datetime.now().strftime("_%d_%m_%y")

            with sqlite3.connect('database.db') as conn:
                cu = conn.cursor() 
                cu.execute(f"CREATE TABLE IF NOT EXISTS meals{date} (chat_id INTEGER, meal TEXT, info TEXT)")
                cu.execute(f"SELECT meal,info FROM MEALS{date} WHERE chat_id = ?", (call.message.chat.id,))
                meals = cu.fetchall()
                if len(meals)>0:                 
                    cu.execute('SELECT target FROM users WHERE chat_id =?',(call.message.chat.id,))
                    text = "<b>Ваши приемы:</b>\n"
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
                    buf = ['','','']
                    buf[0]= f'Сумма за день: {k} {b} {zh} {u}\n' 
                    target=cu.fetchall()
                    if len(target)>0:
                        target = target[0][0]
                        buf[1]=f'\nЦель: {target}\n'
                        target = list(map(int,target.split()))
                        buf[2]=f'<b>Остаток на сегодня: {target[0]-k if target[0]-k>0 else 0} {target[1]-b if target[1]-b>0 else 0 } {target[2]-zh if target[2]-zh>0 else 0} {target[3]-u if target[3]-u>0 else 0 }</b>\n'
                    text+=buf[1]
                    text+=buf[0]
                    text+=buf[2]                   
                    
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id = call.message.id,text = text, reply_markup=create_keyboard_back(),parse_mode="HTML")
                else: 
                    bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.id,text='Приемов не найдено',reply_markup=create_keyboard_back())
                   
        except Exception as e :
            print(e)

    elif call.data == 'del': 
        try:
            create_today_table()
            date = datetime.datetime.now().strftime("_%d_%m_%y")
            ch_id = call.message.chat.id 
            with sqlite3.connect('database.db') as conn: 
                cu = conn.cursor()
                items = [*cu.execute(f'SELECT meal,rowid,info FROM meals{date} WHERE chat_id = ?',(ch_id,))]
                
                cu.close()
            if len(items)>0: 
                bot.edit_message_text(chat_id=ch_id, message_id = call.message.id,text='Выберите прием для удаления', reply_markup=create_keyboard_del(items))
            else:
                bot.edit_message_text(chat_id=ch_id, message_id = call.message.id,text='Приемов не найдено', reply_markup=create_keyboard_back())
                
            
        except Exception as e: 
            print(e)

    elif call.data[0:4]=='del%':
        try: 
            rod = call.data.split('%')[1]
            with sqlite3.connect('database.db') as conn: 
                date = datetime.datetime.now().strftime("_%d_%m_%y")
                cu = conn.cursor()
                cu.execute(f'DELETE FROM meals{date} WHERE rowid=?',(rod,))
                conn.commit()
                cu.close()
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text = 'Прием был успешно удален',reply_markup=create_keyboard_back())
        except Exception as e: 
            print(e)

    elif call.data == 'target':
        try: 
            bot.edit_message_text(chat_id=call.message.chat.id,message_id = call.message.id, text='Напишите вашу цель кбжу через пробел\n Пример: 2000 150 70 200',reply_markup=create_keyboard_back())
            bot.register_next_step_handler(call.message,add_target)
        except Exception as e:
            print(e)


def add_meal(message):
    try: 
        sp = message.text.split(" ",1)
        if len(sp)>1:
            meal, info = sp
            infoch = [k.isdigit() for k in info.split()]
        
            if all(infoch) and len(infoch)==4:
                info = ' '.join(info.split())
                date = datetime.datetime.now().strftime("_%d_%m_%y")
                conn = sqlite3.connect('database.db')
                cu = conn.cursor()
                cu.execute(f"CREATE TABLE IF NOT EXISTS meals{date} (chat_id INTEGER, meal TEXT, info TEXT)")
                cu.execute(f"INSERT INTO meals{date} (chat_id, meal, info) VALUES (?, ?, ?)", (message.chat.id, meal.strip(), info.strip()))
                conn.commit()
                cu.close()
                conn.close()
                bot.send_message(message.chat.id, 'Прием успешно добавлен!')
                bot.send_message(message.chat.id, "Добрый день, выберите действие:", reply_markup=create_keyboard_main())
            else: 
                        bot.send_message(chat_id=message.chat.id, text = "Неверный тип данных\nУкажите прием пищи и кбжу в формате:\nОбед 500 50 20 45",reply_markup=create_keyboard_back() )
                        bot.register_next_step_handler(message, add_meal)
        else: 
            bot.send_message(chat_id=message.chat.id, text = "Неверный тип данных\nУкажите прием пищи и кбжу в формате:\nОбед 500 50 20 45",reply_markup=create_keyboard_back() )
            bot.register_next_step_handler(message, add_meal)
    except Exception as e:
        print(e)
    
    
def add_target(message):
    try:
        kbzhu = ' '.join(message.text.split())
        kbzhuch = kbzhu.split()
        if len(kbzhuch)==4 and all(k.isdigit() for k in kbzhuch):
            with sqlite3.connect('database.db') as conn: 
                cu = conn.cursor()
                cu.execute('SELECT * FROM users WHERE chat_id=?',(message.chat.id,))
                if len([*cu.fetchall()])>0:
                    cu.execute('UPDATE users SET target=? WHERE chat_id=?',(kbzhu,message.chat.id))
                else: 
                    cu.execute('INSERT INTO users (chat_id,target) VALUES (?,?)',(message.chat.id,kbzhu))
                conn.commit()
                cu.close()
                bot.send_message(chat_id=message.chat.id, text = 'Цель успешно установлена',reply_markup=create_keyboard_back())
        else: 
            bot.send_message(chat_id=message.chat.id,text='Неверный формат данных \nПример: 2000 150 70 200')
            bot.register_next_step_handler(message,add_target)
    except Exception as e: 
        print(e)

        

bot.infinity_polling()
