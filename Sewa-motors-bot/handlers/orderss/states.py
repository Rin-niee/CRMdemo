from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """
    Состояния конечного автомата для управления заказами
    
    Определяет все возможные состояния, в которых может находиться
    процесс обработки заказа от выбора до завершения.
    """
    
    # Состояния предварительной проверки
    precheck_decision = State()        # Выбор решения: начать осмотр или запросить консультацию
    precheck_wait_manager = State()    # Ожидание ответа от главного менеджера
    precheck_video = State()           # Загрузка видео для консультации
    precheck_wait_customer = State()   # Ожидание решения заказчика
    precheck_chat = State()            # Чат с заказчиком
    precheck_chat_manager = State()    # Чат с главным менеджером

    # Состояния выбора
    selecting_company = State()        # Выбор компании
    selecting_order = State()          # Выбор заказа

    # Состояния фотосессии
    photo_all = State()                # Загрузка всех фото автомобиля
    photo_video = State()              # Загрузка обзорного видео

    # Дополнительные состояния
    photo_additional = State()         # Дополнительные фото (необязательно)

    # Состояния чек-листа
    checklist_q1 = State()             # Первый вопрос чек-листа
    checklist_q2 = State()             # Второй вопрос чек-листа
