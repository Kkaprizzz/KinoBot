from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, CallbackQuery
from aiogram.fsm.context import FSMContext
from SearchFilmLogic import clear_state
import database

router = Router()

@router.message(F.text.contains("🎬 Твоя Кинотека"))
async def liked_cmd(message: Message, state: FSMContext):
    user_id = message.chat.id
    liked_codes = await database.get_liked_movies(user_id)

    if liked_codes:

        index = 0
        code = liked_codes[index]
        result = await database.show_movie(code)  # (title, description, image_url)

        print(result, code)

        if result:
            title, description, image_url = result

            text = f"<b>{title}</b>\n\n{description}"
            buttons = []
            buttons.append(InlineKeyboardButton(text="💔", callback_data=f"dislikeInF_{code}"))
            if index < len(liked_codes) - 1:
                buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"fav:{index + 1}"))

            row1 = [buttons[0]]
            row2 = buttons[1:]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[row1, row2])

            try:
                media = InputMediaPhoto(media=image_url, caption=text, parse_mode="HTML")
                await message.edit_media(
                    media=media,
                    reply_markup=keyboard
                )
            except:
                await message.reply_photo(
                    photo=image_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

    else:
        try:
            await message.edit_text("Ты ещё ничего не лайкнул(а) 🎬💤")
        except:
            await message.answer("Ты ещё ничего не лайкнул(а) 🎬💤")

@router.callback_query(lambda c: c.data.startswith("fav:"))
async def scroll_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    liked_codes = await database.get_liked_movies(user_id)

    index = int(callback.data.split(":")[1])
    if index < 0 or index >= len(liked_codes):
        await callback.answer("Дальше листать нельзя.")
        return

    code = liked_codes[index]
    result = await database.show_movie(code)
    if not result:
        await callback.answer("Фильм не найден.")
        return

    title, description, image_url = result
    text = f"<b>{title}</b>\n\n{description}"

    # Кнопки
    buttons = [InlineKeyboardButton(text="💔", callback_data=f"dislikeInF_{code}")]
    if index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"fav:{index - 1}"))
    if index < len(liked_codes) - 1:
        buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"fav:{index + 1}"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

    # Обновляем сообщение (меняем фото + текст)
    media = InputMediaPhoto(media=image_url, caption=text, parse_mode="HTML")
    await callback.message.edit_media(media, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("dislikeInF_"))
async def dislikeLikedFilm(callback: CallbackQuery, state: FSMContext):
    user_id = callback.message.chat.id
    code = callback.data.removeprefix("dislikeInF_")
    await database.remove_liked_movie(user_id, int(code))
    await callback.answer("Фильм удалён из списка понравившихся", show_alert=False)
    await liked_cmd(callback.message, state)