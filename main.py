import asyncio
from telethon import TelegramClient, events
from telethon.errors import RPCError, UserNotParticipantError, FloodWaitError
import requests
from datetime import datetime, timedelta, timezone
import edge_tts

api_id = 21889272
api_hash = "61f2299e275c9f1d1f8151e7010b23a6"
change_font = False
commands_on = False
accessed_users = {

}
commands_list = {
}

client = TelegramClient("my_account", api_id, api_hash)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.speak (.+) (.+)"))
async def speak_handler(event):
    await client.delete_messages(event.chat_id, event.message.id)
    text = event.pattern_match.group(1).strip()
    lang = event.pattern_match.group(2).strip()
    voice = "en-US-GuyNeural" if lang == 'en' else "ru-RU-DmitryNeural"
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save("voice.mp3")
    if event.reply_to_msg_id:
        await client.send_file(event.chat_id, "voice.mp3", voice_note=True, reply_to=event.reply_to_msg_id)
    else:
        await client.send_file(event.chat_id, "voice.mp3", voice_note=True)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.font"))
async def font_handler(event):
    global change_font
    change_font = not change_font
    await client.delete_messages(event.chat_id, event.message.id)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.id'))
async def id_handler(event):
    if event.message.reply_to_msg_id:
        await event.message.edit(f"ID пользователя: {event.message.reply_to_message.from_user.id}\nID чата: {event.chat_id}")
    else:
        await event.message.edit(f"ID чата: {event.chat_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.weather (.+)'))
async def weather_handler(event):
    try:
        api_key = "e845771457a6fbeb663c618fbe5d9df1"
        city = event.pattern_match.group(1)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            offset_seconds = data["timezone"]
            tz = timezone(timedelta(seconds=offset_seconds))
            time = datetime.now(tz)
            temp = data["main"]["temp"]
            country = data["sys"]["country"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind_speed = data["wind"]["speed"]
            visibility_meters = data["visibility"]
            visibility_km = visibility_meters / 1000
            cloudy = data["clouds"]["all"]
            sunrise_unix = data["sys"]["sunrise"]
            sunrise = datetime.fromtimestamp(sunrise_unix, tz=timezone.utc)
            sunset_unix = data["sys"]["sunset"]
            sunset = datetime.fromtimestamp(sunset_unix, tz=timezone.utc)
            description = data["weather"][0]["description"]
            tbp = ""
            tbp += (
                f"""Прогноз погоды для: {city}, {country}\n"""
                f"""Время: {time.strftime("%H:%M %d-%m-%Y")}\n"""
                f"""Температура: {temp}°C\n"""
                f"""Ощущается как: {feels_like}°C\n"""
                f"""Состояние: {description}\n"""
                f"""Влажность: {humidity}\n"""
                f"""Давление: {pressure} гПа\n"""
                f"""Видимость: {visibility_km} км\n"""
                f"""Облачность: {cloudy}%\n"""
                f"""Ветер: {wind_speed} км/ч\n"""
                f"""Восход: {sunrise.strftime("%H:%M %d-%m-%Y")}\n"""
                f"""Закат: {sunset.strftime("%H:%M %d-%m-%Y")}\n"""
                )
            await event.message.edit(tbp)
        else:
            print("Не удалось получить данные о погоде. Проверьте название города или API-ключ.")
    except Exception as e:
        print(e)

@client.on(events.NewMessage(pattern=r"\.cur (\d+) (.+)"))
async def currency_handler(event):
    amount = int(event.pattern_match.group(1))
    base_currency = event.pattern_match.group(2)
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    USD_currency = "USD"
    EUR_currency = "EUR"
    PLN_currency = "PLN"
    AZN_currency = "AZN"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if AZN_currency in data['rates']:
            rateAZN = data['rates'][AZN_currency]
            rateUSD = data['rates'][USD_currency]
            rateEUR = data['rates'][EUR_currency]
            ratePLN = data['rates'][PLN_currency]
            tbp = f"""<b>{amount} {base_currency}:</b>\n\n"""
            tbp += f"""{"{:.2f}".format(rateUSD*amount)} USD\n"""
            tbp += f"""{"{:.2f}".format(rateEUR*amount)} EUR\n"""
            tbp += f"""{"{:.2f}".format(ratePLN*amount)} PLN\n"""
            tbp += f"""{"{:.2f}".format(rateAZN*amount)} AZN\n"""
            await event.edit(tbp, parse_mode='html')
        else:
            print(f"Ошибка: валюта {AZN_currency} не найдена.")
    else:
        print("Ошибка при получении данных о курсе валют.")

@client.on(events.NewMessage(pattern=r"\.spam (\d+) (.+)"))
async def spam_handler(event):
    await client.delete_messages(event.chat_id, event.message.id)
    count = int(event.pattern_match.group(1))
    text = event.pattern_match.group(2)
    for _ in range(count):
        try:
            await client.send_message(event.chat_id, text)
            await asyncio.sleep(0.05)
        except RPCError as rcpe:
            await event.reply(f"Ошибка при отправке сообщения: {rcpe}")
            break
        except FloodWaitError as fwe:
            await event.reply(f"{fwe.message}")
            break

@client.on(events.NewMessage(pattern=r"\.command (\d+(?:\.\d+)?) (.+)"))
async def command_handler(event):
    await client.delete_messages(event.chat_id, event.message.id)
    global commands_on
    global commands_list
    commands_on = True
    interval = float(event.pattern_match.group(1))
    command = event.pattern_match.group(2)
    commands_list[command] = interval
    while commands_on and command in commands_list:
        await client.send_message(event.chat_id, command)
        await asyncio.sleep(interval*60+1)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.comlist"))
async def comlist_handler(event):
    global commands_list
    if commands_list:
        command_list = "\n".join([f"{i+1}. {command}" for i, command in enumerate(commands_list)])
        await event.edit("Список команд:\n" + command_list)
    else:
        await event.message.edit("Список команд пуст.")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.stop (\d+)"))
async def stop_handler(event):
    global commands_on
    global commands_list
    commands_on = False
    try:
        stop_index = int(event.pattern_match.group(1)) - 1
        if 0 <= stop_index < len(commands_list):
            command = list(commands_list.keys())[stop_index]
            await asyncio.sleep(3)
            commands_list.pop(command)
            await event.message.edit(f'Команда "{command}" остановлена!')
        else:
            await event.message.edit("Указанный номер команды недействителен.")
    except ValueError:
        await event.message.edit("Введите корректный номер команды.")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.help"))
async def help_handler(event):
    help_text = (
                ".command <время в минутах> <команда> - устанавливает команду для выполнения через интервал.\n"
                ".comlist - список активированных команд\n"
                ".stop <команда> - останавливает выполнение команд.\n"
                ".list - показывает список участников.\n"
                ".call - зовет всех участников\n"
                ".weather <город> - показывает погоду.\n"
                ".cur <сумма> <валюта> - переводит валюту.\n"
                ".ban <участник> || .ban - забанить участника\n"
                ".banall - банит всех участников.\n"
                ".id - показывает ID пользователя.\n"
                ".type <текст> - эффект печати.\n"
                ".spam <количество> <текст> - спам.\n"
                ".font - меняет шрифт на жирный (введите повторно для отключения).\n"
                ".help - помощь по юзерботу.\n"
                ".exit - завершить сеанс."
            )
    await event.message.edit(help_text)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.exit"))
async def list_handler(event):
    await event.edit('Exit.')
    await client.log_out()

@client.on(events.NewMessage(outgoing=True, pattern=r"\.list"))
async def list_handler(event):
    chat_id = event.message.chat_id
    members = await client.get_participants(chat_id)
    member_list = [
        f"{member.first_name} @{member.username}" if member.username else f"{member.first_name} <a href=\"tg://user?id={member.id}\">{member.id}</a>"
        for member in members if not member.bot
    ]
    total_members = len(member_list)
    await event.message.edit(f"Участники чата ({total_members}):\n" + "\n".join(member_list), parse_mode='html')

@client.on(events.NewMessage(outgoing=True, pattern=r"\.call"))
async def call_handler(event):
    chat_id = event.message.chat_id
    members = await client.get_participants(chat_id)
    member_list = [
        f"<a href=\"tg://user?id={member.id}\">︎︎︎</a>"
        for member in members if not member.bot
    ]
    await event.message.edit(f"".join(member_list), parse_mode='html')

@client.on(events.NewMessage(outgoing=True, pattern=r"\.ban (.+)"))
async def ban_handler(event):
    user_input = event.pattern_match.group(1).strip()
    user_id = None
    try:
        if user_input.isdigit():
            user_id = int(user_input)
        else:
            user = await client.get_entity(user_input)
            user_id = user.id
    except ValueError:
        await event.reply("Ошибка: Введите действительный ID или имя пользователя.")
        return
    except Exception as e:
        await event.reply(f"Ошибка: {e}")
        return
    try:
        await client.edit_permissions(event.chat_id, user_id, view_messages=False)
        await event.message.edit(f"Пользователь {user_input} забанен.")
    except UserNotParticipantError:
        await event.message.edit("Пользователь не находится в чате.")
    except RPCError as e:
        await event.message.edit(f"Ошибка при бане пользователя: {e}")
    except Exception as e:
        await event.message.edit(f"{e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.banall"))
async def banall_handler(event):
    await client.delete_messages(event.chat_id, event.message.id)
    chat_id = event.message.chat_id
    members = await client.get_participants(chat_id)
    for member in members:
        if member.id != 892742378:
            try:
                await client.edit_permissions(chat_id, member.id, view_messages=False)
                print(f"Пользователь {member.first_name} забанен.")
            except UserNotParticipantError:
                print(f"Пользователь {member.first_name} уже покинул чат.")
            except RPCError as e:
                print(f"Не удалось забанить {member.first_name}: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.call(\n.+)"))
async def newcall_handler(event):
    text = event.pattern_match.group(1)
    chat_id = event.message.chat_id
    members = await client.get_participants(chat_id)
    member_list = [
        f"[︎︎︎](tg://user?id={member.id})"
        for member in members if not member.bot
    ]
    await event.message.edit("".join(member_list) + f"\n{text}", parse_mode='md')
    i = 0
    while i <= 5:
        await client.send_message(chat_id, "".join(member_list) + f"\n{text}", parse_mode='md')
        i += 1


@client.on(events.NewMessage(outgoing=True, pattern=r"\.type (.+)"))
async def type_handler(event):
    text = event.pattern_match.group(1)
    tbp = ""
    typing_symbol = "▒"
    for char in text:
        await event.edit(tbp + typing_symbol)
        tbp += char
        await asyncio.sleep(0.3)
        await event.edit(tbp)
        await asyncio.sleep(0.1)

@client.on(events.NewMessage(outgoing=True, pattern=r"\.ncall (.+)"))
async def ncall_handler(event):
    text = event.pattern_match.group(1)
    chat_id = event.message.chat_id
    members = await client.get_participants(chat_id)
    member_list = [
        f"<a href=\"tg://user?id={member.id}\">︎︎︎</a>"
        for member in members if not member.bot
    ]
    await event.message.edit(f"{text}" + f"".join(member_list), parse_mode='html')

@client.on(events.NewMessage(outgoing=True))
async def handler(event):
    global change_font
    if event.message and event.message.text and change_font and event.message.text != ".font":
        await event.message.edit(f'__**{event.message.text}**__')

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()