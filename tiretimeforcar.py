import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
(
    AIR_TEMP, TRACK_TEMP, TIRE_PRESSURE,
    AVG_SPEED, USAGE_TIME, ANTIAGING,
    CARBON_BLACK, SILICA, RUBBER_PERCENT
) = range(9)


def calculate_tire_wear(user_data):
    """Расчет износа шин с учетом времени эксплуатации"""
    try:
        # Базовый износ
        base_wear = 20

        # Влияние времени эксплуатации (в минутах)
        usage_minutes = float(user_data.get('usage_time', 0))
        base_wear += min(usage_minutes * 0.05, 40)  # Максимум 40% износа от времени

        # Влияние температуры трека
        track_temp = float(user_data.get('track_temp', 30))
        if track_temp > 50:
            base_wear += (track_temp - 50) * 0.5
        elif track_temp > 40:
            base_wear += (track_temp - 40) * 0.3
        elif track_temp < 15:
            base_wear += (15 - track_temp) * 0.2

        # Влияние скорости
        avg_speed = float(user_data.get('avg_speed', 100))
        if avg_speed > 150:
            base_wear += (avg_speed - 150) * 0.2
        elif avg_speed > 120:
            base_wear += (avg_speed - 120) * 0.1

        # Влияние давления
        pressure = float(user_data.get('tire_pressure', 28))
        base_wear += abs(pressure - 28) * 0.8

        # Влияние состава резины
        rubber_percent = float(user_data.get('rubber_percent', 55))
        base_wear += max(0, 55 - rubber_percent) * 0.4

        # Влияние добавок
        if user_data.get('antiaging', 'Нет') == 'Нет':
            base_wear += 4
        if user_data.get('carbon_black', 'Нет') == 'Нет':
            base_wear += 6
        if user_data.get('silica', 'Нет') == 'Нет':
            base_wear += 8

        # Итоговый износ (не более 100%)
        total_wear = min(100, base_wear)
        remaining = max(0, 100 - total_wear)

        # Оценка состояния
        if remaining > 75:
            condition = "Отличное"
            recommendation = "Шины в идеальном состоянии"
        elif remaining > 50:
            condition = "Хорошее"
            recommendation = "Шины в хорошем состоянии"
        elif remaining > 25:
            condition = "Среднее"
            recommendation = "Рекомендуется замена в ближайшее время"
        elif remaining > 10:
            condition = "Плохое"
            recommendation = "Срочно замените шины"
        else:
            condition = "Критическое"
            recommendation = "Немедленная замена! Опасность повреждения!"

        return {
            'remaining': remaining,
            'condition': condition,
            'recommendation': recommendation,
            'wear_percentage': total_wear
        }

    except Exception as e:
        logger.error(f"Ошибка расчета: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🏎️ Бот для анализа износа шин\n\n"
        "Введите температуру воздуха (°C):"
    )
    return AIR_TEMP


async def air_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        temp = float(update.message.text)
        if not -20 <= temp <= 60:
            await update.message.reply_text("Введите значение от -20°C до 60°C")
            return AIR_TEMP
        context.user_data['air_temp'] = temp
        await update.message.reply_text("Введите температуру трека (°C):")
        return TRACK_TEMP
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return AIR_TEMP


async def track_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        temp = float(update.message.text)
        if not 10 <= temp <= 80:
            await update.message.reply_text("Введите значение от 10°C до 80°C")
            return TRACK_TEMP
        context.user_data['track_temp'] = temp
        await update.message.reply_text("Введите давление в шинах (psi):")
        return TIRE_PRESSURE
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return TRACK_TEMP


async def tire_pressure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        pressure = float(update.message.text)
        if not 15 <= pressure <= 40:
            await update.message.reply_text("Введите значение от 15 до 40 psi")
            return TIRE_PRESSURE
        context.user_data['tire_pressure'] = pressure
        await update.message.reply_text("Введите среднюю скорость (км/ч):")
        return AVG_SPEED
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return TIRE_PRESSURE


async def avg_speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        speed = float(update.message.text)
        if not 50 <= speed <= 350:
            await update.message.reply_text("Введите значение от 50 до 350 км/ч")
            return AVG_SPEED
        context.user_data['avg_speed'] = speed
        await update.message.reply_text("Введите время эксплуатации шин (в минутах):")
        return USAGE_TIME
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return AVG_SPEED


async def usage_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        minutes = float(update.message.text)
        if minutes < 0:
            await update.message.reply_text("Введите положительное число")
            return USAGE_TIME
        context.user_data['usage_time'] = minutes
        await update.message.reply_text(
            "Используются ли противостарители?",
            reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True)
        )
        return ANTIAGING
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return USAGE_TIME


async def antiaging(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['antiaging'] = update.message.text
    await update.message.reply_text(
        "Содержится ли технический углерод?",
        reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True)
    )
    return CARBON_BLACK


async def carbon_black(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['carbon_black'] = update.message.text
    await update.message.reply_text(
        "Содержится ли диоксид кремния?",
        reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True)
    )
    return SILICA


async def silica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['silica'] = update.message.text
    await update.message.reply_text("Введите процент каучука в шинах (50-60%):")
    return RUBBER_PERCENT


async def rubber_percent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        percent = float(update.message.text)
        if not 50 <= percent <= 60:
            await update.message.reply_text("Введите значение от 50% до 60%")
            return RUBBER_PERCENT

        context.user_data['rubber_percent'] = percent
        analysis = calculate_tire_wear(context.user_data)

        if analysis:
            report = (
                "🔍 Результаты анализа:\n\n"
                f"Общий износ: {analysis['wear_percentage']:.1f}%\n"
                f"Остаточный ресурс: {analysis['remaining']:.1f}%\n"
                f"Состояние: {analysis['condition']}\n"
                f"Рекомендация: {analysis['recommendation']}\n\n"
                "Для нового анализа введите /start"
            )
        else:
            report = "Ошибка анализа. Попробуйте снова."

        await update.message.reply_text(report)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return RUBBER_PERCENT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Анализ отменен. Для начала введите /start')
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token("ВАШ ТОКЕН").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AIR_TEMP: [MessageHandler(filters.TEXT & ~filters.COMMAND, air_temp)],
            TRACK_TEMP: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_temp)],
            TIRE_PRESSURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tire_pressure)],
            AVG_SPEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, avg_speed)],
            USAGE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, usage_time)],
            ANTIAGING: [MessageHandler(filters.TEXT & ~filters.COMMAND, antiaging)],
            CARBON_BLACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, carbon_black)],
            SILICA: [MessageHandler(filters.TEXT & ~filters.COMMAND, silica)],
            RUBBER_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, rubber_percent)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
