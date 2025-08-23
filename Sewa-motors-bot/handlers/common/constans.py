from handlers.orderss.states import OrderStates

MAX_FILES_TO_SEND = 20
PHOTO_STAGES = [
    {
        "state": OrderStates.photo_all,
        "title": "📸 Все фото автомобиля",
        "description": "Отправьте все фотографии автомобиля (можно альбомом)",
        "required": True,
        "stage_num": 1,
    },
    {
        "state": OrderStates.photo_video,
        "title": "🎥 Обзорное видео",
        "description": "Снимите короткое видео-обзор автомобиля",
        "required": True,
        "stage_num": 2,
    },
]

TOTAL_STAGES = 2
STAGE_INDEX = {stage["state"]: i for i, stage in enumerate(PHOTO_STAGES)}
