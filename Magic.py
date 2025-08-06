import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F  # F вместо Text!
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram import F  # Волшебный фильтр!
import aiohttp
import os
from dotenv import load_dotenv

# === ИСПРАВЛЕН ПУТЬ К .ENV ===
# Заменили Murillo на Muxillo в пути
load_dotenv(r'C:\Users\Murillo\Desktop\Chat-Bot\.env')

# === НАСТРОЙКИ ===
# ИСПРАВЛЕНО: получаем переменные по имени, а не по значению
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GPTUNNEL_API_KEY = os.getenv("GPTUNNEL_API_KEY")
CHANNEL_USERNAME = "@" + os.getenv("CHANNEL_USERNAME")
# Проверка токенов
if not TELEGRAM_BOT_TOKEN:
    logging.error("Токен Telegram бота не найден! Проверьте .env файл")
    exit(1)

if not GPTUNNEL_API_KEY:
    logging.error("Ключ GPTunnel не найден! Проверьте .env файл")
    exit(1)

if not CHANNEL_USERNAME:
    logging.error("Имя канала не указано! Проверьте .env файл")
    exit(1)

bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# === ЛОГИ ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# === ГЛОБАЛЬНЫЕ ДАННЫЕ ===
user_data = {}

# === КЛАВИАТУРЫ ===
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🔮 Натальная карта')],
        [KeyboardButton(text='✨ Матрица судьбы')]
    ],
    resize_keyboard=True
)

subscription_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='✅ Я подписался')]],
    resize_keyboard=True
)

# === СТАРТ ===
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я делаю астрологический разбор по твоей дате рождения.\n\n"
        "Что тебе интересно?",
        reply_markup=start_keyboard
    )

# === ВЫБОР ТИПА ===
@dp.message(F.text.in_(['🔮 Натальная карта', '✨ Матрица судьбы']))
async def choose_type(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {
        'type': message.text,
        'step': 'waiting_subscription'
    }
    channel_name = os.getenv("CHANNEL_USERNAME")  # Получаем настоящее имя из .env
    channel_link = f"https://t.me/chislovayamagiya"  # Строим настоящую ссылку
    
    await message.answer(
    f"✨ Чтобы продолжить, подпишись на [наш канал]({channel_link})", 
    parse_mode="Markdown",
    reply_markup=subscription_keyboard

    )

# === ПРОВЕРКА ПОДПИСКИ ===
@dp.message(F.text == '✅ Я подписался')
async def check_subscription(message: types.Message):
    user_id = message.from_user.id
    
    try:
        # Проверяем статус подписки
        chat_member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        
        if chat_member.status in ['member', 'creator', 'administrator']:
            if user_id in user_data:
                user_data[user_id]['step'] = 'date'
            await message.answer("📅 Введи дату рождения в формате ДД.ММ.ГГГГ (например: 15.05.1990):")
        else:
            await message.answer("😔 Ты ещё не подписался. Подпишись и нажми кнопку снова.")
            
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        await message.answer("⚠️ Ошибка проверки подписки. Попробуй позже.")

# === ОБРАБОТКА ДАННЫХ ===
@dp.message()
async def handle_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Если пользователь не начал диалог
    if user_id not in user_data:
        await message.answer("Начни с команды /start")
        return
        
    current_step = user_data[user_id].get('step')
    
    # Обработка даты рождения
    if current_step == 'date':
        try:
            # УЛУЧШЕННАЯ ПРОВЕРКА ДАТЫ
            parts = text.split('.')
            if len(parts) != 3:
                raise ValueError
                
            day, month, year = map(int, parts)
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                raise ValueError
                
            user_data[user_id]['date'] = text
            
            # Для натальной карты запрашиваем время
            if user_data[user_id]['type'] == '🔮 Натальная карта':
                user_data[user_id]['step'] = 'time'
                await message.answer("⏰ Введи время рождения в формате ЧЧ:ММ (например: 14:30):")
            # Для матрицы сразу запрашиваем пол
            else:
                user_data[user_id]['step'] = 'gender'
                await message.answer("🚻 Введи свой пол (М или Ж):")
                
        except (ValueError, IndexError):
            await message.answer("❌ Неверный формат даты! Введи дату как ДД.ММ.ГГГГ (например: 01.01.2000)")
    
    # Обработка времени
    elif current_step == 'time':
        try:
            # УЛУЧШЕННАЯ ПРОВЕРКА ВРЕМЕНИ
            parts = text.split(':')
            if len(parts) != 2:
                raise ValueError
                
            hours, minutes = map(int, parts)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError
                
            user_data[user_id]['time'] = text
            user_data[user_id]['step'] = 'gender'
            await message.answer("🚻 Введи свой пол (М или Ж):")
            
        except (ValueError, IndexError):
            await message.answer("❌ Неверный формат времени! Введи время как ЧЧ:ММ (например: 09:15)")
    
    # Обработка пола
    elif current_step == 'gender':
        if text.lower() not in ['м', 'ж']:
            await message.answer("❌ Неверный пол! Введи только М или Ж")
            return
            
        user_data[user_id]['gender'] = text
        user_data[user_id]['step'] = 'city'
        await message.answer("🏙️ Введи город рождения:")
    
    # Обработка города
    elif current_step == 'city':
        user_data[user_id]['city'] = text
        await generate_response(message)
    
    else:
        await message.answer("⏳ Пожалуйста, дождись следующего шага или начни с /start")

# === ЗАПРОС К GPTUNNEL ===
async def generate_response(message: types.Message):
    user_id = message.from_user.id
    data = user_data[user_id]
    
    # Формируем промпт
    if data['type'] == '🔮 Натальная карта':
        prompt = (
            f"Сделай глубокий астрологический разбор натальной карты. "
            f"Дата рождения: {data['date']}, время: {data['time']}, "
            f"пол: {data['gender']}, город: {data['city']}. "
            "Анализ должен включать: знаки зодиака, аспекты планет, "
            "дома гороскопа, особенности личности и жизненные тенденции."
        )
    else:
        prompt = (
            f"Сделай глубокий разбор матрицы судьбы. "
            f"Дата рождения: {data['date']}, пол: {data['gender']}, "
            f"город: {data['city']}. Проанализируй: энергетику личности, "
            "предназначение, финансовый поток и отношения."
        )
    
    # Отправляем запрос
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                'https://gptunnel.ru/v1/chat/completions',
                headers={
                    "Authorization": f"Bearer {GPTUNNEL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты профессиональный астролог. Дай подробный разбор как на личной консультации."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            
            if response.status == 200:
                result = await response.json()
                analysis = result['choices'][0]['message']['content']
                
                full_response = (
                    f"{analysis}\n\n"
                    "✨ Хочешь узнать больше?\n"
                    f"Переходи по ссылке в шапке канала {CHANNEL_USERNAME} "
                    "для полного разбора с ответами на твои вопросы!"
                )
                
                await message.answer(full_response)
                
            else:
                error = await response.text()
                logging.error(f"GPTunnel error: {response.status} - {error}")
                await message.answer("⚠️ Ошибка генерации ответа. Попробуй позже.")
                
        except Exception as e:
            logging.exception("GPTunnel request failed")
            await message.answer("⛔ Произошла техническая ошибка. Попробуй еще раз через 5 минут.")

# === ЗАПУСК БОТА ===
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.info("Бот запущен!")
    asyncio.run(main())
    