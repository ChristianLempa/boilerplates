FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN python -m pip install --proxy="http://cloudproxy.zf-world.com:8080" --upgrade pip
RUN pip install --no-cache-dir --proxy="http://cloudproxy.zf-world.com:8080" --upgrade -r /code/requirements.txt

COPY ./ /code

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]docker images