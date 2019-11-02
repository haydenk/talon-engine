insert into `ErrorLogEntry` ( subSystem
                            , componentName
                            , logLevel
                            , message
                            , acknowledged
                            , createdAt
                            , modifiedAt)
values ('lambda', %(component_name)s, %(log_level)s, %(error_message)s, 0, NOW(), NOW());
