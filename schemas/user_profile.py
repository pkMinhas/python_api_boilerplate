from marshmallow import Schema, fields, validate


class UserProfileInputSchema(Schema):
    fullName = fields.Str(validate=validate.Length(max=20))
    city = fields.Str(validate=validate.Length(max=20))
    country = fields.Str(validate=validate.Length(max=20))
    gender = fields.Str(validate=validate.OneOf(["m","f","undecided"]))
    age = fields.Int(validate=validate.Range(min=16,max=80))
    occupation = fields.Str(validate=validate.Length(max=20))
    mobileNumber = fields.Int(validate=validate.Range(min=7000000000, max=9999999999))
