"""AWS convenience classes
"""

import boto3
import urllib.parse

class SQS():

    def __init__(self, queue=None):
        self._queue = queue
        self._error = None
        self._client = None
        self._last_message = None
        self._queue_url = None

    @property
    def last_message(self):
        return self._last_message

    @last_message.setter
    def last_message(self, message):
        self._last_message = message

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, error):
        self._error = error

    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, queue):
        self._queue = queue
        return self._queue

    @property
    def client(self):
        if not self._client:
            self._client = boto3.client('sqs')

        return self._client

    @client.setter
    def client(self, client):
        self._client = client
        return self._client

    @property
    def queue_url(self):
        if not self._queue_url:
            queue_filter = 'treasurersbriefcase-{queue}'.format(queue=self._queue)
            queue_list = self._client.list_queues(QueueNamePrefix=queue_filter)
            self._queue_url = queue_list["QueueUrls"].pop()

        return self._queue_url

    @queue_url.setter
    def queue_url(self, queue_url):
        _queue_url = queue_url

    def send_message(self, **kwargs):
        if "queue" in kwargs:
            self.queue = kwargs["queue"]

        message = kwargs["message"]

        try:
            self.client.send_message(QueueUrl=self.queue_url, MessageBody=urllib.parse.quote(message))
            self.last_message = message
            return message
        except:
            self.error = sys.exc_info()[0]
            return None

class SSM_Parameters:
    max_results = 10
    default_path = "/"
    client = None

    def __init__(self, **kwargs):
        if 'MaxResults' in kwargs:
            self.max_results = min(self.max_results, kwargs["MaxResults"])

        self.client = boto3.client('ssm')

    def get_parameter(self, name):
        response = self.client.get_parameter(Name=name, WithDecryption=True)
        parameter = response["Parameter"] if "Parameter" in response else []

        return parameter

    def get_parameters_by_path(self, path):

        response = self.client.get_parameters_by_path(Path = path, Recursive = True, WithDecryption = True, MaxResults = self.max_results)
        next_token = response["NextToken"] if "NextToken" in response else None
        parameters = response["Parameters"] if "Parameters" in response else []

        while next_token:
            response = self.client.get_parameters_by_path(NextToken = next_token, Path = path, Recursive = True, WithDecryption = True, MaxResults = self.max_results)
            if "NextToken" in response:
                next_token = response["NextToken"]
            else:
                next_token = ""

            parameters.extend(response["Parameters"])

        return parameters
