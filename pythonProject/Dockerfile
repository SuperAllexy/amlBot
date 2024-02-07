# Используйте официальный образ Python
FROM python:3.8

# Установите рабочую директорию в контейнере
WORKDIR /code

# Установите зависимости системы
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

# Скопируйте файлы зависимостей
COPY requirements.txt .

# Установите зависимости Python
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Скопируйте только необходимые файлы в контейнер
COPY ./requirements.txt /code/requirements.txt
COPY ./TelegramBot.py /code/TelegramBot.py
COPY ./eth.py /code/eth.py
COPY ./btc.py /code/btc.py
COPY ./transaction_analysis.py /code/transaction_analysis.py
COPY ./SqlData.py /code/SqlData.py
COPY ./Dockerfile /code/Dockerfile
COPY ./init.sql /code/init.sql
COPY ./docker-compose.yml /code/docker-compose.yml

ENV PYTHONPATH "${PYTHONPATH}:/code"

# Определите переменные окружения для подключения к базе данных MySQL
ENV MYSQL_HOST=db \
    MYSQL_USER=user \
    MYSQL_DATABASE=aml

# Задайте команду для запуска приложения
CMD ["python", "TelegramBot.py"]