from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests


def get_ethereum_transactions(address: str) -> Dict[str, Any]:
    etherscan_api_key = 'JRTTBDTC6VVRG5FVYQTT6VZD3WRZP2PJ7Z'
    url = f'https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"Error fetching Ethereum transactions: {response.status_code} - {response.text}")


def analyze_ethereum_transactions(address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk_score = 0.0
    total_transaction_value = 0
    unique_addresses = set()
    frequent_transactions = Counter()
    threshold_transactions = 0
    cyclic_patterns = Counter()
    transaction_intervals = []

    risk_assessment = "LOW"
    total_transactions_today = 0
    current_date = datetime.now(timezone.utc).date()

    for i, tx in enumerate(transactions):
        print(transactions)
        value_ether = int(tx['value']) / 1e18  # Преобразование вэл в эфиры
        total_transaction_value += value_ether
        unique_addresses.update([tx['from'], tx['to']])
        frequent_transactions[tx['from']] += 1
        frequent_transactions[tx['to']] += 1

        transaction_date = datetime.fromtimestamp(int(tx['timeStamp']), tz=timezone.utc).date()
        if transaction_date == current_date:
            total_transactions_today += 1

        # Пороговое значение для Ethereum может быть другим, например 10 ETH
        if value_ether > 10:
            risk_score += 1.0
            threshold_transactions += 1

        # Анализ циклических паттернов
        if i > 0:
            prev_tx = transactions[i - 1]
            prev_tx_time = datetime.fromtimestamp(int(prev_tx['timeStamp']))
            current_tx_time = datetime.fromtimestamp(int(tx['timeStamp']))
            interval = (current_tx_time - prev_tx_time).total_seconds()
            transaction_intervals.append(interval)
            if prev_tx['to'] == tx['from']:
                cyclic_patterns[(prev_tx['from'], tx['to'])] += 1

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
    top_transactions = sorted(transactions, key=lambda x: int(x['value']), reverse=True)[:3]

    additional_info = {
        "🔄 Количество транзакций": len(transactions),
        "🔗 Уникальные адреса": len(unique_addresses),
        "💰 Общий объем транзакций": total_transaction_value,
        "📅 Транзакций сегодня": total_transactions_today,
        "🔝 Частые транзакции": [f"{addr}: {count}" for addr, count in frequent_transactions.most_common(5)],
        "💹 Средний размер транзакции": average_transaction_value,
        "💥 Топ-транзакции": [{"hash": tx['hash'], "value": int(tx['value']) / 1e18} for tx in top_transactions]
    }

    if risk_score > 0.7:
        risk_assessment = "HIGH"
    elif risk_score > 0.4:
        risk_assessment = "MID"

    risk_emoji = "🟢" if risk_assessment == "LOW" else "🟡" if risk_assessment == "MID" else "🔴"

    return {
        "cryptocurrency_type": "ETH",
        "address": address,
        "risk_score": risk_score,
        "risk_assessment": risk_assessment,
        "risk_emoji": risk_emoji,
        "additional_info": additional_info
    }

# eth_address = "0xc49ca63eca0032c238276196a5bf51beddba87bf"
# eth_transactions_data = get_ethereum_transactions(eth_address)
#
# # Проверка на наличие данных транзакций в ответе
# if eth_transactions_data['status'] == '1' and 'result' in eth_transactions_data:
#     transactions = eth_transactions_data['result']
#
#     # Анализ транзакций Ethereum
#     analysis_result = analyze_ethereum_transactions(eth_address, transactions)
#
#     # Вывод результатов анализа
#     print(json.dumps(analysis_result, indent=4, ensure_ascii=False))
# else:
#     print("Ошибка при получении данных транзакций Ethereum или нет транзакций для анализа.")
