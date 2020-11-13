from flask_restful import Resource, request
from services.user import UserRegistrationService, UserLoginService
from application_error import ApplicationError
from schemas.user import (UserRegistrationInputSchema,
                          UserLoginInputSchema, ResetPasswordInputSchema,
                          ChangePasswordInputSchema, EmailAddressValidationSchema)

from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required
)


class RegisterUser(Resource):
    def post(self):
        """Creates an email based user:
        email, password
        :returns: {created}
        """
        data = UserRegistrationInputSchema().load(request.json)
        email_lowercase = data["email"].lower()
        UserRegistrationService.create_local_user(email=email_lowercase,
                                                  password=data["password"])
        return {"created": True}, 201


class ValidateEmailAddress(Resource):
    def post(self):
        """Validates the user's email address, given the verification token"""
        data = EmailAddressValidationSchema().load(request.json)
        email_lowercase = data["email"].lower()
        verification_token = data["verificationToken"]
        UserRegistrationService.validate_email_address_verification_token(email_lowercase, verification_token)


class ResendEmailAddressVerificationMail(Resource):
    @jwt_required
    def get(self):
        user_id = get_jwt_identity()
        UserRegistrationService.resend_email_address_verification_email(user_id)
        return {}, 200


class UserLogin(Resource):
    def post(self):
        """
        email
        password
        :return: {access_token, refresh_token}
        """
        data = UserLoginInputSchema().load(request.json)
        email_lowercase = data["email"].lower()
        token_response = UserLoginService.get_login_tokens(email_lowercase, data["password"])
        return token_response


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        """Authorization header should be Bearer <refreshToken>"""
        current_user = get_jwt_identity()
        return {
            # Mark the token as un-fresh since we used the refresh token to regenerate this
            "accessToken": create_access_token(identity=current_user, fresh=False),
            "userId": current_user
        }


class ResetPassword(Resource):
    def get(self, email):
        """Sends password reset email (containing reset token) to the registered address"""
        UserLoginService.send_password_reset_email(email=email.lower())
        return {}, 200

    def post(self, email):
        """Given a password reset token, allows to reset the password for the given user:
        token, newPassword"""
        data = ResetPasswordInputSchema().load(request.json)
        # userId is expected to be supplied as query param
        user_id = request.args.get("userId")
        if user_id is None:
            raise ApplicationError("userId must be a query parameter!")
        UserLoginService.reset_password_using_token(user_id=user_id,
                                                    token=data["token"],
                                                    new_password=data["newPassword"])
        return {}, 200


class ChangePassword(Resource):
    @jwt_required
    def post(self):
        """Given existing password, changes the logged-in user's password.
        existingPassword, newPassword
        """
        # userId is retrieved from jwt identity
        userId = get_jwt_identity()
        data = ChangePasswordInputSchema().load(request.json)
        UserLoginService.change_password(userId,
                                         existing_password=data["existingPassword"],
                                         new_password=data["newPassword"])
        return {}, 200
