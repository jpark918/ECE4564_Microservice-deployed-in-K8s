# basic python image
FROM python:3.7

# install pika to access rabbitmq
RUN pip install --upgrade pip
RUN pip3 install pika
RUN pip3 install cryptography
RUN pip3 install tweepy
RUN pip3 install paramiko
RUN pip3 install wolframalpha
RUN pip3 install uuid
RUN pip install pickle-mixin

# Without this setting, Python never prints anything out.
ENV PYTHONUNBUFFERED=1

# declare the source directory
WORKDIR /usr/src/app/producer

# copy the file
COPY producer.py .
COPY ClientKeys.py .
# start command
CMD [ "python", "producer.py" ]