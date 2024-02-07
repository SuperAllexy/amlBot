import logging
from typing import Dict, Any

from pycoinpayments import CoinPayments
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from SqlData import *
from btc import analyze_bitcoin_transactions, get_bitcoin_transactions
from eth import analyze_ethereum_transactions, get_ethereum_transactions
from transaction_analysis import perform_risk_check

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

cp = CoinPayments(public_key='600b8c4c8e9e1c1445ce13acf9a34eaee1212ae42fd794b27ed8659e36ffd0f4',
                  private_key='69368b25C1b95991c9202F98087dc2D4b9f29465C6F18B2844a7703fab07C20A')


def start(update, context):
    update.message.reply_text(
        'Добро пожаловать в наш бот!'
        '\nОн проводит AML проверки на криптовалютные кошельки и транзакции'
        '\nBTC, ETH, USDT TRC20'
        '\nЦена за одну проверку 0.5$, минимальное количество проверок начинается от 50 проверок'
    )
    user_id = update.effective_user.id
    remaining_checks = get_remaining_transactions(user_id)

    if remaining_checks > 0:
        reply_text = 'У вас есть доступные проверки. Выберите действие:'
        keyboard = [[InlineKeyboardButton("AML Проверка", callback_data='aml_check')]]
    else:
        reply_text = 'У вас нет доступных проверок. Выберите действие:'
        keyboard = [[InlineKeyboardButton("Купить Проверки", callback_data='buy_checks')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(reply_text, reply_markup=reply_markup)


def start_buy(update, context):
    user_id = update.effective_user.id
    remaining_checks = get_remaining_transactions(user_id)
    logger.info(f"Пользователь {user_id} имеет {remaining_checks} оставшихся транзакций")
    if remaining_checks <= 0:
        create_transaction_params = {
            'amount': 0.00058,
            'currency1': 'BTC',
            'currency2': 'BTC',
            'buyer_email': 'sweetiki56@gmail.com'
        }

        print(user_id)

        # Создание транзакции
        transaction = cp.create_transaction(create_transaction_params)
        logger.info(f"Response from CoinPayments: {transaction}")

        if transaction['error'] == 'ok':
            txn_id = transaction['txn_id']
            amount = transaction['amount']
            address = transaction['address']

            context.user_data['txn_id'] = txn_id

            if update.callback_query:  # Если вызвано через CallbackQuery
                update.callback_query.message.reply_text(f"Для оплаты отправьте {amount} BTC на адрес {address}.")
            else:  # Если вызвано напрямую через команду
                update.message.reply_text(f"Для оплаты отправьте {amount} BTC на адрес {address}.")

            keyboard = [
                [InlineKeyboardButton("Проверить статус", callback_data=f"check_{txn_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                update.callback_query.message.reply_text('Нажмите для проверки статуса транзакции:',
                                                         reply_markup=reply_markup)
            else:
                update.message.reply_text('Нажмите для проверки статуса транзакции:', reply_markup=reply_markup)
        else:
            if update.callback_query:
                update.callback_query.message.reply_text("Ошибка создания транзакции.")
            else:
                update.message.reply_text("Ошибка создания транзакции.")


def handle_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get('is_aml_check'):
        try:
            crypto_type = determine_crypto_type(text)
            if crypto_type == 'BTC':
                btc_transactions_data = get_bitcoin_transactions(text)
                analysis_result = analyze_bitcoin_transactions(text, btc_transactions_data['txs'])
            elif crypto_type == 'ETH':
                eth_transactions_data = get_ethereum_transactions(text)
                analysis_result = analyze_ethereum_transactions(text, eth_transactions_data['result'])
            else:  # USDT TRC20
                analysis_result = perform_risk_check(text)

            formatted_response = format_analysis_result(analysis_result, crypto_type)
            update.message.reply_text(formatted_response)

            subtract_transaction(user_id)  # Уменьшаем количество доступных проверок
            remaining = get_remaining_transactions(user_id)
            update.message.reply_text(f'У вас осталось {remaining} транзакций на счету:')

            context.user_data['is_aml_check'] = False
            if remaining > 0:
                reply_text = 'У вас есть доступные проверки. Выберите действие:'
                keyboard = [[InlineKeyboardButton("AML Проверка", callback_data='aml_check')]]
            else:
                reply_text = 'У вас нет доступных проверок. Выберите действие:'
                keyboard = [[InlineKeyboardButton("Купить Проверки", callback_data='buy_checks')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(reply_text, reply_markup=reply_markup)
        except Exception as e:
            update.message.reply_text(f'Ошибка: {e}')
    else:
        # Здесь может быть логика для обработки других сообщений
        if text == 'Помощь' or text == '/help':
            update.message.reply_text("Это справочное сообщение с инструкциями о том, как пользоваться ботом.")
        elif text.startswith('/'):
            update.message.reply_text("Команда не распознана. Пожалуйста, введите корректную команду.")
        else:
            update.message.reply_text(
                "Я не понимаю это сообщение. Пожалуйста, введите корректную команду или сообщение.")


def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    txn_id = context.user_data.get('txn_id')
    user_id = update.effective_user.id

    if data == "aml_check":
        # Логика для инициации AML проверки
        handle_aml_check(update, context)
    elif data == "buy_checks":
        # Логика для покупки проверок
        start_buy(update, context)
    elif data.startswith("check_") and txn_id:
        # Логика для проверки статуса платежа
        params = {'txid': txn_id}
        transaction_info = cp.get_tx_info(params=params)
        if transaction_info['error'] == 'ok':
            status = transaction_info['status']
            if status >= 100 or status == 2:
                query.edit_message_text(text="Товар успешно оплачен.")
                add_transactions(user_id, 50)  # Добавление транзакций после подтверждения оплаты
                query.edit_message_text(text="Покупка подтверждена. У вас теперь 50 доступных проверок.")
            else:
                query.edit_message_text(text="Статус платежа: Ожидание.")
                keyboard = [
                    [InlineKeyboardButton("Проверить статус", callback_data=f"check_{txn_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.message.reply_text('Нажмите для повторной проверки статуса транзакции:',
                                         reply_markup=reply_markup)
        else:
            query.edit_message_text(text="Ошибка проверки статуса транзакции.")
    else:
        query.edit_message_text(text="Неизвестная команда.")


def handle_aml_check(update, context):
    user_id = update.effective_user.id
    remaining_checks = get_remaining_transactions(user_id)

    if remaining_checks > 0:
        context.user_data['is_aml_check'] = True  # Устанавливаем флаг для последующей обработки в handle_message
        context.bot.send_message(chat_id=user_id, text="Запущена AML проверка. Пожалуйста, отправьте адрес транзакции.")
    else:
        context.bot.send_message(chat_id=user_id, text="У вас нет доступных проверок. Пожалуйста, приобретите их.")


def determine_crypto_type(address: str) -> str:
    if address.startswith('0x'):
        return 'ETH'
    elif address.startswith('1') or address.startswith('3'):
        return 'BTC'
    else:
        return 'USDT'


def format_analysis_result(result: Dict[str, Any], crypto_type: str) -> str:
    # Форматирование результата
    risk_emoji = result.get('risk_emoji', '🤷')
    address = result.get("address", 'Не указан')
    risk_score = round(result.get("risk_score", 0.0), 2)
    risk_assessment = result.get("risk_assessment", "Не определен")
    additional_info = result.get("additional_info", {})

    response = f"Тип криптовалюты: {crypto_type}\nАдрес: {address}\nРиск:{risk_score}\nУровень риска: {risk_assessment} {risk_emoji}\n\nДополнительная информация:\n"
    for key, value in additional_info.items():
        response += f"{key}: {value}\n"
    return response


def main():
    updater = Updater('6939291894:AAGV02Fssp4Tpo24jGYUPVTQlWJ3lwE-hrs', use_context=True)
    logger.info("Starting bot")
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("buy", start_buy))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
