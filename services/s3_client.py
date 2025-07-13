import boto3
from config import env


class S3Client:
    def __init__(self, bucket_name: str = env.S3_BUCKET_NAME):
        self._bucket_name = bucket_name
        self._session = boto3.Session(
            aws_access_key_id=env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            region_name=env.AWS_REGION,
        )
        self._client = self._session.client('s3')

    def upload_file(self, file_path: str, object_name: str) -> None:
        """
        Upload a file to the S3 bucket.
        :param file_path: The path to the file to upload.
        :param object_name: The name of the object in the S3 bucket.
        """
        try:
            self._client.upload_file(file_path, self._bucket_name, object_name)
            print(f"File {file_path} uploaded to {self._bucket_name}/{object_name}.")
        except Exception as e:
            print(f"Error uploading file: {e}")

    def delete_object(self, file_path: str) -> None:
        """
        Delete a file from the S3 bucket.
        :param file_path: The path to the file to delete.
        """
        try:
            self._client.delete_object(Bucket=self._bucket_name, Key=file_path)
            print(f"File {file_path} deleted from {self._bucket_name}.")
        except Exception as e:
            print(f"Error deleting file: {e}")

    @property
    def bucket_name(self) -> str:
        """
        Get the name of the S3 bucket.
        :return: The name of the S3 bucket.
        """
        return self._bucket_name