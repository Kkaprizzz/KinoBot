from aiogram import Bot, Dispatcher
from telethon import TelegramClient, errors, functions
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.errors import InviteHashInvalidError, InviteHashExpiredError
from typing import Union
import database, config, asyncio
import re

userbot = TelegramClient('session_name', config.api_id, config.api_hash)

error_msgs = ['chat not found', 'user not participant', 'bot was kicked']

async def is_chat_closed(invite_link: str) -> bool:
    """Проверяет, закрыт ли канал (по заявкам/недоступен)."""
    try:
        invite_hash = invite_link.split('/')[-1].replace('+', '')
        invite = await userbot(CheckChatInviteRequest(invite_hash))
        is_request_needed = getattr(invite, 'request_needed', False)
        print(f"Канал закрыт (требуется заявка): {is_request_needed}")
        return is_request_needed
    except (InviteHashInvalidError, InviteHashExpiredError):
        print(f"Ссылка {invite_link} недействительна или истекла — считаем канал закрытым")
        return True
    except Exception as e:
        print(f"Ошибка проверки invite-ссылки: {e}")
        return True

async def check_subscription(user_id: int, channel_id: Union[str, int]) -> bool:
    try:
        # Если это invite-ссылка с + — пропускаем проверку
        if isinstance(channel_id, str) and 't.me/+' in channel_id:
            print(f"Приватный канал {channel_id} — пропускаем проверку")
            return True

        # Для публичных каналов/супергрупп — проверяем подписку
        if isinstance(channel_id, int) or (isinstance(channel_id, str) and channel_id.lstrip('-').isdigit()):
            channel_id = int(channel_id)
            if str(channel_id).startswith("-100"):
                peer = PeerChannel(int(str(channel_id)[4:]))
                entity = await userbot.get_entity(peer)
            else:
                entity = await userbot.get_entity(channel_id)
        else:
            username = channel_id.replace("https://t.me/", "").replace("@", "")
            entity = await userbot.get_entity(username)

        await userbot(functions.channels.GetParticipantRequest(channel=entity, participant=user_id))
        return True

    except errors.UserNotParticipantError:
        print(f"Пользователь {user_id} не подписан на канал {channel_id}")
        return False
    except Exception as e:
        print(f"Ошибка проверки подписки для {user_id} в {channel_id}: {e}")
        if any(err in str(e).lower() for err in error_msgs):
            return True
        return False


async def check_bot_subscription(user_id) -> bool:
    """Проверка подписки на музыкального бота."""
    result = await database.music_user_exists(user_id)
    print(f"Музыкальный бот — подписка: {result}")
    return result

async def check_all_subscriptions(user_id: int) -> bool:
    """Проверка подписки на всех спонсоров."""
    sponsors = await database.get_sponsors()
    all_subscribed = True

    for sponsor_id, name, channelUrl_pub, channelUrl_private in sponsors:
        if sponsor_id == 1:
            result = await check_bot_subscription(user_id)
        else:
            # Если есть приватная ссылка — проверяем по ней, иначе по публичной
            check_target = channelUrl_private or channelUrl_pub
            result = await check_subscription(user_id, check_target)

        if not result:
            all_subscribed = False

    return all_subscribed
