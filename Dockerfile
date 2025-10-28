FROM python:3.11.4-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

#COPY ./app /app

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
