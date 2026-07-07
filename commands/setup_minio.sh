#!/bin/bash

set -e

echo "Configuring MinIO Client..."
mc alias set minio http://"$MINIO_HOST":"$MINIO_PORT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

if mc ls minio/"$MINIO_STORAGE" > /dev/null 2>&1; then
    echo "Bucket '$MINIO_STORAGE' already exists. Skipping creation."
else
    echo "Creating bucket: $MINIO_STORAGE"
    mc mb minio/"$MINIO_STORAGE"
fi

echo "Setting bucket policy to public..."
mc anonymous set download minio/"$MINIO_STORAGE"

echo "Getting policy info..."
mc anonymous get minio/"$MINIO_STORAGE"

echo "MinIO configuration completed!"
exit 0
