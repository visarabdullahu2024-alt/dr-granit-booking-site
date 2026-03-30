FROM python:3.12-slim

WORKDIR /app
COPY . /app

ENV DOCTOR_APP_HOST=0.0.0.0
ENV DOCTOR_APP_PORT=8000
ENV DOCTOR_APP_DB_PATH=/data/doctor_booking.db

RUN mkdir -p /data
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python3", "server.py"]
