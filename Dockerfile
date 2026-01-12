FROM python:3.13-slim

LABEL authors="ksaha"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "app/main.py"]

#ENTRYPOINT ["top", "-b"]
