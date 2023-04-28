import discord
from discord.ext import commands
from config import token   # Берём токен бота из файла config
import os
import yt_dlp as youtube_dl

# Импортируем необходимые библиотеки для работы бота. Не забыть скачать библиотеку PyNaCl используя "pip install pynacl"


bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())  # Задаём префикс для всех команд бота '/'.
# Для того чтобы вызвать бота, необходимо перед всеми командами ставить данный символ


@bot.event
async def on_ready():       # Сообщение, которое показывается нам, говорящее, что бот запустился.
    print('Бот работает!')


server, server_id, name_channel = None, None, None    # Задаём переменные, которые в будущем будут показывать,
# на каком сервере и в каком канале находится бот
domains = ['https://www.youtube.com/', 'http://www.youtube.com/', 'https://youtu.be/', 'http://youtu.be/']
# Домены, на которые реагирует бот


async def check_domains(link):  # Данная функция проверяет корректность ссылки, которую вписал пользователь
    for x in domains:
        if link.startswith(x):   # Если она начинается с доменов, что представлены в списке выше, то всё хорошо
            return True
    return False


# Комманда для проигрывания музыки
@bot.command()
async def play(message, *, command=None):
    """Воспроизводит музыку"""    # Эти описания будут видны при вызове /help пользователем
    global server, server_id, name_channel
    author = message.author   # Извлекаем данные об авторе
    if command == None:
        server = message.guild    # Извлекаем массив данных о сервере, чтобы бот потом к нему подключился
        name_channel = author.voice.channel.name   # Узнаём название канала, откуда пользователь вызывает бота
    params = command.split(' ')  # Разделяем по пробелам команду, заданную пользователем, создавая массив
    if len(params) == 1:   # Воспроизводим локальный файл
        sourse = params[0]
        server = message.guild
        name_channel = message.author.voice.channel.name
        voice_channel = discord.utils.get(server.voice_channels, name=name_channel)
        print('p1')  # Заметка для нас, что эта ветка сработала
    elif len(params) == 3:  # Подключаемся по заданному id канала и воспроизводим музыку
        # Далее извлекаем информацию из команды
        server_id = params[0]  # id сервера
        voice_id = params[1]  # id войс-чата
        sourse = params[2]  # Ссылка на музыку
        try:
            server_id = int(server_id)  # Проверяем корректность id сервера
            voice_id = int(voice_id)  # и id войс-чата
        except:
            await message.channel.send(f'{author.mention}, id сервера или голосового канала должно быть целочисленным.')
            # Упоминаем автора, чтобы он увидел, что его команда неверна
            return
        print('p3')  # Заметка для нас, что эта ветка сработала
        server = bot.get_guild(server_id)  # Передаём сервер id
        voice_channel = discord.utils.get(server.voice_channels, id=voice_id)
    else:
        await message.channel.send(f'{author.mention}, некорректно введённая команда.')  # Если ничего не сработало,
        # то введённая команда некорректна
        return

    voice = discord.utils.get(bot.voice_clients, guild=server)  # Информация о подключении к войс-чату
    if voice is None:
        await voice_channel.connect()  # Если бот не подключён, подключаем
        voice = discord.utils.get(bot.voice_clients, guild=server)  # Новая информация о подключении к войс-чату

    if sourse == None:   # Если ничего не пришло, то воспроизводить ничего и не будем
        pass
    elif sourse.startswith('http'):   # Если у нас передана ссылка
        if not await check_domains(sourse):
            await message.channel.send(f'{author.mention}, неверная ссылка.')  # Если пользователь дал ссылку не с ютуба
            return

        song_there = os.path.isfile('song.mp3')  # Переменная, говорящая, на месте ли файл
        try:
            if song_there:     # Если файл есть, то его можно удалить
                os.remove('song.mp3')
        except PermissionError:
            await message.channel.send('Недостаточно прав для удаления файла.')
            return

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': "mp3",
                    'preferredquality': '192',
                }
            ],
        }
        # Здесь представлена характеристика файла, который мы скачаем

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([sourse])        # Скачиваем файл по ссылке с ютуба
        for file in os.listdir('./'):
            if file.endswith('.mp3'):
                os.rename(file, 'song.mp3')
        # Каждый раз, когда скачиваем файл, мы его переименовываем в конкретное название,
        # а потом каждый раз перезаписываем его
        voice.play(discord.FFmpegPCMAudio('song.mp3'))  # Проигрываем песню
    else:
        voice.play(discord.FFmpegPCMAudio(sourse))


# Команда, отключающая бота
@bot.command()
async def leave(message):
    """Отключает бота от войс-чата"""
    global server, name_channel
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_connected():  # Проверяем, подключён ли бот. Если нет, то смысла отключать его уже нет.
        await voice.disconnect()
    else:
        await message.channel.send(f'{message.author.mention}, бот уже отключён от голосового канала.')


# Команда, ставящая музыку на паузу
@bot.command()
async def pause(message):
    """Останавливает воспроизведение музыки"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_playing():  # Проверяем, на паузе ли уже бот
        voice.pause()
    else:
        await message.channel.send(f'{message.author.mention}, музыка не воспроизводится.')


# Команда, продолжающая воспроизведение музыки
@bot.command()
async def resume(message):
    """Продолжает воспроизведение музыки"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    if voice.is_paused():  # Проверяем, воспроизводится ли бот
        voice.resume()
    else:
        await message.channel.send(f'{message.author.mention}, музыка уже воспроизводится.')


# Команда, сбрасывающая поставленную песню
@bot.command()
async def stop(message):
    """Сбрасывает поставленную музыку"""
    voice = discord.utils.get(bot.voice_clients, guild=server)
    voice.stop()


bot.run(token)  # Запускаем бота с нашим токеном
