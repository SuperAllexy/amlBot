from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests


def get_bitcoin_transactions(address: str) -> Dict[str, Any]:
    url = f'https://blockchain.info/rawaddr/{address}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"Error fetching Bitcoin transactions: {response.status_code} - {response.text}")


def is_bitcoin_address(address):
    try:
        addr = Address.import_address(address)
        return True if addr else False
    except Exception:
        return False


def analyze_bitcoin_transactions(address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        # Суммируем общую стоимость транзакций из выходов
        total_transaction_value += sum(out['value'] for out in tx['out'])

        # Собираем уникальные адреса из входов и выходов
        unique_addresses.update([inp['prev_out']['addr'] for inp in tx['inputs'] if 'prev_out' in inp])
        unique_addresses.update([out['addr'] for out in tx['out'] if 'addr' in out])

        # Считаем частоту транзакций для каждого адреса
        for out in tx['out']:
            if 'addr' in out:
                frequent_transactions[out['addr']] += 1

        # Работа с временем транзакции
        transaction_date = datetime.fromtimestamp(tx['time'], tz=timezone.utc).date()
        if transaction_date == current_date:
            total_transactions_today += 1

        # Проверка пороговой стоимости транзакции
        if sum(out['value'] for out in tx['out']) > 1000000000:
            risk_score += 1.0
            threshold_transactions += 1

        # Анализ циклических паттернов и интервалов между транзакциями
        if i > 0:
            prev_tx = transactions[i - 1]
            for inp in tx['inputs']:
                if 'prev_out' in inp and inp['prev_out']['addr'] == prev_tx['hash']:
                    cyclic_patterns[(prev_tx['hash'], tx['hash'])] += 1

                prev_tx_time = datetime.fromtimestamp(prev_tx['time'])
                current_tx_time = datetime.fromtimestamp(tx['time'])
                interval = (current_tx_time - prev_tx_time).total_seconds()
                transaction_intervals.append(interval)

        # Проверка общего объема транзакций
    if total_transaction_value > 50000000000:
        risk_score += 1.0

        # Проверка количества уникальных адресов
    if len(unique_addresses) > 10:
        risk_score += 1.0

        # Дополнительные метрики риска
    if len(frequent_transactions) > 20:
        risk_score += 1.0

    if threshold_transactions > 5:
        risk_score += 1.0

    if len(cyclic_patterns) > 3:
        risk_score += 1.0

        # Анализ интервалов между транзакциями
    short_intervals_count = sum(1 for interval in transaction_intervals if interval < 60)
    if short_intervals_count > 10:
        risk_score += 1.0

    risk_score = risk_score / len(transactions) if transactions else 0

    average_transaction_value = total_transaction_value / len(transactions) if transactions else 0
    top_transactions = sorted(transactions, key=lambda x: sum(out['value'] for out in x['out']), reverse=True)[:3]

    # Создание словаря с дополнительной информацией
    additional_info = {
        "🔄 Количество транзакций": len(transactions),
        "🔗 Уникальные адреса": len(unique_addresses),
        "💰 Общий объем транзакций": total_transaction_value,
        "📅 Транзакций сегодня": total_transactions_today,
        "🔝 Частые транзакции": [f"{addr}: {count}" for addr, count in frequent_transactions.most_common(5)],
        "💹 Средний размер транзакции": average_transaction_value,
        "💥 Топ-транзакции": [{"hash": tx['hash'], "value": sum(out['value'] for out in tx['out'])} for tx in
                             top_transactions]
    }

    risk_assessment = "LOW"
    if risk_score > 0.7:
        risk_assessment = "HIGH"
    elif risk_score > 0.4:
        risk_assessment = "MID"

    # Использование эмоджи для различных уровней риска
    risk_emoji = "🟢" if risk_assessment == "LOW" else "🟡" if risk_assessment == "MID" else "🔴"

    # Возвращение результатов анализа вместе с дополнительной информацией и эмоджи
    return {
        "cryptocurrency_type": "BTC",  # Тип криптовалюты
        "address": address,
        "risk_score": risk_score,
        "risk_assessment": risk_assessment,
        "risk_emoji": risk_emoji,
        "additional_info": additional_info
    }

#
# btc_address = "1PWgoq2CUafN5V6iLnyg6TXgiqTBJKdufp"
# btc_transactions_data = get_bitcoin_transactions(btc_address)  # Предполагается, что эта функция реализована
# btc_analysis_result = analyze_bitcoin_transactions(btc_address, btc_transactions_data['txs'])
# print(json.dumps(btc_analysis_result, indent=4, ensure_ascii=False))
