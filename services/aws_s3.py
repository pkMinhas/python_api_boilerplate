import boto3
from application_error import ApplicationError
from botocore.exceptions import ClientError
from boto3.exceptions import S3UploadFailedError

class AwsS3:
    """It is important to note that this class follows conventions as designed by the CloudCube Heroku provider"""
    bucket_name = None
    cube_name = None
    s3_client = None
    base_url = None

    @classmethod
    def configure_client(cls, aws_access_key_id, aws_secret_access_key, bucket_name, base_url, cube_name):
        """Must be called before invoking any other method"""
        cls.bucket_name = bucket_name
        cls.cube_name = cube_name
        cls.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        cls.base_url = base_url

    @classmethod
    def get_object_url(cls,object_name):
        if object_name is None or len(object_name) == 0:
            return ""
        return f"{cls.base_url}/{object_name}"

    @classmethod
    def upload_file(cls, source_file_path, s3_object_name):
        """Upload a file to a S3 bucket

        :param source_file_path: File to upload
        :param bucket: Bucket to upload to
        :param s3_object_name: S3 object name
        :return: True if file was uploaded, else False
        """
        if cls.s3_client is None:
            raise ApplicationError("S3 client not configured!", 500)

        # If S3 object_name was not specified, raise error
        if s3_object_name is None:
            raise ApplicationError("Invalid object name for uploading file!", 500)

        # Upload the file
        try:
            print(cls.bucket_name)
            print(source_file_path)
            print(s3_object_name)
            # Cloudcube requires that we add <cubename> before objectname as a path else ops will fail
            response = cls.s3_client.upload_file(source_file_path, cls.bucket_name, f"{cls.cube_name}/{s3_object_name}")
            print(f"Upload response {response}")
        except ClientError as e:
            print(e)
            raise ApplicationError("Unable to upload file. Please try again!")
        except S3UploadFailedError as se3:
            print(se3)
            raise ApplicationError("Unable to upload file. Please try again!")
        return True

    @classmethod
    def delete_object(cls, object_name):
        if object_name is None:
            return
        if len(object_name) == 0:
            return
        # cloud cube wants us to add cubename before objectname to correctly identify and delete object
        final_object_name = f"{cls.cube_name}/{object_name}"
        print(f"Deleting object: {final_object_name}")
        cls.s3_client.delete_object(Bucket=cls.bucket_name, Key=final_object_name)
