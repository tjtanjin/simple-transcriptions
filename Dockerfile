FROM python:3.12

MAINTAINER Tan Jin (tjtanjin)

# install system wide dependencies
RUN apt-get -yqq update
RUN apt-get -yqq install tesseract-ocr

# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .

# install app-specific dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-telegram-bot[job-queue]

# app command
CMD ["python", "-u", "./main.py"]