

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get install -y g++ && \
    apt-get install -y libgmp3-dev


# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

ENV MODEL_PATH=True
WORKDIR /app
COPY . .

RUN python -m pip install --upgrade pip && \
    pip install --upgrade setuptools &&  \
    pip install --upgrade wheel


RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

EXPOSE 8050


## Run the dash app located in the current directory on port 8050.
CMD ["python", "dash_app.py"]