import pika
import tweepy
from cryptography.fernet import Fernet
import ClientKeys
import hashlib
import pickle
import time
import uuid
import datetime
import os

tweetindex = 0;
avgtwt = 0;
processtwt = 0;
start_time = 0;
avgtime = []
testlist = []
usedlist = []

# twitter log in variables
bearer_token = ClientKeys.twitterbearer
screen_name = ClientKeys.twitterName
client = tweepy.Client(bearer_token)
twitterid = client.get_user(username=screen_name)

# Get User's Tweets
# This endpoint/method returns Tweets composed by a single user, specified by
# the requested user ID
print("[", datetime.datetime.now(), "] ", "Launch MQ publisher at Microservice 1")
while (1):
    tweetobj = ""
    user_id = twitterid.data.id
    response = client.get_users_tweets(user_id, max_results=20)

    #store all pulled tweets into a list
    for stuff in response.data:
        testlist.append(stuff)
    # checks if there is a new tweet posted after we pull the latest 20 tweets from the account
    try:
        newtweetfound = 0
        for stuffitem in testlist:
            if newtweetfound == 1:
                break
            if len(usedlist) == 0: #at the very beginning of the program usedlist is empty
                tweetobj = stuffitem
                usedlist.append(stuffitem)  # add it to used list
                testlist.remove(stuffitem)  # remove it from list of tweets to be used (take care not to have duplicate)
                break
            for index, item in enumerate(usedlist):
                endoflist = 0
                used = 0
                if stuffitem.text == item.text: #if tweet has already been used
                    break
                    used = 1
                    if index == len(usedlist) - 1: #check if I am on the last index in usedlist
                        endoflist = 1
                elif endoflist == 0 and used == 0 and index == len(usedlist) - 1: #if tweet has not been used
                    tweetobj = stuffitem
                    usedlist.append(stuffitem) #add it to used list
                    testlist.remove(stuffitem) #remove it from list of tweets to be used (take care not to have duplicate)
                    newtweetfound = 1
                    break
        start_time = time.time()
    except:
        print("[", datetime.datetime.now(), "] ", "no more new tweets")

    # gets the text from the tweet
    brek = []
    if tweetobj == "":
        continue
    tweetobj = tweetobj.text
    
    # parses tweet to get question
    for i in range(0, len(tweetobj)):
        if tweetobj[i] == '"':
            brek.append(i)
    if len(brek) != 2:
        print("[", datetime.datetime.now(), "] ", "You messed up the format ex: #ECE4564T18 “How old is the moon?”")

    brek[0] = brek[0] + 1
    hold = tweetobj[brek[0]:brek[1]]
    tweetobj = hold

    key = ClientKeys.Encryptionkey

    # Instance the Fernet class with the key

    fernet = Fernet(key)

    # then use the Fernet class instance
    # to encrypt the string, the string must
    # be encoded to byte string before encryption
    encMessage = fernet.encrypt(tweetobj.encode())
    decMessage = fernet.decrypt(encMessage).decode()

    result = hashlib.md5(encMessage)

    db = {1:key, 2: encMessage, 3:result.digest()}
    msg = pickle.dumps(db)
    msg = bytes(f"{len(msg):<{10}}", 'utf-8')+msg
    
    # read rabbitmq connection url from environment variable

    # close the channel and connection
    # to avoid program from entering with any lingering
    # message in the queue cache
    class produce(object):

        def __init__(self):
            amqp_url = os.environ['AMQP_URL']

            # connect to rabbitmq
            self.connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
            self.chan = self.connection.channel()
            result = self.chan.queue_declare(queue='', exclusive=True)
            self.callback_queue = result.method.queue
            self.chan.basic_consume(queue=self.callback_queue,
                               on_message_callback=self.on_response)
            print("[", datetime.datetime.now(), "] ", "Connecting to <amqp://rabbit_mq?connection_attempts=10&retry_delay=10> on queue wolf")
            self.response = None
            self.corr_id = None
        
        # gets the body of the messsage
        def on_response(self, ch, method, props, body):
            if self.corr_id == props.correlation_id:
                self.response = body
        # sends a request to wolfframe alpha
        def call(self, n):
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.chan.basic_publish(exchange='', routing_key='wolf',
                               body = n, properties=pika.BasicProperties(reply_to=self.callback_queue,correlation_id=self.corr_id,))
            self.connection.process_data_events(time_limit=None)
            return self.response


    asdf = produce()
    print("[", datetime.datetime.now(), "] ", "Getting new Question: ", tweetobj)
    print("[", datetime.datetime.now(), "] ", "Encrypt: Generated Key: ", key ,"| Cipher text: ", encMessage)
    print("[", datetime.datetime.now(), "] ", "Sending data: ", db, " to Microservice 2")


    data = asdf.call(msg)

    if(data != None):
        db = pickle.loads(data[10:])
        print("[", datetime.datetime.now(), "] ", "Received data: ", db, " to Microservice 2")
        decMessage = fernet.decrypt(db[1]).decode()
        print("[", datetime.datetime.now(), "] ", "Decrypt: Using Key: ", db[1] ,"| Plain text: ", decMessage)
        hold = time.time() - start_time
        avgtime.append(hold)
        
        tweetindex = tweetindex + 1
        
        #latency calculations
        avgfinal = 0
        mintime = 0
        maxtime = 0
        firsttime = 0
        for i in avgtime:
            avgfinal = avgfinal + i
            if firsttime == 0: #intially store the first time as both min/max
                mintime = i
                maxtime = i
                firsttime = 1
            if i < mintime: #check if smaller time exists
                mintime = i
            if i > maxtime: #check if longer time exists
                maxtime = i
        avgfinal = avgfinal/len(avgtime)
        print("avg latency: ", avgfinal)
        print("min latency: ", mintime)
        print("max latency: ", maxtime)
