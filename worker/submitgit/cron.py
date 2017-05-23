from io import BytesIO
from datetime import datetime, timezone
import kronos
import pika
import json

import requests as rq
from requests.exceptions import RequestException

from submitgit.crypto import decrypt
from submitgit.models import SGAssignment, SGSubmission
from worker.loader import load_credential


url = "http://submitgit-stella.ap-northeast-2.elasticbeanstalk.com/"
github_url = "https://raw.githubusercontent.com/"
lang_extension = {
    0: ".py",
    1: ".rb",
    2: ".clj",
    3: ".php",
    4: ".js",
    5: ".scala",
    6: ".go",
    7: ".c",
    8: ".java",
    9: ".vb",
    10: ".cs",
    11: ".sh",
    12: ".m",
    13: ".sql",
    14: ".pl",
    15: ".cpp"
}


def connect_queue(data):
    credential = pika.PlainCredentials(load_credential('RQ_ID'),
                                       load_credential('RQ_PASSWORD'))
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
    now = datetime.now(timezone.utc)
    assignment_list = SGAssignment.objects.filter(deadline__gte=now)

    for assignment in assignment_list:
        repo_list = assignment.course.sgrepository_set.all()
        for repo in repo_list:
            # already passed
            if SGSubmission.objects.filter(student=repo.student,
                                           assignment=assignment,
                                           is_passed=True).exists():
                continue

            # already working
            if SGSubmission.objects.filter(student=repo.student,
                                           assignment=assignment,
                                           is_working=True).exists():
                continue

            repo_url = [i for i in repo.url.split('/') if i != ""]
            github_repo_name = repo_url.pop()
            github_username = repo_url.pop()

            code = ""
            langid = None

            rq_builder = lambda ext: rq.get(github_url+'%s/%s/master/%s%s' % (
                github_username,
                github_repo_name,
                assignment.test_file_name,
                ext))

            for lang in assignment.test_langids.split(','):
                lang = int(lang)
                ext = lang_extension[lang]
                is_enc = False
                for i in range(2):
                    res = rq_builder(ext)
                    try:
                        res.raise_for_status()
                    except RequestException:
                        is_enc = True
                        ext += '.joon'
                        continue
                    if is_enc:
                        raw_code = res.content
                        key = repo.key
                        enc_code = BytesIO(raw_code)
                        dec_code, size = decrypt(key, enc_code)
                        dec_code.truncate(size)
                        code = dec_code.read().decode('utf-8')
                    else:
                        code = res.text
                    langid = lang
                    if langid == 15:
                        langid = 7
                    break
                if code is not "":
                    break

            if code is "":
                continue

            # if user's code is in submission history, pass the checking
            if SGSubmission.objects.filter(code=code,
                                           assignment=assignment,
                                           student=repo.student,
                                           is_passed=False):
                continue

            files = {
                'raw_code':
                    (assignment.test_file_name+lang_extension[lang], code)
                }
            data = {"student": repo.student.id, "assignment": assignment.id}
            token = load_credential("auth_token")
            res = rq.post(url+"api/v1/submission/",
                          files=files,
                          data=data,
                          headers={"Authorization": "Token %s" % token})
            res_data = json.loads(res.text)
            queue_data = {'id': res_data['id'], 'stdin': assignment.test_input,
                          'time': assignment.test_time,
                          'is_test': assignment.is_test,
                          'output': assignment.test_output,
                          'language': langid, 'code': code}
            connect_queue(queue_data)
