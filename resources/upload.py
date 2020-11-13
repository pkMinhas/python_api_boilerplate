from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from application_error import ApplicationError
from werkzeug.utils import secure_filename
import tempfile
import os
from services.aws_s3 import AwsS3
from PIL import Image, UnidentifiedImageError
from datetime import datetime
from services.user_profile import UserProfileService
import uuid

__PROFILE_PIC_MAX_WIDTH__ = 400
__PROFILE_PIC_MAX_HEIGHT__ = 400


def __allowed_file__(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {"jpg", "png", "jpeg", "bmp"}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def __resize_picture__(full_file_path, resized_image_path, max_w=400, max_h=400):
    try:
        image = Image.open(full_file_path)
        image.thumbnail((max_w, max_h))
        # remove the alpha channel, otherwise we cannot save as jpg
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(resized_image_path, quality=95)
    except UnidentifiedImageError as e:
        raise ApplicationError("Invalid image file!")


def __upload_image__(file, s3_object_name, max_w, max_h):
    if file is None:
        raise ApplicationError("Invalid file!")
    if file.filename == '':
        raise ApplicationError("Invalid filename!")
    if __allowed_file__(file.filename) is False:
        raise ApplicationError("Invalid file type!")

    # Save to temp directory and then upload to s3
    with tempfile.TemporaryDirectory() as tmpdirname:
        print('created temporary directory', tmpdirname)
        # Since user provided file names are inherently insecure, use the secure_filename() method
        filename = secure_filename(file.filename)
        full_file_path = os.path.join(tmpdirname, filename)
        # save to location
        file.save(full_file_path)
        # resize image
        resized_image_path = os.path.join(tmpdirname, f"{uuid.uuid4()}.jpg")
        __resize_picture__(full_file_path, resized_image_path, max_w, max_h)
        # upload to s3
        AwsS3.upload_file(resized_image_path, s3_object_name)


class ProfilePictureUpload(Resource):
    @jwt_required
    def post(self):
        """
        All pictures are resized & uploaded to public directory
        """
        user_id = get_jwt_identity()
        # check if the post request has the file part
        if 'file' not in request.files:
            raise ApplicationError("Key 'file' not a part of request!")
        file = request.files['file']
        # generate profile pic name with timestamp
        current_timestamp = datetime.timestamp(datetime.now())
        # NOTE: the object name is based on convention :
        # Any object name starting with "public" is publicly visible via S3
        s3_object_name = f"public/profile/{user_id}-{current_timestamp}.jpg"
        __upload_image__(file, s3_object_name, __PROFILE_PIC_MAX_WIDTH__, __PROFILE_PIC_MAX_HEIGHT__)
        # Make entry
        UserProfileService.update_profile_picture(user_id, new_pic_object_name=s3_object_name)
        return {
            "filename": s3_object_name,
            "userId": user_id,
            "url": AwsS3.get_object_url(s3_object_name)
        }
