"""Lambda Function to download URLs from SQS and save to S3"""
import os
from json import loads, dumps
from hashlib import sha256
from urllib.parse import urlparse
import boto3
from requests import Session
from client_request.anonymous_request import AnonymousRequest
from client_request.api_key_request import ApiKeyRequest
from client_request.basic_auth_request import BasicAuthRequest

S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
MYSQL_HOST = os.environ["MYSQL_HOST"]
MYSQL_CONFIG = {
    "user": os.environ["MYSQL_USERNAME"],
    "passwd": os.environ["MYSQL_PASSWORD"],
    "db": os.environ["MYSQL_DB_NAME"],
}


def lambda_handler(event, context):
    """Lambda Function handler method"""
    s3_client = boto3.client('s3')
    status_code = 200
    response_body = []

    for record in event['Records']:
        body = loads(record['body'])
        auth_type = record['messageAttributes']['AuthType']['StringValue']
        class_name = record['messageAttributes']['Class']['StringValue']

        url_request_id = body['id']
        url = body['url'].strip()
        credentials = None
        if 'credentials' in body:
            credentials = body['credentials']

        try:
            sess = Session()
            request = AnonymousRequest(url)

            if auth_type.lower() == 'basic':
                request = BasicAuthRequest(
                    url,
                    username=credentials['username'],
                    password=credentials['password'])

            if auth_type.lower() == 'api_key':
                request = ApiKeyRequest(
                    url,
                    location=credentials['location'],
                    field=credentials['field'],
                    value=credentials['value'])

            res = sess.send(request.create(), timeout=60)
            res.raise_for_status()

            contents = res.text
            hash_of_contents = sha256(url.encode('utf-8') + contents.encode('utf-8'))
            parsed_uri = urlparse(url)
            s3_key_name = "%s/%s" % (parsed_uri.netloc, hash_of_contents.hexdigest())
            object_url = "%s/%s/%s" % (s3_client.meta.endpoint_url, S3_BUCKET_NAME, s3_key_name)
            insert_error_log = False
            error_log_message = None

            try:
                if s3_key_exists(s3_client, S3_BUCKET_NAME, s3_key_name):
                    raise FileExistsError(
                        "Object with key '%s' already exists. Skipping."
                        % hash_of_contents.hexdigest())

                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key_name,
                    Body=contents,
                    ContentType=res.headers.get('Content-Type'),
                    Metadata={"url": url, "class": class_name},
                )
            except FileExistsError as ex:
                # Send some context about this error to Lambda Logs
                insert_error_log = True
                error_log_message = str(ex)

            run_sql_queries(
                class_name=class_name,
                request_id=url_request_id,
                status_message='Completed',
                insert_error_log=insert_error_log,
                insert_s3_object=True,
                log_level='NOTICE',
                error_log_message=error_log_message,
                s3_key_name=s3_key_name,
                object_url=object_url,
            )

            response_body.append({
                "url": url,
                "object_url": object_url,
                "hash": hash_of_contents.hexdigest(),
            })

        except Exception as ex:
            # Send some context about this error to Lambda Logs
            run_sql_queries(
                class_name=class_name,
                request_id=url_request_id,
                status_message='Error',
                insert_error_log=True,
                log_level='ERROR',
                error_log_message=str(ex))

            status_code = 409
            response_body.append({
                "error": str(ex),
            })

    return {
        "status_code": status_code,
        "body": dumps(response_body),
    }


def s3_key_exists(client, bucket, key):
    """Simple function to check if key exists in specified S3 Bucket"""
    response = client.list_objects_v2(Bucket=bucket, Prefix=key)
    for obj in response.get('Contents', []):
        if obj['Key'] == key:
            return True
    return False


def run_sql_queries(**kwargs):
    """Encapsulated DB function to run SQL queries for this function"""
    class_name = kwargs.get('class_name')
    request_id = kwargs.get('request_id')
    s3_key_name = kwargs.get('s3_key_name', None)
    object_url = kwargs.get('object_url', None)
    region = kwargs.get('region', 'us-east-1')
    status_message = kwargs.get('status_message', None)
    insert_error_log = kwargs.get('insert_error_log', False)
    insert_s3_object = kwargs.get('insert_s3_object', False)
    log_level = kwargs.get('log_level', 'INFO')
    error_log_message = kwargs.get('error_log_message', None)
    app_dir = os.path.dirname(os.path.realpath(__file__))
    with open(app_dir + '/db/query.yml', 'r') as infile:
        from yaml import load
        db_files_config = load(stream=infile)

    try:
        from pymysql import connect
        cnx = connect(MYSQL_HOST, **MYSQL_CONFIG)
        db_files = db_files_config[class_name]
        with cnx.cursor() as cur:
            if db_files['update']:
                update_query = fetch_file_contents(db_files['update'])
                cur.execute(update_query, {"new_status": status_message, "entity_id": request_id})
            if insert_error_log and db_files['error_log_insert']:
                insert_query = fetch_file_contents(db_files['error_log_insert'])
                join_query = fetch_file_contents(db_files['error_log_join'])
                cur.execute(insert_query, {
                    "component_name": class_name,
                    "log_level": log_level,
                    "error_message": error_log_message,
                    "entity_id": request_id,
                })
                error_log_id = cur.lastrowid
                cur.execute(join_query, {
                    "error_log_id": error_log_id,
                    "entity_id": request_id,
                })
            if insert_s3_object and db_files['s3_object_insert']:
                select_query = fetch_file_contents(db_files['s3_object_select'])
                cur.execute(select_query, s3_key_name)
                if cur.rowcount > 0:
                    result = cur.fetchone()
                    s3_object_id = result[0]
                else:
                    insert_query = fetch_file_contents(db_files['s3_object_insert'])
                    cur.execute(insert_query, {
                        "key_name": s3_key_name,
                        "region": region,
                        "object_url": object_url,
                        "entity_id": request_id,
                    })
                    s3_object_id = cur.lastrowid
                join_query = fetch_file_contents(db_files['s3_object_join'])
                cur.execute(join_query, {"entity_id": request_id, "object_id": s3_object_id})
        cnx.commit()
    finally:
        cnx.close()


def fetch_file_contents(filename):
    """Abstracted function to read the contents of a query file and return it"""
    app_dir = os.path.dirname(os.path.realpath(__file__))
    with open(app_dir + filename) as file:
        contents = file.read()
    file.close()
    return contents
