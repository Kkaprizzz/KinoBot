from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database, subCheck_logic

router = Router()

class SearchStates(StatesGroup):
    Searching = State()
    NotSearching = State()

async def clear_state(state: FSMContext):
    await state.set_state(SearchStates.NotSearching)

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if await subCheck_logic.check_all_subscriptions(user_id):
        await callback.message.delete()
        await state.set_state(SearchStates.Searching)
        await callback.message.answer("✅ <b>Отлично!</b>\nТеперь введи код фильма в формате (1234) ниже ⬇️", parse_mode="HTML")

    else:
        await callback.answer("❌ Вы ещё не подписались на все каналы!", show_alert=True)

@router.message(F.text.contains("🔎 Поиск по коду"))
async def searchFilmHandler(message: Message, state: FSMContext):
    userId = message.from_user.id
    chatId = message.chat.id

    sponsors = await database.get_sponsors()
    print(sponsors)
    if sponsors:
        if not await subCheck_logic.check_all_subscriptions(userId):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
                [InlineKeyboardButton(text=f"Канал {name}", url=url)]
                for id, name, url, url_private in sponsors
            ] + [[InlineKeyboardButton(text="✅ Я подписался на все каналы", callback_data='check_subscription')]]
            )

            await message.reply_photo(
                photo="https://ibb.co/BVZVtP91", 
                caption=(
                    "📌 Перед началом работы необходимо подтвердить подписку на все каналы-партнёры.\n\n"
                    "✅ После проверки подписки бот будет доступен для использования.\n"
                    "👇 Проверь подписку и запускай бота."
                ),
                reply_markup=keyboard
            )
        else:

            await message.answer("Напиши код ниже в формате (ХХХХ)⬇️")
            await state.set_state(SearchStates.Searching)

@router.message(SearchStates.Searching)
async def searchHandler(message: Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not code.isdigit():
        await message.answer("Код должен быть только из цифр! 🔢")
        return
    
    result = await database.show_movie(int(code))

    if result:
        try:

            title, description, image_url = result
            button = []
            isLiked = await database.get_liked_movies(user_id)
            if int(code) not in isLiked:
                button.append(InlineKeyboardButton(text="❤️", callback_data=f"like_{code}"))
            else:
                button.append(InlineKeyboardButton(text="💔", callback_data=f"dislike_{code}"))
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[button])

            await message.reply_photo(
                image_url,
                caption=f"Название: <b>{title}</b>\n\n<b>{description}</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")
            return
    else:
        await message.answer("❌🎬 <b>Фильм не найден.</b>\nПопробуй другой код! 😊", parse_mode="HTML")

@router.callback_query(F.data.startswith('like_'))
async def like_movie(callback: CallbackQuery):
    # Извлекаем код фильма из callback_data
    code = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    await database.add_liked_movie(user_id, code)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💔", callback_data=f"dislike_{code}")]])
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)
    await callback.answer("Фильм добавлен в список понравившихся!", show_alert=False)

@router.callback_query(F.data.startswith('dislike_'))
async def dislike_movie(callback: CallbackQuery):
    code = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    await database.remove_liked_movie(user_id, code)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❤️", callback_data=f"dislike_{code}")]])
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)
    await callback.answer("Фильм убран из списка понравившихся!", show_alert=False)