# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/
LABEL authors="sapereira"

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get install -y g++ && \
    apt-get install -y libgmp3-dev


# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
#ENV PYTHONUNBUFFERED=0

# Dweal with numba cache problems
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

ENV TOPIC_MODELS_PATH=topic_models

WORKDIR /app

# Create a non-privileged user that the api will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

RUN mkdir -p /nonexistent

RUN chmod -R 777 /nonexistent
# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.

RUN python -m pip install --upgrade pip && \
    pip install --upgrade setuptools &&  \
    pip install --upgrade wheel


RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt


# Copy the source code into the container.
COPY . .
COPY topic_models ./app
# Expose the port that the application listens on.
EXPOSE 8000
# Switch to the non-privileged user to run the application.
# USER appuser
# Run the application.
CMD uvicorn 'api.app:app' --host=0.0.0.0 --port=8000
