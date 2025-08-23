from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import asyncio
from typing import Dict, List, Optional, Tuple

from config import MAX_FILE_SIZE
from handlers.common.constans import PHOTO_STAGES
from handlers.orderss.states import OrderStates
from handlers.common.utils import get_stage_by_state
from utils.file_handler import save_file_with_stage, get_stage_files
from keyboards.inline import get_photo_stage_keyboard, get_main_menu_keyboard
from handlers.orderss.rework import get_rework_keyboard

router = Router()

media_group_storage: Dict[str, List[Message]] = {}

PHOTO_SESSION_STATES = frozenset(stage["state"] for stage in PHOTO_STAGES) | {
    OrderStates.photo_additional
}


async def process_single_file(
    message: Message, state_data: dict, file_id: str, file_name: str = None
) -> Tuple[bool, Optional[dict]]:
    selected_order = state_data.get("selected_order")
    if not selected_order:
        await message.answer("Выберите заказ", reply_markup=get_main_menu_keyboard())
        return False, None

    current_state = state_data.get("current_stage")
    if not current_state:
        return False, None

    try:
        success, _ = await save_file_with_stage(
            message.bot,
            file_id,
            message.from_user.id,
            selected_order,
            current_state["title"],
            file_name,
        )
        return success, current_state
    except Exception:
        return False, current_state


def extract_file_info(message: Message) -> Optional[Tuple[str, str, int]]:
    if message.photo:
        photo = message.photo[-1]
        return photo.file_id, f"photo_{photo.file_unique_id}.jpg", photo.file_size or 0
    elif message.document:
        doc = message.document
        return (
            doc.file_id,
            doc.file_name or f"doc_{doc.file_unique_id}",
            doc.file_size or 0,
        )
    elif message.video:
        video = message.video
        return video.file_id, f"video_{video.file_unique_id}.mp4", video.file_size or 0
    return None


async def send_progress_fast(
    message: Message, stage_info: dict, files_count: int, state: FSMContext
):
    if stage_info.get("state") == OrderStates.photo_additional:
        text = (
            f"<b>{stage_info['title']}</b>\n"
            f"✅ Файлов: {files_count}\n\n"
            f"Загружайте еще или переходите дальше:"
        )
    else:
        text = (
            f"<b>{stage_info['title']}</b> | Этап {stage_info['stage_num']}/{len(PHOTO_STAGES)}\n"
            f"✅ Файлов: {files_count}\n\n"
            f"Загружайте еще или переходите дальше:"
        )

    try:
        if stage_info.get("state") == OrderStates.photo_additional:
            markup = get_rework_keyboard()
        else:
            markup = get_photo_stage_keyboard(stage_info)
        await message.answer(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await message.answer(f"✅ Загружено файлов: {files_count}")


@router.message(F.photo | F.document | F.video)
async def handle_stage_media(message: Message, state: FSMContext):
    current_state_name = await state.get_state()
    if current_state_name not in PHOTO_SESSION_STATES:
        return

    state_data = await state.get_data()
    current_stage = get_stage_by_state(current_state_name)

    if not current_stage:
        return

    state_data["current_stage"] = current_stage

    if current_stage["state"] == OrderStates.photo_video:
        if not message.video:
            await message.answer("Нужно видео")
            return
    elif current_stage["state"] == OrderStates.photo_additional:
        if not (message.photo or message.document or message.video):
            await message.answer("Нужно фото или видео")
            return
    else:
        if not (message.photo or message.document):
            await message.answer("Нужно фото")
            return

    if message.media_group_id:
        media_group_id = message.media_group_id

        if media_group_id not in media_group_storage:
            media_group_storage[media_group_id] = []

        media_group_storage[media_group_id].append(message)

        await asyncio.sleep(0.1)

        if media_group_id in media_group_storage:
            messages = media_group_storage.pop(media_group_id)
            asyncio.create_task(
                process_media_group_async(messages, state_data, current_stage, state)
            )
    else:
        asyncio.create_task(
            process_single_file_async(message, state_data, current_stage, state)
        )


async def process_single_file_async(
    message: Message, state_data: dict, current_stage: dict, state: FSMContext
):
    file_info = extract_file_info(message)
    if not file_info:
        return

    file_id, file_name, file_size = file_info

    if file_size > MAX_FILE_SIZE:
        await message.answer("❌ Файл слишком большой")
        return

    success, _ = await process_single_file(message, state_data, file_id, file_name)

    if success:
        selected_order = state_data.get("selected_order")
        if selected_order:
            files = get_stage_files(
                message.from_user.id, selected_order, current_stage["title"]
            )
            await send_progress_fast(message, current_stage, len(files), state)
    else:
        await message.answer("❌")


async def process_media_group_async(
    messages: List[Message], state_data: dict, current_stage: dict, state: FSMContext
):
    if not messages:
        return

    first_message = messages[0]
    successful_uploads = 0

    tasks = []
    for msg in messages:
        file_info = extract_file_info(msg)
        if file_info:
            file_id, file_name, file_size = file_info
            if file_size <= MAX_FILE_SIZE:
                tasks.append(process_single_file(msg, state_data, file_id, file_name))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful_uploads = sum(
            1 for result in results if isinstance(result, tuple) and result[0]
        )

    if successful_uploads > 0:
        selected_order = state_data.get("selected_order")
        if selected_order:
            files = get_stage_files(
                first_message.from_user.id, selected_order, current_stage["title"]
            )
            await send_progress_fast(first_message, current_stage, len(files), state)


@router.message(F.text)
async def handle_text_in_stage_mode(message: Message, state: FSMContext):
    current_state_name = await state.get_state()
    if current_state_name not in PHOTO_SESSION_STATES:
        return

    current_stage = get_stage_by_state(current_state_name)
    if not current_stage:
        return

    if current_stage["state"] == OrderStates.photo_additional:
        markup = get_rework_keyboard()
    else:
        markup = get_photo_stage_keyboard(current_stage)
    await message.answer(
        f"<b>{current_stage['title']}</b>\nОтправьте файлы или используйте кнопки:",
        reply_markup=markup,
        parse_mode="HTML",
    )
