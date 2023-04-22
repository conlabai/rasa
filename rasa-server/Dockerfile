# Python version we use
ARG PYVERSION=3.8
FROM python:${PYVERSION}-slim as builder
ARG PYVERSION

# install dependencies of interest
USER root
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt && \
    python -m spacy download ru_core_news_lg && \
    python -m pip install ddtrace

# set workdir and copy data files from disk
# note the latter command uses .dockerignore

FROM python:${PYVERSION}-slim as runtime
ARG PYVERSION

WORKDIR /app
ENV HOME=/app

COPY --from=builder /usr/local/lib/python${PYVERSION}/site-packages /usr/local/lib/python${PYVERSION}/site-packages 
COPY --from=builder /usr/local/bin /usr/local/bin 
COPY . .

# make sure the container process can write to .rasa directory
RUN mkdir .rasa || true
RUN mkdir models || true
RUN mkdir .config || true
RUN chown 1000 .rasa models .config
# set the user to run, don't run as root
USER 1000

# set entrypoint for interactive shells
ENTRYPOINT ["rasa"]

# command to run when container is called to run
CMD ["run", "--enable-api", "--port", "8080"]
