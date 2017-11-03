import os
import sys

import hashlib
import json
import datetime

# server version
__version__ = 2

opj = os.path.join

cwd = os.path.dirname(__file__)
private_dir = opj(cwd, '../records/private')
public_dir = opj(cwd, '../records/public')
utc_now = datetime.datetime.now().strftime('%Y.%m.%d-%H.%M.%S')
valid_surveys = ['neuroscience', 'datascience', 'demo', 'cbbs_imaging']


def get_client_ip(environ):
    try:
        return environ['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
        return environ['REMOTE_ADDR']

def get_client_agent(environ):
    try:
        return environ['HTTP_USER_AGENT']
    except KeyError:
        return 'unknown'

def generate_record_id(data, ip):
    rid = hashlib.md5('%s%s%s' % (data, utc_now, ip)).hexdigest()
    return rid


def is_valid_submission(d):
    """Perform all possible tests and return flag"""
    if 'survey_name' in d:
        if d['survey_name'] not in valid_surveys:
            # we only play with stuff we know...
            return False

        if not os.path.isdir(opj(private_dir, d['survey_name'])):
            return False
        if not os.path.isdir(opj(public_dir, d['survey_name'])):
            return False

    if not 'content' in d:
        return False

    return True


def application(environ, start_response):
    status = '404 Not Found'
    output = ''

    if environ['REQUEST_METHOD'] == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0

        request_body = environ['wsgi.input'].read(request_body_size)

        try:
          data = json.loads(request_body)  # form content as decoded JSON
        except:
          data = {}
          status = '400 Bad Request'

        if is_valid_submission(data):
            survey_name = data['survey_name']
            data = data['content']

            # append some useful info
            data['submit_date'] = datetime.date.today().isoformat()
            data['server_version'] = __version__

            # set the dirs we're going to save to
            survey_pub_dir = opj(public_dir, survey_name)
            survey_priv_dir = opj(private_dir, survey_name)

            # get/generate the needed info to save
            client_ip = get_client_ip(environ)
            client_agent = get_client_agent(environ)
            record_id = generate_record_id(data, client_ip)
            record = json.dumps(data)

            # save the public record
            with open(opj(survey_pub_dir, record_id), 'w') as _file:
                _file.write(record)

            # save private file (ip and date/time)
            with open(opj(survey_priv_dir, record_id), 'w') as _file:
                _file.write(json.dumps({ 'ip': client_ip, 'agent': client_agent, 'dt': utc_now }))

            output = 'success.html'
        else:
            status = '400 Bad Request'
            # TODO: should be an error of some kind
            output = 'Not like that my friend'

    # aaaaaand respond to client
    start_response('200 OK', [('Content-type', 'text/plain'),
                              ('Content-Length', str(len(output)))])
    return [output]
