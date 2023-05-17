import pika
import ClientKeys
from cryptography.fernet import Fernet
import wolframalpha
import ServerKeys
import hashlib
import pickle
import os
import datetime

# read rabbitmq connection url from environment variable
amqp_url = os.environ['AMQP_URL']
url_params = pika.URLParameters(amqp_url)

# connect to rabbitmq
connection = pika.BlockingConnection(url_params)
chan = connection.channel()

# declare a new queue
# durable flag is set so that messages are retained
# in the rabbitmq volume even between restarts
chan.queue_declare(queue='meth')


print("[", datetime.datetime.now(), "] ", "Launch MQ subscriber at Microservice 3")
print("[", datetime.datetime.now(), "] ", "Connecting to <amqp://rabbit_mq?connection_attempts=10&retry_delay=10> on queue meth")
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
    print("[", datetime.datetime.now(), "] ", "Received data: ", db[2])
    decMessage = fernet.decrypt(db[2]).decode()

    #print("decrypted string: ", decMessage)

    question = decMessage
    print("[", datetime.datetime.now(), "] ", "Decrypt: Key: ", key, " | Plain text: ", decMessage)

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
    except StopIteration:
        answer = "Wolframalpha error"
        print("[", datetime.datetime.now(), "] ", "Received answer from Wolframalpha: ", answer)

    print("[", datetime.datetime.now(), "] ", "For ", decMessage, " the answer is ", answer)

    encMessage = fernet.encrypt(answer.encode())
    print("[", datetime.datetime.now(), "] ", "Encrypt: Key: ", key, " | Ciphertext: ", encMessage)
    db2 = {1: encMessage, 2: db[3]}

    msg = pickle.dumps(db2)
    msg = bytes(f"{len(msg):<{10}}", 'utf-8') + msg
    response = msg

    result = hashlib.md5(encMessage)
    print("[", datetime.datetime.now(), "] ", "Generated MD5 Checksum: ", result.digest())
    print("[", datetime.datetime.now(), "] ", "Sending answer: ", response, " by replying to messages to ", properties.reply_to, " on key ", key)


    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id= \
                                                         properties.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# to make sure the consumer receives only one message at a time
# next message is received only after acking the previous one
chan.basic_qos(prefetch_count=1)

# define the queue consumption
chan.basic_consume(queue='meth',
                   on_message_callback=receive_msg)

# start consuming
chan.start_consuming()
