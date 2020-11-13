from pymongo import MongoClient, database
from constants import ClaimsManagement, UserProfile

TEST_DATABASE_NAME = "test_mb_database"

class DatabaseManager:
    mongoClient: MongoClient = None
    db: database.Database = None

    @classmethod
    def initialize_database(cls, connection_uri):
        cls.mongoClient = MongoClient(connection_uri)
        # TODO: change the default db name (used in case the connection uri does not specify the database)
        cls.db = cls.mongoClient.get_default_database(default="marchingbytes")
        print(f"Connected to database: {cls.db.name}")
        # Create index(s) on all the required collections
        cls.__createIndexes__()

    @classmethod
    def initialize_testing_database(cls, connection_uri):
        print(f"Connecting to testing database: {TEST_DATABASE_NAME} at {connection_uri}")
        cls.mongoClient = MongoClient(connection_uri)
        cls.db = cls.mongoClient[TEST_DATABASE_NAME]
        cls.__createIndexes__()

    @classmethod
    def delete_testing_database(cls):
        print(f"Deleting database {TEST_DATABASE_NAME}")
        cls.mongoClient.drop_database(TEST_DATABASE_NAME)

    @classmethod
    def __createIndexes__(cls):
        """Creates the required indexes on the collections"""
        # add a unique userId index to claims management collection
        cls.db[ClaimsManagement.COLLECTION_NAME].create_index(ClaimsManagement.USER_ID, unique=True)
        # add a unique userId index to user profile
        cls.db[UserProfile.COLLECTION_NAME].create_index(UserProfile.USERID, unique=True)
