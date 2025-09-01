from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.data import (
    get_companies,
    get_open_orders_older_than,
    get_my_order
    )


def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📦 Выбрать заказ", callback_data="select_order")]]
    )


def get_help_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    open_orders = get_open_orders_older_than(60)
    my_orders = get_my_order(user_id)
    count = len(open_orders)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Компании", callback_data="select_order"),
                InlineKeyboardButton(text=f"📝 Мои заявки({my_orders})", callback_data="my_orders_menu"),
                InlineKeyboardButton(text=f"🕧 Открытые заявки ({count})", callback_data="orderplan_menu"),
                InlineKeyboardButton(text=f"🙅‍♂️ Отказаться от заказа", callback_data="all_my_orders"),
            ]
        ]
    )


def get_companies_keyboard():
    companies = get_companies()
    buttons = [
        [InlineKeyboardButton(text=company["name"], callback_data=f"company_{company['id']}")]
        for company in companies
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_companies_with_disabled_keyboard(companies):
    buttons = [[InlineKeyboardButton(text=c["name"], callback_data=f"open_company_{c['id']}")] for c in companies]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_disabled_orders_keyboard(orders):
    return InlineKeyboardMarkup(
        inline_keyboard=
            [[InlineKeyboardButton(text=f"{o.get('brand','')} {o.get('model','')}", callback_data=f"open_order_{o['id']}")]
             for o in orders] +
            [[InlineKeyboardButton(text="⬅️ Назад к компаниям", callback_data="openorders_back_companies")]]
    )


def get_orders_keyboard(orders, back_button: bool = False):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{o.get('brand','')} {o.get('model','')}".strip(), callback_data=str(o["id"]) 
            )
        ]
        for o in orders
    ]
    if back_button:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к компаниям", callback_data="back_to_companies")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_orders_with_opened_keyboard(orders: list) -> InlineKeyboardMarkup:
    def _format_opened(val):
        s = str(val or "")
        return s.split(".")[0]

    inline_buttons = []
    for o in orders:
        text = f"{o.get('brand') or 'Без названия'} {o.get('model') or ''} {o.get('year') or ''}"
        if o.get('manager_id'):
            text += f"— менеджер {o.get('manager_id')} выехал на съемку" 
        inline_buttons.append([InlineKeyboardButton(text=text, callback_data=f"order_time_{o.get('id')}")])

    return InlineKeyboardMarkup(inline_keyboard=inline_buttons)

#меню отказа от заказа
def get_orders_with_opened_keyboard_for_decline(orders: list) -> InlineKeyboardMarkup:
    def _format_opened(val):
        s = str(val or "")
        return s.split(".")[0]

    inline_buttons = []
    for o in orders:
        text = f"{o.get('brand') or 'Без названия'} {o.get('model') or ''} {o.get('year') or ''}"
        inline_buttons.append([InlineKeyboardButton(text=text, callback_data=f"decline_order_{o.get('id')}")])

    return InlineKeyboardMarkup(inline_keyboard=inline_buttons)


def get_order_info_keyboard(context="company"):
    if context == "status":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📸 Загрузить осмотр", callback_data="start_photo_session")],
                [InlineKeyboardButton(text="⬅️ Назад к статусам", callback_data="back_to_status_filter")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📸 Загрузить осмотр", callback_data="start_photo_session")]]
    )


def get_photo_stage_keyboard(stage_info, context="company"):
    buttons = []
    current_stage = stage_info.get("stage_num", 1)
    total_stages = stage_info.get("total_stages", 2)

    if current_stage < total_stages:
        buttons.append([InlineKeyboardButton(text="➡️ Следующий этап", callback_data="next_stage")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Завершить съемку", callback_data="next_stage")])

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к заказам" if context != "status" else "⬅️ Назад к статусам",
                callback_data="back_to_orders" if context != "status" else "back_to_status_filter",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_filtered_orders_keyboard(orders):
    status_emoji = {"progress": "🟡", "done": "🟢", "open": "🔵"}
    buttons = [
        [
            InlineKeyboardButton(text=f"{status_emoji.get(o['status'],'⚪')} {o['model']}", callback_data=f"order_status_{o['id']}")
        ]
        for o in orders
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к статусам", callback_data="back_to_status_filter")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_upload_keyboard(include_back: bool = False):
    buttons = [[InlineKeyboardButton(text="✅ Завершить загрузку", callback_data="finish_upload")]]
    if include_back:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к заказам", callback_data="back_to_orders")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="back_to_menu")]])


def get_precheck_decision_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸Загрузить осмотр", callback_data="precheck_start")],
            [InlineKeyboardButton(text="🗒 Нужна консультация", callback_data="precheck_need_consult")],
        ]
    )


def get_precheck_manager_keyboard(order_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📹 Запросить короткое видео", callback_data=f"precheck_req_video_{order_id}")],
            [InlineKeyboardButton(text="▶️ Продолжай осмотр", callback_data=f"precheck_continue_{order_id}")],
        ]
    )


def get_precheck_after_video_keyboard(order_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Продолжай осмотр", callback_data=f"precheck_continue_{order_id}")],
            [InlineKeyboardButton(text="💬 Связаться с осмотрщиком", callback_data=f"precheck_chat_{order_id}")],
            [InlineKeyboardButton(text="⛔️ Остановить осмотр", callback_data=f"precheck_stop_{order_id}")],
        ]
    )


def get_customer_decision_keyboard(order_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕙 Заказчик не ответил", callback_data=f"cust_no_answer_{order_id}")],
            [InlineKeyboardButton(text="⛔️ Не продолжать осмотр", callback_data=f"cust_stop_{order_id}")],
            [InlineKeyboardButton(text="✅ Продолжать (с комментарием)", callback_data=f"cust_continue_{order_id}")],
        ]
    )


def get_precheck_manager_reply_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить администратору", callback_data=f"manager_reply_{order_id}")]
        ]
    )


def get_order_status_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔵 Открытые", callback_data="status_open")],
            [
                InlineKeyboardButton(
                    text="🟡 В процессе", callback_data="status_progress"
                )
            ],
            [InlineKeyboardButton(text="🟢 Завершённые", callback_data="status_done")],
        ]
    )


def get_my_orders_keyboard(orders):
    status_emoji = {"progress": "🟡", "done": "🟢", "open": "🔵"}
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{status_emoji.get(o['status'],'⚪')} {o['model']}",
                    callback_data=f"order_{o['status']}_{o['id']}",
                )
            ]
            for o in orders
        ]
    )


def get_deadline_orders_keyboard(orders):
    return InlineKeyboardMarkup(inline_keyboard=[])


def get_checklist_question_keyboard(qnum: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"chk:{qnum}:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"chk:{qnum}:no"),
            ]
        ]
    )


def get_checklist_multichoice_keyboard(
    qnum: int, options: list[tuple[str, str]]
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"chk:{qnum}:{code}")]
        for label, code in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить заказ",
                    callback_data=f"admin_confirm_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Доп. задание и доработка",
                    callback_data=f"admin_rework_with_task_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в меню", callback_data="back_to_menu"
                )
            ],
        ]
    )
