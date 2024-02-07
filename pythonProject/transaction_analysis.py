import re
from collections import Counter
from datetime import datetime, timezone
from typing import Callable, TypeVar, Dict, Any, List

import requests

Fn = Callable
K = TypeVar('K')
V = TypeVar('V')

TRONGRID_API_KEY = '0d410306-1ed7-42b2-a753-cdcd436a96af'

to_snake_case: Fn[[str], str] = lambda camel: re.sub(r'(?<!^)(?=[A-Z])', '_', camel).lower()


def snake_case_key(key: K) -> K:
    if isinstance(key, str):
        return to_snake_case(key)
    return key


def snake_case_dict(d: Dict[K, V]) -> Dict[K, V]:
    if not isinstance(d, dict):
        return d
    ret: Dict[K, V] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = snake_case_dict(v)
        if isinstance(v, list):
            v = [snake_case_dict(x) for x in v]
        ret[snake_case_key(k)] = v
    return ret


def get_trc20_transactions(address: str, api_url: str = None, all_transactions: List[Dict[str, Any]] = None) -> List[
    Dict[str, Any]]:
    if all_transactions is None:
        all_transactions = []
    if api_url is None:  # Если URL не предоставлен, используем начальный URL
        api_url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        all_transactions.extend(data['data'])  # Добавляем текущую страницу данных
        print(all_transactions)
        if 'meta' in data and 'links' in data['meta'] and 'next' in data['meta']['links']:
            next_page_url = data['meta']['links']['next']
            return get_trc20_transactions(address, next_page_url,
                                          all_transactions)  # Рекурсивный вызов для следующей страницы
        else:
            return all_transactions  # Возвращаем все собранные данные
    else:
        raise Exception(f"Error fetching transactions: {response.status_code} - {response.text}")


def analyze_transactions(address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk_score = 0.0
    total_transaction_value = 0
    unique_addresses = set()
    frequent_transactions = Counter()
    threshold_transactions = 0
    cyclic_patterns = Counter()
    transaction_intervals = []

    total_transactions_today = 0
    current_date = datetime.now(timezone.utc).date()

    for i, tx in enumerate(transactions):
        print(f"Checking transaction: {tx}")
        # Суммируем общую стоимость транзакций
        total_transaction_value += int(tx['value'])
        # Собираем уникальные адреса
        unique_addresses.update([tx['from'], tx['to']])
        # Считаем частоту транзакций для каждого адреса
        frequent_transactions[tx['from']] += 1
        frequent_transactions[tx['to']] += 1

        transaction_date = datetime.fromtimestamp(tx['block_timestamp'] / 1000.0, tz=timezone.utc).date()
        if transaction_date == current_date:
            total_transactions_today += 1

        # Проверяем, превышает ли стоимость транзакции установленный порог
        if int(tx['value']) > 1000000000:
            risk_score += 1.0
            threshold_transactions += 1

        # Анализ циклических паттернов и интервалов между транзакциями
        if 'block_timestamp' in tx and i > 0:
            prev_tx = transactions[i - 1]
            if 'block_timestamp' in prev_tx and prev_tx['to'] == tx['from']:
                cyclic_patterns[(prev_tx['from'], tx['to'])] += 1

                prev_tx_time = datetime.fromtimestamp(prev_tx['block_timestamp'] / 1000.0)
                current_tx_time = datetime.fromtimestamp(tx['block_timestamp'] / 1000.0)
                interval = (current_tx_time - prev_tx_time).total_seconds()
                transaction_intervals.append(interval)

    # Проверка общего объема транзакций
    if total_transaction_value > 50000000000:
        risk_score += 1.0

    # Проверка количества уникальных адресов
    if len(unique_addresses) > 10:
        risk_score += 1.0

    # Дополнительные метрики риска
    if len(frequent_transactions) > 20:  # Порог для частых транзакций
        risk_score += 1.0

    if threshold_transactions > 5:  # Порог для транзакций с высокой стоимостью
        risk_score += 1.0

    if len(cyclic_patterns) > 3:  # Порог для обнаружения циклических паттернов
        risk_score += 1.0

    # Анализ интервалов между транзакциями
    short_intervals_count = sum(1 for interval in transaction_intervals if interval < 60)  # интервалы менее 60 секунд
    if short_intervals_count > 10:  # Пример порога
        risk_score += 1.0

    risk_score = risk_score / len(transactions) if transactions else 0

    average_transaction_value = total_transaction_value / len(transactions) if transactions else 0
    top_transactions = sorted(transactions, key=lambda x: x['value'], reverse=True)[:3]

    # Создание словаря с дополнительной информацией
    additional_info = {
        "🔄 Количество транзакций": len(transactions),
        "🔗 Уникальные адреса": len(unique_addresses),
        "💰 Общий объем транзакций": total_transaction_value,
        "📅 Транзакций сегодня": total_transactions_today,
        "🔝 Частые транзакции": [f"{addr}: {count}" for addr, count in frequent_transactions.most_common(5)],
        "💹 Средний размер транзакции": average_transaction_value,
        "💥 Топ-транзакции": [{"id": tx['transaction_id'], "value": tx['value']} for tx in top_transactions]
    }

    risk_assessment = "LOW"
    if risk_score > 0.7:
        risk_assessment = "HIGH"
    elif risk_score > 0.4:
        risk_assessment = "MID"

    # Использование эмоджи для различных уровней риска
    if risk_assessment == "LOW":
        risk_emoji = "🟢"  # Зеленый круг
    elif risk_assessment == "MID":
        risk_emoji = "🟡"  # Желтый круг
    else:
        risk_emoji = "🔴"  # Красный круг

    cryptocurrency_type = transactions[0]['token_info']['symbol']

    # Возвращение результатов анализа вместе с дополнительной информацией и эмоджи
    return {
        "cryptocurrency_type": cryptocurrency_type,
        "address": address,
        "risk_score": risk_score,
        "risk_assessment": risk_assessment,
        "risk_emoji": risk_emoji,
        "additional_info": additional_info
    }


def perform_risk_check(usdt_address: str) -> Dict[str, Any]:
    transactions = get_trc20_transactions(usdt_address)
    print("done")
    if transactions:
        analysis_result = analyze_transactions(usdt_address, transactions)
        return analysis_result
    else:
        raise Exception("Transaction data not found.")

# # Example usage
# usdt_address = "TFQQFB9ykAroZgTESDPJqJWQimn4hsnpr6"
# risk_report = perform_risk_check(usdt_address)
#
# print(json.dumps(snake_case_dict(risk_report), indent=4, ensure_ascii=False))
