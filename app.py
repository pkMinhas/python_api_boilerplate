from flask import Flask
from flask_restful import Api
from resources.user import (RegisterUser, UserLogin, TokenRefresh,
                            ResetPassword, ChangePassword, ValidateEmailAddress, ResendEmailAddressVerificationMail)
from resources.claims_management import ClaimsList, UpdateClaims
from resources.user_profile import UserProfile, PublicUserProfile
from resources.upload import ProfilePictureUpload

from marshmallow import ValidationError
from application_error import ApplicationError
from services.claims import ClaimsManagementService
from services.user import UserRegistrationService

import os
from flask_jwt_extended import JWTManager
from database_manager import DatabaseManager
from services.aws_s3 import AwsS3
from flask_cors import CORS
from constants import JwtClaims


def create_app(test_mode=False):
    """Uses factory pattern to create app objects"""
    app = Flask(__name__)

    # Configure CORS
    # TODO: setup the correct origins
    # instructions at https://flask-cors.corydolphin.com/en/latest/api.html
    CORS(app, origins=["*.marchingbytes.com"])

    # Set flask config variables
    # Allow app to use custom error handlers when in production mode
    app.config["PROPAGATE_EXCEPTIONS"] = True
    # setup the flask-jwt-extended extension
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

    # setup maximum upload file size allowed
    # 2MB
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    # test mode config overrides
    if test_mode:
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "1234567890"
        print("Starting server in TESTING mode!")

    # configure database
    configure_database(test_mode)
    # configure jwt
    configure_jwt(app)
    # configure error handlers
    configure_error_handlers(app)
    # configure aws s3 client
    configure_AWS_s3(test_mode)
    # Configure api
    configure_api(app)
    return app


def configure_AWS_s3(test_mode=False):
    # This method is written assuming CloudCube services on Heroku.
    # Env variables might differ in case other methods are used to access S3 buckets
    # NOTE: env variable reflect the naming used by CloudCube
    aws_access_key_id = os.environ.get("CLOUDCUBE_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("CLOUDCUBE_SECRET_ACCESS_KEY")
    base_url = os.environ.get("CLOUDCUBE_URL")
    # bucket name is derived from cloudcube url. Refer: https://devcenter.heroku.com/articles/cloudcube#s3-api-and-bucket-name
    # ignore https:// & then split
    bucket_name = base_url[8:]
    bucket_name = bucket_name.split(".")[0]
    # cube name is the last part used to uniquely identify the storage space within a bucket
    cube_name = base_url[8:]
    all_url_parts = cube_name.split("/")
    cube_name = all_url_parts[len(all_url_parts) - 1]
    AwsS3.configure_client(aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key,
                           bucket_name=bucket_name,
                           base_url=base_url,
                           cube_name=cube_name)


def configure_database(test_mode=False):
    connection_uri = os.environ.get("MONGODB_URI")
    if test_mode:
        DatabaseManager.initialize_testing_database(connection_uri)
    else:
        DatabaseManager.initialize_database(connection_uri)


def configure_jwt(app):
    """Uses the Flask-JWT-Extended extension to setup jwt tokens for this application"""
    jwt = JWTManager(app)

    # Using the user_claims_loader, we can specify a method that will be
    # called when creating access tokens, and add these claims to the said
    # token. This method is passed the identity of who the token is being
    # created for, and must return data that is json serializable
    @jwt.user_claims_loader
    def add_claims_to_access_token(user_id):
        """This is the method where you add custom claims to tokens, based on the userId"""
        claims_dict = ClaimsManagementService.get_user_claims(user_id)
        is_admin = claims_dict["isAdmin"]
        is_super_admin = claims_dict["isSuperAdmin"]
        is_email_address_verified = UserRegistrationService.is_email_address_verified(user_id)
        # Note: Add other claims as required
        return {
            JwtClaims.IS_EMAIL_ADDRESS_VERIFIED: is_email_address_verified,
            JwtClaims.IS_ADMIN: is_admin,
            JwtClaims.IS_SUPER_ADMIN: is_super_admin
        }


def configure_api(app):
    api = Api(app)
    # user registration and login end points
    api.add_resource(RegisterUser, "/register")
    api.add_resource(UserLogin, "/login")
    api.add_resource(ValidateEmailAddress, "/validateEmailAddress")

    # used when user forgets password
    api.add_resource(ResetPassword, "/resetPassword/<string:email>")
    # token refresh end point
    api.add_resource(TokenRefresh, "/user/refreshToken")

    api.add_resource(ResendEmailAddressVerificationMail, "/user/resendEmailVerificationMail")

    # used when changing password when logged-in
    api.add_resource(ChangePassword, "/user/changePassword")

    # Claim management (super-admin endpoints)
    api.add_resource(ClaimsList, "/management/allClaims")
    api.add_resource(UpdateClaims, "/management/updateClaims")

    # User profile
    api.add_resource(UserProfile, "/user/profile")
    api.add_resource(ProfilePictureUpload, "/user/profile/pictureUpload")
    api.add_resource(PublicUserProfile, "/profileById/<string:other_user_id>")


def configure_error_handlers(app):
    # Error handler for marshmallow validation exceptions
    @app.errorhandler(ValidationError)
    def handle_validation_exception(e):
        """Return JSON for validation errors"""
        # Validation errors are in form key:[messages]
        # we just turn this into a simple string of format: key - message1; key - message2...
        message = ""
        for key in e.messages.keys():
            value = e.messages[key]
            message_separator = "; "
            # if value is list, append all
            if isinstance(value, list):
                for entry in value:
                    message += key.capitalize() + " - " + entry + message_separator
            elif isinstance(value, str):
                message += key.capitalize() + " - " + value + message_separator
        # Remove last "; " from message
        message = message[: len(message) - len(message_separator)]
        return {"message": message}, 400

    # Error handler for application errors
    @app.errorhandler(ApplicationError)
    def handle_application_error(e):
        """Return JSON for app errors"""
        return e.to_dict(), e.status_code


# This block is the one responsible for executing the app
if __name__ == '__main__':
    app = create_app()
    app.run()
