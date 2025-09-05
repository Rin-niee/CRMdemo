import os
from datetime import datetime
from config import STORAGE_PATH
from handlers.common.constans import PHOTO_STAGES
from utils.data import (
    insert_file_record
)
import logging
logger = logging.getLogger(__name__)
async def save_file_with_stage(bot, file_id: str, user_id: int, order_id, stage_title: str, file_name: str = None):
    try:
        if not all([bot, file_id, user_id is not None, order_id is not None, stage_title]):
            return False, None
            
        file = await bot.get_file(file_id)
        order_folder = _make_order_folder(user_id, order_id)

        if not file_name:
            file_name = _generate_filename(file.file_path)

        stage_prefix = _stage_prefix(stage_title)
        file_path = os.path.join(order_folder, f"{stage_prefix}_{datetime.now().strftime('%H%M%S')}_{file_name}")
        relative_file_path = os.path.relpath(file_path, start='storage')
        await insert_file_record(order_id, relative_file_path)
        await bot.download_file(file.file_path, file_path)
        
        return True, file_path

    except Exception as e:
        return False, None


def get_stage_files(user_id: int, order_id, stage_title: str):
    try:
        if user_id is None or order_id is None or stage_title is None:
            return []
        
        order_id_str = str(order_id)
        user_id_str = str(user_id)
        
        order_folder = os.path.join(STORAGE_PATH, user_id_str, order_id_str)
        if not os.path.exists(order_folder):
            return []
            
        stage_prefix = _stage_prefix(stage_title)
        files = []
        
        for fn in os.listdir(order_folder):
            if fn.startswith(stage_prefix + "_"):
                file_path = os.path.join(order_folder, fn)
                if os.path.isfile(file_path):
                    files.append({
                        "name": fn, 
                        "path": file_path, 
                        "order_id": order_id_str,
                        "stage": stage_title, 
                        "size": os.path.getsize(file_path)
                    })
        
        return files
    except Exception as e:
        return []


def get_user_files(user_id: int, order_id=None):
    try:
        if user_id is None:
            return []

        canonical_prefix_to_title = {
            _stage_prefix(stage["title"]): stage["title"] for stage in PHOTO_STAGES
        }

        canonical_prefix_to_title[_stage_prefix("📷 Дополнительные материалы")] = "📷 Дополнительные материалы"

        user_id_str = str(user_id)
        user_folder = os.path.join(STORAGE_PATH, user_id_str)

        if not os.path.exists(user_folder):
            return []

        files = []

        if order_id is not None:
            folders = [str(order_id)]
        else:
            folders = [f for f in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, f))]

        for folder in folders:
            order_folder = os.path.join(user_folder, folder)
            if not os.path.isdir(order_folder):
                continue

            for fn in os.listdir(order_folder):
                path = os.path.join(order_folder, fn)
                if os.path.isfile(path):
                    stage = "Прочие"

                    for prefix, title in canonical_prefix_to_title.items():
                        if fn.startswith(prefix + "_"):
                            stage = title
                            break
                    else:
                        for prefix, title in legacy_prefix_to_title.items():
                            if fn.startswith(prefix + "_"):
                                stage = title
                                break

                    ext = os.path.splitext(fn)[1].lower()
                    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
                        ftype = "photo"
                    elif ext in {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}:
                        ftype = "video"
                    else:
                        ftype = "other"
                    files.append({
                        "name": fn,
                        "path": path,
                        "order_id": folder,
                        "stage": stage,
                        "size": os.path.getsize(path),
                        "type": ftype
                    })
        return files
    except Exception as e:
        logger.error(f"get_user_files error: {e}")
        return []


def get_files_by_stage_summary(user_id: int, order_id):
    try:
        stages_summary = {"📸 Все фото автомобиля": 0, "🎥 Обзорное видео": 0, "Прочие": 0}
        files = get_user_files(user_id, order_id)
        
        for file in files:
            stage = file.get("stage", "Прочие")
            if stage in stages_summary:
                stages_summary[stage] += 1
            else:
                stages_summary["Прочие"] += 1
        return stages_summary
    except Exception as e:
        return {"📸 Все фото автомобиля": 0, "🎥 Обзорное видео": 0, "Прочие": 0}


def _make_order_folder(user_id, order_id):
    try:
        if user_id is None or order_id is None:
            raise ValueError(f"user_id или order_id равны None: user_id={user_id}, order_id={order_id}")
            
        user_id_str = str(user_id)
        order_id_str = str(order_id)
        folder = os.path.join(STORAGE_PATH, user_id_str, order_id_str)
        os.makedirs(folder, exist_ok=True)
        return folder
    except Exception as e:
        raise


def _generate_filename(file_path):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if file_path:
            ext = os.path.splitext(file_path)[1]
        else:
            ext = ""
        return f"file_{timestamp}{ext}"
    except Exception as e:
        return f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _stage_prefix(stage_title):
    try:
        if stage_title is None:
            return "Unknown"

        clean_title = (
            stage_title
            .replace("📸 ", "")
            .replace("🎥 ", "")
            .replace("📷 ", "")
            .replace(" ", "_")
        )

        return clean_title
    except Exception as e:

        return "Unknown"