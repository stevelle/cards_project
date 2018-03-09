FROM python:3.6.2-alpine3.6

RUN pip install falcon gunicorn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /usr/src/card_table
WORKDIR /usr/src/card_table
COPY . /usr/src/card_table

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "card_table.server"]
