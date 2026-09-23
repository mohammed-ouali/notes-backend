import asyncio
from collections.abc import AsyncIterator
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageError(Exception):
    pass

class StorageObjectNotFoundError(StorageError):
    pass

class Storage:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name

    async def create_bucket_if_not_exists(self) -> None:
        try:
            bucket_exists = await asyncio.to_thread(self.client.bucket_exists, self.bucket_name)
    
            if not bucket_exists:
                await asyncio.to_thread(self.client.make_bucket, self.bucket_name)
    
        except S3Error as exception:
            raise StorageError(f"Failed to initialize storage bucket: {self.bucket_name}") from exception

    async def upload(self, object_key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(self.client.put_object, self.bucket_name, object_key, BytesIO(data), len(data), content_type)

        except S3Error as exception:
            raise StorageError(f"Failed to upload object: {object_key}") from exception

    async def get(self, object_key: str) -> AsyncIterator[bytes]:
        response = None

        try:
            response = await asyncio.to_thread(self.client.get_object, self.bucket_name, object_key)

            while True:
                chunk = await asyncio.to_thread(response.read, 1024 * 1024)

                if not chunk:
                    break

                yield chunk

        except S3Error as exception:
            if exception.code == "NoSuchKey":
                raise StorageObjectNotFoundError(f"Object not found: {object_key}") from exception

            raise StorageError(f"Failed to retrieve object: {object_key}") from exception

        finally:
            if response is not None:
                response.close()
                response.release_conn()

    async def delete(self, object_key: str) -> None:
        try:
            await asyncio.to_thread(self.client.remove_object, self.bucket_name, object_key)

        except S3Error as exception:
            raise StorageError(f"Failed to delete object: {object_key}") from exception