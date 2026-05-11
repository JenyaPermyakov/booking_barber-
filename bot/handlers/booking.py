from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.booking import (
    get_confirm_keyboard,
    get_dates_keyboard,
    get_services_keyboard,
    get_slots_keyboard,
)
from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.api import (
    create_booking,
    delete_booking,
    get_my_booking,
    get_services,
    get_slots,
)
from bot.states.booking import BookingState


router = Router()


@router.message(F.text == "Записаться")
async def start_booking(message: Message, state: FSMContext):
    await state.clear()

    services = await get_services()

    if not services:
        await message.answer(
            "Не удалось получить список услуг.\n"
            "Проверьте, что Django API запущен."
        )
        return

    await state.set_state(BookingState.choosing_service)

    await message.answer(
        "Отлично, начинаем запись.\n\n"
        "Выберите услугу:",
        reply_markup=get_services_keyboard(services),
    )


@router.callback_query(
    BookingState.choosing_service,
    F.data.startswith("service_")
)
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.replace("service_", ""))

    await state.update_data(service_id=service_id)
    await state.set_state(BookingState.choosing_date)

    await callback.message.answer(
        "Услуга выбрана ✅\n\n"
        "Выберите дату:",
        reply_markup=get_dates_keyboard(),
    )

    await callback.answer()


@router.callback_query(
    BookingState.choosing_date,
    F.data.startswith("date_")
)
async def choose_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace("date_", "")

    data = await state.get_data()
    service_id = data.get("service_id")

    slots = await get_slots(
        date=selected_date,
        service_id=service_id,
    )

    if not slots:
        await callback.message.answer(
            "На эту дату свободных слотов нет.\n\n"
            "Пожалуйста, выберите другую дату:",
            reply_markup=get_dates_keyboard(),
        )
        await callback.answer()
        return

    await state.update_data(date=selected_date)
    await state.set_state(BookingState.choosing_time)

    await callback.message.answer(
        f"Дата выбрана ✅\n\n"
        f"Выберите свободное время:",
        reply_markup=get_slots_keyboard(slots),
    )

    await callback.answer()


@router.callback_query(
    BookingState.choosing_time,
    F.data.startswith("time_")
)
async def choose_time(callback: CallbackQuery, state: FSMContext):
    selected_time = callback.data.replace("time_", "")

    await state.update_data(time=selected_time)
    await state.set_state(BookingState.entering_name)

    await callback.message.answer(
        "Время выбрано ✅\n\n"
        "Введите ваше имя:"
    )

    await callback.answer()


@router.message(BookingState.entering_name)
async def enter_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "Имя слишком короткое.\n"
            "Введите имя ещё раз:"
        )
        return

    await state.update_data(name=name)
    await state.set_state(BookingState.entering_phone)

    await message.answer(
        "Введите номер телефона.\n\n"
        "Пример: 87001234567"
    )


@router.message(BookingState.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.text.strip().replace(" ", "").replace("+", "")

    if not phone.isdigit():
        await message.answer(
            "Телефон должен содержать только цифры.\n"
            "Введите номер ещё раз:"
        )
        return

    if len(phone) < 10 or len(phone) > 12:
        await message.answer(
            "Некорректная длина номера.\n"
            "Введите номер ещё раз:"
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(BookingState.confirming)

    data = await state.get_data()

    await message.answer(
        "Проверьте данные записи:\n\n"
        f"Услуга ID: {data['service_id']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n\n"
        "Подтвердить запись?",
        reply_markup=get_confirm_keyboard(),
    )


@router.callback_query(
    BookingState.confirming,
    F.data == "confirm_booking"
)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    payload = {
        "service_id": data["service_id"],
        "telegram_id": callback.from_user.id,
        "client_name": data["name"],
        "phone": data["phone"],
        "booking_date": data["date"],
        "booking_time": data["time"],
    }

    success, response_data = await create_booking(payload)

    if not success:
        await callback.message.answer(
            "Не удалось создать запись ❌\n\n"
            f"Ответ API:\n{response_data}"
        )
        await callback.answer()
        return

    await state.clear()

    await callback.message.answer(
        "Запись успешно создана ✅\n\n"
        f"Дата: {response_data.get('booking_date')}\n"
        f"Время: {response_data.get('booking_time')}\n\n"
        "Ждём вас!",
        reply_markup=main_menu_keyboard,
    )

    await callback.answer()


@router.callback_query(
    BookingState.confirming,
    F.data == "cancel_booking_process"
)
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.answer(
        "Создание записи отменено.",
        reply_markup=main_menu_keyboard,
    )

    await callback.answer()


@router.message(F.text == "Моя запись")
async def show_my_booking(message: Message):
    success, booking = await get_my_booking(message.from_user.id)

    if not success:
        await message.answer(
            "Активная запись не найдена."
        )
        return

    service = booking.get("service")
    client = booking.get("client")

    await message.answer(
        "Ваша активная запись:\n\n"
        f"ID записи: {booking.get('id')}\n"
        f"Дата: {booking.get('booking_date')}\n"
        f"Время: {booking.get('booking_time')}\n"
        f"Статус: {booking.get('status')}\n"
        f"Услуга: {service}\n"
        f"Клиент: {client}"
    )


@router.message(F.text == "Отменить запись")
async def cancel_my_booking(message: Message):
    success, booking = await get_my_booking(message.from_user.id)

    if not success:
        await message.answer(
            "У вас нет активной записи для отмены."
        )
        return

    booking_id = booking.get("id")

    if not booking_id:
        await message.answer(
            "Не удалось определить ID записи."
        )
        return

    delete_success, response_data = await delete_booking(booking_id)

    if not delete_success:
        await message.answer(
            "Не удалось отменить запись ❌\n\n"
            f"Ответ API:\n{response_data}"
        )
        return

    await message.answer(
        "Запись успешно отменена ✅",
        reply_markup=main_menu_keyboard,
    )
