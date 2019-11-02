insert into `s3_object` (key_name, region, object_url, createdAt)
values (%(key_name)s, %(region)s, %(object_url)s, NOW());
