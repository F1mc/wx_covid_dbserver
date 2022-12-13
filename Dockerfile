FROM python:3.8

WORKDIR /usr/src/app
COPY . .
EXPOSE 4001
RUN pip install -r requirements.txt

CMD ["python", "/usr/src/app/app_server.py"]