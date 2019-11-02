import pytest
import mock
import os
import boto3
from moto import mock_s3
import json
import yaml
from requests import HTTPError
from url_download_request import lambda_function


@pytest.fixture()
def sqs_event():
    """ Generates SQS Event"""

    return yaml.load(open('tests/unit/url_download_request/handler_test_data.yml'))


@mock_s3
@mock.patch('requests.Session.send', autospec=True)
@mock.patch('pymysql.connect', autospec=True)
def test_lambda_handler_success(mocked_connect, mocked_get, sqs_event):
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket=bucket_name)
    lambda_context = dict(aws_request_id="31437208-923c-4c3c-b8a7-50db7018f88d")

    for record in sqs_event['Records']:
        expected_http_status_code = 200
        expected_body = json.loads(record['body'])
        expected_url = expected_body['url'].strip()
        expected_contents = "<html><body>Mocked HTML response</body></html>"

        mocked_req_obj = mock.Mock()
        mocked_req_obj.status_code = expected_http_status_code
        mocked_req_obj.text = expected_contents
        mocked_req_obj.headers = {"Content-Type": "text/html"}
        mocked_get.return_value = mocked_req_obj

        from hashlib import sha256
        hash_of_contents = sha256(expected_url.encode('utf-8') + expected_contents.encode('utf-8'))

        from urllib.parse import urlparse
        parsed_uri = urlparse(expected_url)
        s3_key_name = "%s/%s" % (parsed_uri.netloc, hash_of_contents.hexdigest())

        ret = lambda_function.lambda_handler(sqs_event, lambda_context)
        assert ret["status_code"] is expected_http_status_code

        new_object = s3.get_object(Bucket=bucket_name, Key=s3_key_name)
        body = new_object.get('Body').read().decode('utf-8')

        assert body == expected_contents

        for data in json.loads(ret["body"]):
            assert expected_url in data['url']
            assert data["hash"] == hash_of_contents.hexdigest()


@mock_s3
@mock.patch('requests.Session.send', autospec=True)
@mock.patch('pymysql.connect', autospec=True)
@pytest.mark.parametrize("expected_http_status,will_fail", [
    (200, False),
    (201, False),
    (301, False),
    (401, True),
    (403, True),
    (500, True)
])
def test_lambda_handler_failed_request(mocked_connect, mocked_get, sqs_event, expected_http_status, will_fail):
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket=bucket_name)
    lambda_context = dict(aws_request_id="31437208-923c-4c3c-b8a7-50db7018f88d")

    for record in sqs_event['Records']:
        mocked_req_obj = mock.Mock()
        mocked_req_obj.status_code = expected_http_status
        mocked_req_obj.text = "mock data"
        mocked_req_obj.headers = {"Content-Type": "text/html"}
        if will_fail:
            mocked_get.side_effect = HTTPError(expected_http_status)
        mocked_get.return_value = mocked_req_obj

        ret = lambda_function.lambda_handler(sqs_event, lambda_context)

        if will_fail:
            assert ret["status_code"] == 409
        else:
            assert ret["status_code"] == 200


@mock_s3
@mock.patch('requests.Session.send', autospec=True)
@mock.patch('pymysql.connect', autospec=True)
def test_lambda_handler_existing_object(mocked_connect, mocked_get, sqs_event):
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket=bucket_name)
    lambda_context = dict(aws_request_id="31437208-923c-4c3c-b8a7-50db7018f88d")

    for record in sqs_event['Records']:
        expected_http_status_code = 200
        expected_body = json.loads(record['body'])
        expected_url = expected_body['url'].strip()
        expected_contents = "<html><body>Mocked HTML response</body></html>"

        mocked_req_obj = mock.Mock()
        mocked_req_obj.status_code = expected_http_status_code
        mocked_req_obj.text = expected_contents
        mocked_req_obj.headers = {"Content-Type": "text/html"}
        mocked_get.return_value = mocked_req_obj

        from hashlib import sha256
        hash_of_contents = sha256(expected_url.encode('utf-8') + expected_contents.encode('utf-8'))

        s3.put_object(Bucket=bucket_name, Key=hash_of_contents.hexdigest(), Body=expected_contents)

        ret = lambda_function.lambda_handler(sqs_event, lambda_context)
        assert ret["status_code"] == 200


@mock_s3
@pytest.mark.parametrize("expected_key,expected_body,expected_file_exists", [
    ('file_that_exists', '<html><body>Mocked HTML response</body></html>', True),
    ('file_that_does_not_exist', '<html><body>Mocked HTML response</body></html>', False),
])
def test_s3_key_exists(expected_key, expected_body, expected_file_exists):
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket=bucket_name)
    if expected_file_exists:
        s3.put_object(Bucket=bucket_name, Key=expected_key, Body=expected_body)

    ret = lambda_function.s3_key_exists(s3, bucket_name, expected_key)

    assert ret is expected_file_exists
