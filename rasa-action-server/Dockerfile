FROM python:3.8-slim

WORKDIR /app
ENV HOME=/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN pip install ddtrace

COPY . .

USER 1001

ENTRYPOINT ["python"]

CMD [ "-m", "rasa_sdk", "--actions", "actions" ]
