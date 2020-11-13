from marshmallow import Schema, fields, validate

class UserClaimsUpdateSchema(Schema):
    userId = fields.Str(required=True)
    isAdmin = fields.Bool(required=True)
    isSuperAdmin = fields.Bool(required=True)
