#!/bin/sh
/usr/bin/minio server /data --console-address :9001 & 
sleep 10  # Give the server more time to start
mc alias set myminio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
mc mb myminio/my-bucket --ignore-existing
mc anonymous set download myminio/my-bucket
mc policy set public myminio/my-bucket
mc admin user add myminio appuser apppassword
mc admin policy attach myminio readwrite --user=appuser
echo 'MinIO Configuration Complete'
tail -f /dev/null  # Keep the container running