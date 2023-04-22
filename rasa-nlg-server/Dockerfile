FROM rasa/rasa:3.4.0

WORKDIR /app
ENV HOME=/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

USER root

RUN pip install --upgrade pip && \
pip install ddtrace && \
pip install aiohttp-retry
# pip install asyncio

COPY . .

USER 1001

ENTRYPOINT [ "python" ]

CMD [ "nlg_server.py" ]
