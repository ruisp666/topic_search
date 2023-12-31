# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get install -y g++ && \
    apt-get install -y libgmp3-dev


# clean unacessary installation files
RUN rm -rf /var/lib/apt/lists/*

# To be used with decouple for remote deployment
ARG ALLOWED_ORIGINS
ENV ALLOWED_ORIGINS=$ALLOWED_ORIGINS

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


COPY . .
COPY /api /app/api
RUN ls /app/api/assets
RUN python -m pip install -r requirements.txt
# Copy the source code into the container.

# Expose the port that the application listens on.
EXPOSE 8037
# Switch to the non-privileged user to run the application.
# USER appuser
# Run the application.
CMD uvicorn 'api.app:app' --host=0.0.0.0 --port=8037
