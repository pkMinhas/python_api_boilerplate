#This file is used by pytest to configure fixtures for all tests
import pytest
from app import create_app
from database_manager import DatabaseManager


# session scoped client, to ensure that user registeration tests create the user required by other tests
@pytest.fixture(scope="session")
def test_client():
    # Create app in test mode
    flask_app = create_app(test_mode=True)

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    # All code after yield is run when the fixture is going out of scope
    # (https://docs.pytest.org/en/latest/fixture.html)
    ctx.pop()
    # delete test database
    DatabaseManager.delete_testing_database()
