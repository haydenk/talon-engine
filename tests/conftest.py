"""pytest configuration file"""
import os
import sys

"""Add project directory to system path for modules"""
sys.path.append('./url_download_request')
sys.path.append('./rss_feed')
sys.path.append('./global_threat_level')

os.environ['S3_BUCKET_NAME'] = 'pytest_s3_bucket'
os.environ['MYSQL_HOST'] = 'mariadb'
os.environ['MYSQL_USERNAME'] = 'talon'
os.environ['MYSQL_PASSWORD'] = 'talon'
os.environ['MYSQL_DB_NAME'] = 'talon'
