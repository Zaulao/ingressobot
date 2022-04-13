FROM python:3.9-slim
COPY bot/ingresso.py /bot/
WORKDIR /bot
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir requests python-telegram-bot

CMD ["python", "ingresso.py"]