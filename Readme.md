# Boilerplate project for creating new API servers using Python3 & Flask
- Uses [Pipenv](https://pypi.org/project/pipenv/) for managing dependencies
- Built on top of [Flask](https://flask.palletsprojects.com/en/1.1.x/), using a couple of other open-source libraries (see Pipfile for complete list)
- Uses MongoDB for database operations related to user management. Plugging in other database systems (MySQL, SQL Server etc.) for business logic should be straightforward.
- Provides services for sending mails via SendGrid
- Provides services for uploading files to AWS cloud buckets
- Uses JWT for tokens
- Provides out of the box APIs for user management (including roles)
- Sets up common decorators for role/claim based access
- Comes with Pytest test suite (Work in progress. *Apologies!*) for the API layer. I recommend that you write test cases for your project and preferably, cover all the modules. Remember that in the long run, unit tests save time, money & your precious mental sanity.

## DB Design
The following collections are a part of this boilerplate:
- users  -- contains the basic information for the registered user. Name etc. are stored separately in user profile.
- passwordResetTokens
- userProfiles
- claimsManagement 

The database design is quite straightforward. All the collection related constants (and a couple of other constants) are defined in `constants.py`. That should be the first stop in case you need to understand what's going on in the DB layer.

## Usage
### Setup environment variables
- JWT_SECRET_KEY
- MONGODB_URI
- SENDGRID_API_KEY

The next set of env variables is for accessing AWS services but configured via the Heroku CloudCube add-on
- CLOUDCUBE_ACCESS_KEY_ID
- CLOUDCUBE_SECRET_ACCESS_KEY
- CLOUDCUBE_URL

### Setup CORS
- File `app.py`, method `create_app()`, setup the correct set of CORS options

### Setup max file upload size
- File `app.py`, method `create_app()`, setup the required value for `app.config["MAX_CONTENT_LENGTH"]`

## Running the test suite
Invoking `pytest` on the command line will run the test cases in order. The test suite expects `setup_env.py` to be a part of `tests->functional` package. This file can be used to set the env variables before starting the tests. Care must be taken to ensure that you do not check-in any secret keys to your source control repository.

You'll need to run a MongoDB instance to execute the test cases locally.

## Deployment options
While this project can be deployed just like any standard python application, you might find certain files such as `Procfile` and `runtime.txt` which are specific to Heroku based deployments

## Author
Preet Kamal Singh Minhas, [MarchingBytes Technology Solutions (OPC) Pvt. Ltd.](https://marchingbytes.com)

## License
MIT. For details, refer to LICENSE file.

## Liked this project?
If this project helped you in any way, star the repository on github. 

