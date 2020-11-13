from marshmallow import Schema, fields, validate

#regex allowing lowercase letters, numbers and length b/w 3-15
usernameRegex = "^[a-z0-9_]{3,15}$"


class UserRegistrationInputSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=4))


class UserLoginInputSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class ResetPasswordInputSchema(Schema):
    token = fields.Str(required=True)
    newPassword = fields.Str(required=True, validate=validate.Length(min=4))


class ChangePasswordInputSchema(Schema):
    existingPassword = fields.Str(required=True)
    newPassword = fields.Str(required=True, validate=validate.Length(min=4))

class EmailAddressValidationSchema(Schema):
    email = fields.Email(required=True)
    verificationToken = fields.Str(required=True)