import pika
from cryptography.fernet import Fernet
import wolframalpha
import hashlib
import ClientKeys
import ServerKeys
import pickle
import uuid
import datetime
import os

# read rabbitmq connection url from environment variable
amqp_url = os.environ['AMQP_URL']
url_params = pika.URLParameters(amqp_url)

# connect to rabbitmq
connection = pika.BlockingConnection(url_params)
chan = connection.channel()

# declare a new queue
# durable flag is set so that messages are retained
# in the rabbitmq volume even between restarts
chan.queue_declare(queue='wolf')

print("[", datetime.datetime.now(), "] ", "Launch MQ subscriber at Microservice 2")
print("[", datetime.datetime.now(), "] ", "Connecting to <amqp://rabbit_mq?connection_attempts=10&retry_delay=10> on queue wolf")

def receive_msg(ch, method, properties, body):
    print("[", datetime.datetime.now(), "] ", "Accepted new messages from MQ Broker ", properties.reply_to)
    db = pickle.loads(body[10:])
    key = ClientKeys.Encryptionkey
    fernet = Fernet(db[1])
    
    # decrypt the encrypted string with the
    # Fernet instance of the key,
    # that was used for encrypting the string
    # encoded byte string is returned by decrypt method,
    # so decode it to string with decode methods
    decMessage = fernet.decrypt(db[2]).decode()
    print("[", datetime.datetime.now(), "] ", "Decrypt: Using Key: ", db[1], "| Plain text: ", decMessage)
    print("[", datetime.datetime.now(), "] ", "Determine ", decMessage ," is a math (or non-math) question")
    question = decMessage
    
    # determines if it is a math qiestion or a regular question
    mathprob = 0
    for i in range(0, len(question)):
        if question[i] == '+' or question[i] == '-' or question[i] == '/' or question[i] == '*':
            mathprob = 1
    # if it is a math question then it sends it to microservice3
    if (mathprob == 1):
        print("[", datetime.datetime.now(), "] ", "Sending math question to Microservice 3: ", question)
        key = ClientKeys.Encryptionkey
        fernet = Fernet(key)
        encMessage = fernet.encrypt(question.encode())
        decMessage = fernet.decrypt(encMessage).decode()
        result = hashlib.md5(encMessage)
        dba = {1: key, 2: encMessage, 3: result.digest()}
        msg = pickle.dumps(dba)
        question = bytes(f"{len(msg):<{10}}", 'utf-8') + msg

        class produce(object):

            def __init__(self):
                # connect to rabbitmq
                self.connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
                self.chan = self.connection.channel()
                result = self.chan.queue_declare(queue='', exclusive=True)
                self.callback_queue = result.method.queue
                self.chan.basic_consume(queue=self.callback_queue,
                                        on_message_callback=self.on_response)
                self.response = None
                self.corr_id = None

            def on_response(self, ch, method, props, body):
                if self.corr_id == props.correlation_id:
                    self.response = body

            def call(self, n):
                self.response = None
                self.corr_id = str(uuid.uuid4())
                self.chan.basic_publish(exchange='', routing_key='meth',
                                        body=n, properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                                correlation_id=self.corr_id, ))
                self.connection.process_data_events(time_limit=None)
                return self.response

        asdf = produce()

        answer = asdf.call(question)
        dba = pickle.loads(answer[10:])
        answer = fernet.decrypt(dba[1]).decode()
        print("[", datetime.datetime.now(), "] ", "Received answer from Microservice 3: ", answer)
    else:
        print("[", datetime.datetime.now(), "] ", "Sending non-math question to Wolframalpha: ", question)
        # App id obtained by the above steps
        app_id = ServerKeys.wolf_id

        # Instance of wolf ram alpha
        # client class
        client = wolframalpha.Client(app_id)

        # Stores the response from
        # wolf ram alpha
        res = client.query(question)

        # Includes only text from the response
        try:
            answer = next(res.results).text
            print("[", datetime.datetime.now(), "] ", "Received answer from Wolframalpha: ", answer)
        except StopIteration:
            answer = "Wolframalpha error"
            print("[", datetime.datetime.now(), "] ", "Received answer from Wolframalpha: ", answer)

    encMessage = fernet.encrypt(answer.encode())
    print("[", datetime.datetime.now(), "] ", "Encrypt: Key: ", key, " | Ciphertext: ", encMessage)
    db2 = {1: encMessage, 2: db[3]}

    msg = pickle.dumps(db2)
    msg = bytes(f"{len(msg):<{10}}", 'utf-8') + msg
    response = msg

    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id= \
                                                         properties.correlation_id),
                     body=response)
    print("[", datetime.datetime.now(), "] ", "Sending answer: ", response, " by replying to messages to ", properties.reply_to, " on key ", key)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# to make sure the consumer receives only one message at a time
# next message is received only after acking the previous one
chan.basic_qos(prefetch_count=1)

# define the queue consumption
chan.basic_consume(queue='wolf',
                   on_message_callback=receive_msg)

# start consuming
chan.start_consuming()
