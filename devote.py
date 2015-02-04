from hammock import Hammock
import json
import base64

USERNAME = "my-email@example.com"
API_KEY = "my-devote-api-key"
BASE_URL = "https://devote.io/api"
VERSION = "v1"


class DevoteApiError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class Devote(object):

    def __init__(self):

        auth = "ApiKey %s:%s" % (USERNAME, API_KEY)

        headers = {
            "Authorization": auth,
            'content-type': 'application/json'
        }
        self.url = Hammock("%s/%s" % (BASE_URL, VERSION), verify=False, append_slash=True, headers=headers)

    def _get(self, resource):
        return self.url(resource).GET()

    def _post(self, resource, params):
        return self.url(resource).POST(data=params)

    def project_list(self):
        return self._get("project")

    def get_project(self, project_id):
        return self._get("project/%d" % project_id)

    def _post_reward(self, message, group_id=None, project_id=None, url=None, attachment=None, public=False):
        group = None
        if not url and not attachment:
            raise DevoteApiError("You must supply a url or an attachment to post a reward")
        elif public is True:
            if project_id is None:
                raise DevoteApiError("Public rewards must have a project_id")
        else:
            if group_id is None:
                raise DevoteApiError("Group rewards must have a group_id")
            else:
                group_data = self._get("group/%d" % group_id).json()
                group = group_data['resource_uri']
                project_id = group_data['project']

        project_data = self.get_project(project_id).json()
        reward_topic = project_data['reward_topic']
        user = project_data['user']

        post_params = {
            "body": message,
            "topic": reward_topic,
            "user": user
        }
        pybb_post = self._post("post", json.dumps(post_params))
        post = pybb_post.json()['resource_uri']

        s3media_params = {
            "group": group,
            "post": post,
        }

        if url is not None:
            s3media_params["download_link"] = url
            s3media_post = self._post("s3media", json.dumps(s3media_params))

        else:
            with open(attachment, 'rb') as attachment_file:
                encoded_file = base64.b64encode(attachment_file.read())
                file_field = {
                    "name": attachment.rsplit("/", 1)[1],
                    "file": encoded_file,
                }
                s3media_params['attachment'] = file_field
                s3media_post = self.post("s3media", json.dumps(s3media_params))

        s3media = s3media_post.json()
        print s3media
        return s3media

    def post_reward(self, group_id, message, url=None, attachment=None):
        return self._post_reward(message, group_id=group_id, url=url, attachment=attachment)

    def post_public_reward(self, project_id, message, url=None, attachment=None):
        return self._post_reward(message, project_id=project_id, url=url, attachment=attachment, public=True)
