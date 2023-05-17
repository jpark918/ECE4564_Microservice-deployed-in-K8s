## Libraries used in the services
* import pika
* import ClientKeys
* from cryptography.fernet import Fernet
* import wolframalpha
* import hashlib
* import ServerKeys
* import pickle
* import uuid
* import datetime
* import os
* import tweepy
* import time

## Run the program

* To run `docker-compose up`

* To close `docker-compose down -v --rmi all --remove-orphans`

## Kubernetes

* individually type 'kubectl apply -f x.yaml' to each of the yaml files

## Specification:
Final Project is the “superset” of Project 2 and Project 3. It is based on the text-based question
and answer system built by previous projects.
- Questions to your Q&A system comes from Twitter Tweets and got answered by
WolframAlpha’s computational knowledge engine for non-math questions and a new computing
services for math-specific questions
- The system includes three microservices and two external services.
- Microservice 1: a non-stopping client program captures a Twitter status object (Tweet)
containing the question text in a streaming mode
- Microservice 2: a dispatching service, which receives question payload from
microservice 1, forwards to different services based on question type, collects answer
and replies to microservice 1.
- Microservice 3: a computing service responsible of answering any math question
- External services: Twitter services and WolframAlpha computational knowledge engine
- Three microservices are hosted in a Kubernetes/Minikube cluster. Each services is deployed
as a deployment of 3 replicas and enabled with a ClusterIP-typed service.
Note: The interaction with IBM Watson’s text-to-speech (TTS) translation API is not
included in the final project.

## Updated Workflow
- The non-stopping client program (microservice 1) captures a Twitter status object (Tweet)
containing the question text in a streaming mode.
- Microservice 1 builds and sends a question “payload” to Microservice 2 via gRPC or MQ.
- Microservice 2 unpacks the payload,
- For non-math questions, sends the question to the WolframAlpha external services and
receives the answer.
- For math specific questions (supported operator includes +, - , *, /), sends the question
to microservice 3 and collect answer.
- Microservice 2 builds and sends an answer “payload” back to Microservice 1.
- Microservice 1 unpacks the payload and displays the answer on the monitor.
- All programs are running in docker containers in K8s pods.
- Microservice pods can be deployed in one or multiple machines.
- Send 20 tweets (10 non-math and 10 math), and records latency to process each tweet
