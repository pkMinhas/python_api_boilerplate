from database_manager import DatabaseManager as DM
from services.security import password_context
from datetime import datetime, timedelta
from application_error import ApplicationError
import uuid
from constants import User, PasswordResetTokens
from services.email import send_email
import secrets
from flask_jwt_extended import (
    create_access_token, create_refresh_token
)
from bson.objectid import ObjectId


class UserRegistrationService:
    @classmethod
    def create_local_user(cls, email, password):
        if cls.is_email_used(email):
            # email already exists
            raise ApplicationError(message="Email address already used by another account!")

        # user does not exist, create
        password_hash = password_context.hash(password)
        current_timestamp = datetime.utcnow()
        email_verification_token = str(uuid.uuid4())
        user_id = DM.db[User.COLLECTION_NAME].insert_one({
            User.EMAIL: email,
            User.PASSWORD_HASH: password_hash,
            User.CREATED_AT: current_timestamp,
            User.LAST_MODIFIED_AT: current_timestamp,
            User.EMAIL_VERIFIED: False,
            User.VERIFICATION_TOKEN: email_verification_token
        }).inserted_id

        cls.__send_email_address_verification_mail__(email, email_verification_token)
        return user_id

    @classmethod
    def validate_email_address_verification_token(cls, email, verification_token):
        user = cls.__get_existing_user_by_email__(email)
        if user is None:
            raise ApplicationError(message="Invalid email id!")
        if user[User.VERIFICATION_TOKEN] == verification_token:
            # token matches, update entry
            DM.db[User.COLLECTION_NAME].update_one({User.EMAIL: email},
                                                   {"$set": {User.EMAIL_VERIFIED: True,
                                                             User.LAST_MODIFIED_AT: datetime.utcnow()}})
            return True
        return False

    @classmethod
    def __send_email_address_verification_mail__(cls, email, verification_token):
        # TODO: change body and subject
        send_email(to=email, subject="Verify MB user", body=f"Verification Token: {verification_token}")

    @classmethod
    def __get_existing_user_by_email__(cls, email):
        return DM.db[User.COLLECTION_NAME].find_one({User.EMAIL: email})

    @classmethod
    def is_email_used(cls, email) -> bool:
        return DM.db[User.COLLECTION_NAME].count_documents(({User.EMAIL: email})) > 0

    @classmethod
    def is_email_address_verified(cls, user_id) -> bool:
        doc = DM.db[User.COLLECTION_NAME].find_one({"_id": ObjectId(user_id)})
        if doc is None:
            return False
        return doc.get(User.EMAIL_VERIFIED, False)

    @classmethod
    def resend_email_address_verification_email(cls, user_id):
        existing_user_doc = DM.db[User.COLLECTION_NAME].find_one({"_id": ObjectId(user_id)})
        if existing_user_doc is None:
            raise ApplicationError("Invalid user!")
        email_address = existing_user_doc.get(User.EMAIL, None)
        if email_address is not None and existing_user_doc.get(User.EMAIL_VERIFIED, False) is False:
            UserRegistrationService.__send_email_address_verification_mail__(email_address,
                                                                             existing_user_doc[User.VERIFICATION_TOKEN])


class UserLoginService:
    @classmethod
    def get_login_tokens(cls, email, supplied_password):
        """Gets the user matching email and password"""
        userDoc = DM.db[User.COLLECTION_NAME].find_one({User.EMAIL: email})
        if userDoc is None:
            raise ApplicationError("Invalid credentials!", 403)

        # now we match the password hash
        if password_context.verify(supplied_password, userDoc[User.PASSWORD_HASH]):
            # correct user
            # generate jwt and return
            # We use the _id as the identity value in the access token
            # mark the access token as fresh since we just verified the user's login email and password
            user_id = str(userDoc["_id"])  # convert to str from ObjectId
            return {
                "accessToken": create_access_token(user_id, fresh=True),
                "refreshToken": create_refresh_token(user_id)
            }
        else:
            raise ApplicationError("Invalid credentials!", status_code=403)

    @classmethod
    def send_password_reset_email(cls, email):
        user_doc = DM.db[User.COLLECTION_NAME].find_one({User.EMAIL: email})
        if user_doc is None:
            # do nothing and return if the user doc is not available
            return
        # generate reset password token
        reset_password_token = secrets.token_urlsafe()
        # token valid for 30 mins from now
        valid_till = datetime.utcnow() + timedelta(minutes=30)
        # save to reset token collection
        user_id = str(user_doc["_id"])
        DM.db[PasswordResetTokens.COLLECTION_NAME].insert_one({
            PasswordResetTokens.USERID: user_id,
            PasswordResetTokens.TOKEN: reset_password_token,
            PasswordResetTokens.IS_CONSUMED: False,
            PasswordResetTokens.VALID_TILL: valid_till
        })
        # TODO: change mail subject line & body
        send_email(to=email,
                   subject=f"MB: Password reset email",
                   body=f"UserId: {user_id}, Reset password token: {reset_password_token}, valid till: {valid_till}")

    @classmethod
    def reset_password_using_token(cls, user_id, token, new_password):
        """Given a password reset token, will reset password if all criteria match"""
        # match criteria = userId, token, !isConsumed & validTill > currentTime
        password_reset_doc = DM.db[PasswordResetTokens.COLLECTION_NAME].find_one({
            PasswordResetTokens.USERID: user_id,
            PasswordResetTokens.TOKEN: token,
            PasswordResetTokens.IS_CONSUMED: False,
            PasswordResetTokens.VALID_TILL: {"$gte": datetime.utcnow()}
        })
        if password_reset_doc is None:
            raise ApplicationError("Invalid password reset token. Please try again!")
        # TODO: use transactions (bit complicated but the recommended way)
        new_password_hash = password_context.hash(new_password)
        DM.db[User.COLLECTION_NAME].update_one(filter={"_id": ObjectId(user_id)},
                                               update={"$set": {User.PASSWORD_HASH: new_password_hash,
                                                                User.LAST_MODIFIED_AT: datetime.utcnow()}})
        DM.db[PasswordResetTokens.COLLECTION_NAME].update_one(filter={"_id": ObjectId(password_reset_doc["_id"])},
                                                              update={"$set": {PasswordResetTokens.IS_CONSUMED: True}})

    @classmethod
    def change_password(cls, user_id, existing_password, new_password):
        print(user_id)
        existing_user_doc = DM.db[User.COLLECTION_NAME].find_one({"_id": ObjectId(user_id)})
        if existing_user_doc is None:
            raise ApplicationError("Invalid user!")
        if not password_context.verify(existing_password, existing_user_doc[User.PASSWORD_HASH]):
            raise ApplicationError("Existing password incorrect!")
        # now we update the document with new password
        new_password_hash = password_context.hash(new_password)
        DM.db[User.COLLECTION_NAME].update_one(filter={"_id": ObjectId(user_id)},
                                               update={"$set": {User.PASSWORD_HASH: new_password_hash,
                                                                User.LAST_MODIFIED_AT: datetime.utcnow()}})
