from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.user_profile import UserProfileService
from constants import UserProfile as UserProfileConstants
from schemas.user_profile import UserProfileInputSchema
from datetime import datetime
from services.aws_s3 import AwsS3
from application_error import ApplicationError
from date_utils import pymongo_naive_utc_datetime_to_ms

class UserProfile(Resource):
    @jwt_required
    def get(self):
        """Gets the user's profile"""
        user_id = get_jwt_identity()
        profile_doc = UserProfileService.get_user_profile(user_id)
        if profile_doc is None:
            return None, 404
        else:
            # Never return database object as-is, it might fuck up the clients.
            # Especially true when using mongodb and there might be fields missing in document
            response_dict = {
                "userId": profile_doc.get(UserProfileConstants.USERID, ""),
                "fullName": profile_doc.get(UserProfileConstants.FULL_NAME, ""),
                "age": profile_doc.get(UserProfileConstants.AGE, 99),
                "country": profile_doc.get(UserProfileConstants.COUNTRY, ""),
                "city": profile_doc.get(UserProfileConstants.CITY, ""),
                "gender": profile_doc.get(UserProfileConstants.GENDER, "undecided"),
                "occupation": profile_doc.get(UserProfileConstants.OCCUPATION, ""),
                "mobileNumber": profile_doc.get(UserProfileConstants.MOBILE_NUMBER, 0)
            }
            # Add display pic field
            picture_object_name = profile_doc.get(UserProfileConstants.PICTURE_OBJECT_NAME)
            if picture_object_name is not None:
                response_dict["displayPicUrl"] = AwsS3.get_object_url(picture_object_name)
            else:
                response_dict["displayPicUrl"] = ""
            # Convert the datetime field into a timestamp
            last_modified_at = profile_doc.get(UserProfileConstants.LAST_MODIFIED_AT, datetime.utcnow())
            response_dict["lastModifiedAt"] = pymongo_naive_utc_datetime_to_ms(last_modified_at)

            return response_dict

    def __upsert_profile__(self):
        """Creates the user's profile"""
        user_id = get_jwt_identity()
        data = UserProfileInputSchema().load(request.json)
        UserProfileService.upsert_user_profile(user_id, full_name=data.get("fullName"),
                                               city=data.get("city"),
                                               country=data.get("country"),
                                               gender=data.get("gender"),
                                               age=data.get("age"),
                                               occupation=data.get("occupation"),
                                               mobile_number=data.get("mobileNumber",0))
        return {}, 201

    @jwt_required
    def post(self):
        return self.__upsert_profile__()

    @jwt_required
    def put(self):
        return self.__upsert_profile__()


class PublicUserProfile(Resource):
    def get(self, other_user_id):
        profile_doc = UserProfileService.get_user_profile(other_user_id)
        if profile_doc is None:
            raise ApplicationError("User profile unavailable", 404)
        else:
            # return selected fields when another user requests this id
            response_dict = {
                "userId": profile_doc.get(UserProfileConstants.USERID, ""),
                "fullName": profile_doc.get(UserProfileConstants.FULL_NAME, ""),
                "country": profile_doc.get(UserProfileConstants.COUNTRY, ""),
                "city": profile_doc.get(UserProfileConstants.CITY, "")
            }
            # Add display pic field
            picture_object_name = profile_doc.get(UserProfileConstants.PICTURE_OBJECT_NAME)
            if picture_object_name is not None:
                response_dict["displayPicUrl"] = AwsS3.get_object_url(picture_object_name)
            else:
                response_dict["displayPicUrl"] = ""
            return response_dict
