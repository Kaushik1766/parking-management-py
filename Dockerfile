FROM python:3.13.11-slim-trixie
LABEL authors="ksaha"

WORKDIR code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "--port", "8000", "--host", "0.0.0.0", "app/main.py"]

#ENTRYPOINT ["top", "-b"]