# Defines the keys for all the mongo collections & other constants

class User:
    COLLECTION_NAME = "users"
    EMAIL = "email"
    PASSWORD_HASH = "passwordHash"
    CREATED_AT = "createdAt"
    LAST_MODIFIED_AT = "lastModifiedAt"
    EMAIL_VERIFIED = "isVerified"
    VERIFICATION_TOKEN = "verificationToken"


class PasswordResetTokens:
    COLLECTION_NAME = "passwordResetTokens"
    USERID = "userId"
    TOKEN = "token"
    VALID_TILL = "validTill"
    IS_CONSUMED = "isConsumed"


class ClaimsManagement:
    COLLECTION_NAME = "claimsManagement"
    USER_ID = "userId"
    IS_ADMIN = "isAdmin"
    IS_SUPER_ADMIN = "isSuperAdmin"
    LAST_MODIFIED_BY = "lastModifiedBy"
    LAST_MODIFIED_AT = "lastModifiedAt"


class UserProfile:
    COLLECTION_NAME = "userProfiles"
    USERID = "userId"
    FULL_NAME = "fullName"
    CITY = "city"
    COUNTRY = "country"
    GENDER = "gender"
    AGE = "age"
    OCCUPATION = "occupation"
    LAST_MODIFIED_AT = "lastModifiedAt"
    PICTURE_OBJECT_NAME = "pictureObjectName"
    MOBILE_NUMBER = "mobileNumber"


class JwtClaims:
    IS_EMAIL_ADDRESS_VERIFIED = "isEmailAddressVerified"
    IS_ADMIN = "isAdmin"
    IS_SUPER_ADMIN = "isSuperAdmin"
