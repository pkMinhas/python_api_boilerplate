from database_manager import DatabaseManager as DM
from constants import UserProfile
from datetime import datetime
from application_error import ApplicationError
from services.aws_s3 import AwsS3


class UserProfileService:
    @classmethod
    def user_profile_exists(cls, user_id):
        count = DM.db[UserProfile.COLLECTION_NAME].count_documents({UserProfile.USERID: user_id})
        return count > 0

    @classmethod
    def get_user_profile(cls, user_id):
        return DM.db[UserProfile.COLLECTION_NAME].find_one({UserProfile.USERID: user_id})

    @classmethod
    def upsert_user_profile(cls, user_id, full_name=None, city=None, country=None,
                            gender=None, age=None,
                            occupation=None,
                            mobile_number=0) -> bool:
        if user_id is None or len(user_id) == 0:
            return False
        if full_name is None:
            raise ApplicationError("Please provide your name!")
        if gender is None:
            gender = "undecided"
        data = {
            UserProfile.USERID: user_id,
            UserProfile.FULL_NAME: full_name,
            UserProfile.CITY: city,
            UserProfile.COUNTRY: country,
            UserProfile.GENDER: gender,
            UserProfile.AGE: age,
            UserProfile.OCCUPATION: occupation,
            UserProfile.MOBILE_NUMBER: mobile_number,
            UserProfile.LAST_MODIFIED_AT: datetime.utcnow()
        }
        DM.db[UserProfile.COLLECTION_NAME].update_one(filter={UserProfile.USERID: user_id},
                                                      update={"$set": data},
                                                      upsert=True)

    @classmethod
    def update_profile_picture(cls, user_id, new_pic_object_name):
        # algo: get original object, check if exists pic object name
        # if yes, delete existing object and save this
        # if no, then save this
        profile = cls.get_user_profile(user_id)
        existing_pic_object_name = None
        if profile is not None:
            existing_pic_object_name = profile.get(UserProfile.PICTURE_OBJECT_NAME)

        # save new entry
        # There is a chance that an entry for this user_id does not exist (profile not created).
        # Upsert to ensure that entry is created
        DM.db[UserProfile.COLLECTION_NAME].update_one(filter={UserProfile.USERID: user_id},
                                                      update={"$set":
                                                                  {UserProfile.PICTURE_OBJECT_NAME: new_pic_object_name}
                                                              },
                                                      upsert=True)
        # try to delete existing pic object (ignore failures)
        try:
            if existing_pic_object_name is not None:
                AwsS3.delete_object(existing_pic_object_name)
        except BaseException as e:
            # catching all exceptions
            # ignoring
            print(f"Error while deleting object {existing_pic_object_name}: " + str(e))

