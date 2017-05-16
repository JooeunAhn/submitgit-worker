from datetime import datetime
import kronos
import random
import pika
import json

import requests as rq


from submitgit.models import SGUser, SGProfile, SGCourse, SGRepository, SGAssignment
from worker.loader import load_credential

"""
@kronos.register('* * * * *')
def complain():
    com = ["aaa", "bbb"]
    print (random.choice(com))
"""

url = "http://submitgit-stella.ap-northeast-2.elasticbeanstalk.com/"


def connect_queue(data):
    credential = pika.PlainCredentials(load_credential('RQ_ID'), load_credential('RQ_PASSWORD'))
    parameters = pika.ConnectionParameters(load_credential('RQ_IP'),
                                           5672,
                                           "/",
                                           credential)
    connection = pika.BlockingConnection(parameters=parameters)
    channel = connection.channel()

    channel.queue_declare(queue=load_credential('QUEUE_NAME'), durable=True)
    message = json.dumps(data)
    channel.basic_publish(exchange='',
                          routing_key=load_credential('QUEUE_NAME'),
                          body=message,
                          properties=pika.BasicProperties(
                              delivery_mode=2,
                          )) 
    connection.close()


@kronos.register('50 * * * *')
def submit():
    now = datetime.now()
    assignment_list = SGAssignment.objects.filter(deadline__gte=now)
    
    for assignment in assignment_list:
        repo_list = assignment.course.sgrepository_set.all()
        for repo in repo_list:
            # assuming getting file...
            # files = {'file': open('somefile.pdf', 'rb')}
            # values = {'author': 'John Smith'}
            # r = requests.post(url, files=files, data=values)
            # TODO have to remove blank=True in raw_code

            data = {"student": repo.student.id, "assignment": assignment.id}
            token = load_credential("auth_token")
            res = rq.post(url+"api/v1/submission/",
                          data=data,
                          headers={"Authorization": "Token %s" % token})
            res_data = json.loads(res.text)
            queue_data = {'id': res_data['id'], 'stdin': assignment.test_input,
                          'time': assignment.test_time, 'is_test': assignment.is_test,
                          'output': assignment.test_output,
                          'language': 0, 'code': "print 'Jooeun'",} # TODO NEED TO INPROVE
            connect_queue(queue_data)
