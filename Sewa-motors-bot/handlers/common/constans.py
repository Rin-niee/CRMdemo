from handlers.orderss.states import OrderStates

MAX_FILES_TO_SEND = 20
PHOTO_STAGES = [
    {
        "state": OrderStates.photo_all,
        "title": "📸 Все фото автомобиля и видео автомобиля",
        "description": "Отправьте все фотографии автомобиля (можно альбомом)",
        "required": True,
        "stage_num": 1,
    },
]

TOTAL_STAGES = 1
STAGE_INDEX = {stage["state"]: i for i, stage in enumerate(PHOTO_STAGES)}
