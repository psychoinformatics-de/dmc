import os
import cherrypy
import uuid
import hashlib
import json
import base64
import datetime

opj = os.path.join


def is_valid_submission(d):
    """Perform all possible tests and return flag"""
    if 'submitter_id' in d:
        sid = d['submitter_id']
        if '/' in sid:
            # is not a UUID, but could be a path
            return False
        if not os.path.exists(opj('submitter_uuids', sid)):
            # this thing claims it is a recurring submission
            # but we don't know about the one it references
            return False
    return True


def generate_submitter_id(sid):
    """Generate a new public submitter ID"""
    # generate a new ID, add extra randomness so it cannot be
    # guessed from the UUID itself
    sid = hashlib.md5(
        '%s%s' % (sid, uuid.uuid4())).hexdigest()
    # now shorten in to 6 chars with base64 + safety net
    for start in xrange(0, len(sid) - 4):
        id_ = base64.urlsafe_b64encode(sid[start:start + 4])[:6]
        if not os.path.exists(opj('submitters', id_)):
            return id_
    raise RuntimeError("we have serious issues with lack of randomness")


class SurveyDB(object):
    @cherrypy.expose
    def get_rid(self, sid=None):
        """Retrieve the latest record submitted given personal ID"""
        if sid is None:
            # when called without clue, just be happy -- silently
            return None
        sfilename = opj('submitter_uuids', sid)
        if not os.path.exists(sfilename):
            return None
        submitter_id = open(sfilename).read()
        rec_path = opj('submitters', submitter_id, 'record')
        if not os.path.exists(rec_path):
            return None
        record_id = os.path.split(os.path.realpath(rec_path))[-1]
        return record_id

    @cherrypy.expose
    @cherrypy.tools.json_in(force=True)
    def submit(self):
        # this is the form content as decoded JSON, aka a dict
        data = cherrypy.request.json
        if not is_valid_submission(data):
            # XXX should be an error of some kind
            return "Not like that my friend"
        # get an ID for this submitter, generate random UUID
        # if none comes with the submission
        # this is the ID one needs to know to retrieve a previous
        # submission to resubmit an update
        submitter_uuid = str(data.get('submitter_uuid', uuid.uuid4()))

        # at this point we trust the UUID (based on the initial checks)

        # submitter ID
        # this is the 'public' submitter reference we use to indicate
        # which record came from whom
        # this is also the ID people can use to retrieve the 'latest'
        # result
        submitter_file = opj('submitter_uuids', submitter_uuid)
        if os.path.exists(submitter_file):
            # we have a previous submission for this UUID, retrieve the ID
            submitter_id = open(submitter_file).read()
            if not len(submitter_id) == 32:
                # we expect an MD5 sum
                raise ValueError("this should not happen")
        else:
            submitter_id = generate_submitter_id(submitter_uuid)
            # and store for later
            with open(submitter_file, 'w') as _file:
                _file.write(submitter_id)

        # this directory will contain stuff like badges, computed
        # stats, ...
        submitters_dir = opj('submitters', submitter_id)
        if not os.path.exists(submitters_dir):
            os.makedirs(submitters_dir)

        # prep record for storage
        # 1st kill the UUID as the records will be public
        if 'submitter_uuid' in data:
            del data['submitter_uuid']
        # and replace with submitter ID hash
        data['submitter_id'] = submitter_id

        # record submite date -- no time, we don't need that in the
        # public records
        data['submit_date'] = datetime.date.today().isoformat()

        rec_path = opj(submitters_dir, 'record')
        if os.path.exists(rec_path):
            # we have a previous submission, make the record aware of it
            # the ID is the filename where the 'record' link points to
            prev_record_id = os.path.split(os.path.realpath(rec_path))[-1]
            if not len(prev_record_id) == 32:
                # we expect an MD5 sum
                raise ValueError("this should not happen")
            data['prev_record_id'] = prev_record_id

        # record is final, serialize and store using its identity as the name
        record = json.dumps(data)
        record_id = hashlib.md5(record).hexdigest()
        with open(opj('records', record_id), 'w') as _file:
            _file.write(record)

        # finally populate public data for this submitter
        # for now place the latest record in here
        if os.path.exists(rec_path):
            os.unlink(rec_path)
        os.symlink(opj('..', '..', 'records', record_id), rec_path)

        # return private and public IDs to the submitter, they
        # need to be displayed for future reference
        # record ID is not needed, can be obtained via submitter_id
        return str((submitter_uuid, submitter_id))


if __name__ == '__main__':
    conf = {
        '/': {'tools.staticdir.on': True,
                'tools.staticdir.root': os.path.abspath(os.curdir),
                'tools.staticdir.dir': 'client',
                'tools.staticdir.index': 'timeline.html'}
    }
    cherrypy.quickstart(SurveyDB(), config=conf)
