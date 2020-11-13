from tests.functional.common_functions import loginUser, validPassword, emailRegistered
from flask_jwt_extended import decode_token

validEmail = emailRegistered
invalidEmail = "abc"


def test_registerInvalidUser(test_client):
    url = "/register"
    # get is not allowed
    response = test_client.get(url)
    assert response.status_code == 405
    # try post without data
    response = test_client.post(url)
    assert response.status_code == 400
    # try registering without one of email, password
    json = {"email": validEmail}
    response = test_client.post(url, json=json)
    assert response.status_code == 400
    json = { "password": "xx", "email": invalidEmail}
    response = test_client.post(url, json=json)
    assert response.status_code == 400
    # try registering valid user, but with password less than 4 characters
    json = {"password": "xx", "email": validEmail}
    response = test_client.post(url, json=json)
    assert response.status_code == 400


def test_registerValidUser(test_client):
    json = {"password": validPassword, "email": validEmail}
    response = test_client.post("/register", json=json)
    print(response.get_json())
    assert response.status_code == 201


def test_invalidLogin(test_client):
    res = test_client.get("/login")
    assert res.status_code == 405
    res = test_client.post("/login")
    assert res.status_code == 400
    assert res.get_json()["message"] is not None
    # Invalid username
    res = test_client.post("/login", json={"email": "anc", "password": "testing"})
    assert res.status_code == 403
    assert res.get_json()["message"] == "Invalid credentials!"
    # Invalid password
    res = test_client.post("/login", json={"email": validEmail, "password": "testing"})
    assert res.status_code == 403
    assert res.get_json()["message"] == "Invalid credentials!"
    # POST without params
    res = test_client.post("/login")
    assert res.status_code == 400


def test_validLogin(test_client):
    res = test_client.post("/login", json={"email": validEmail, "password": validPassword})
    assert res.status_code == 200
    json = res.get_json()
    assert isinstance(json["accessToken"], str) == True
    assert isinstance(json["refreshToken"], str) == True
    assert len(json["accessToken"]) > 0
    assert len(json["refreshToken"]) > 0
    assert json["refreshToken"] != json["accessToken"]
    #verify that the jwt does not have isAdmin set to true for a normal user
    jwtPayload = decode_token(json["accessToken"])
    assert jwtPayload["user_claims"]["isAdmin"] == False
    assert isinstance(jwtPayload["identity"],str)


def test_get_resetPassword(test_client):
    # valid but unregistered user will result in 200
    res = test_client.get("/resetPassword/smiley@test.com")
    assert res.status_code == 200
    # /resetPassword without username is 404
    res = test_client.get("/resetPassword")
    assert res.status_code == 404
    # registered email will result in 200
    res = test_client.get(f"/resetPassword/{validEmail}")
    assert res.status_code == 200
    # response must be an empty dict. This call should send an email
    assert res.get_json() == {}


def test_post_resetPassword(test_client):
    # POST without json
    res = test_client.post(f"/resetPassword/{validEmail}")
    assert res.status_code == 400
    # with invalid json (new password not supplied)
    json = {"token": "xyz"}
    res = test_client.post(f"/resetPassword/{validEmail}", json=json)
    assert res.status_code == 400
    # new password less than 4
    json = {"token": "xyz", "newPassword": "123"}
    res = test_client.post(f"/resetPassword/{validEmail}", json=json)
    assert res.status_code == 400
    print(res.get_json()["message"])
    assert res.get_json()["message"] == "Newpassword - Shorter than minimum length 4."
    # invalid token value
    json = {"token": "xyz", "newPassword": "1234"}
    res = test_client.post(f"/resetPassword/{validEmail}?userId=abcd1234", json=json)
    assert res.status_code == 400
    assert res.get_json()["message"] == "Invalid password reset token. Please try again!"
    # POST without query param
    res = test_client.post(f"/resetPassword/{validEmail}", json=json)
    assert res.status_code == 400
    assert res.get_json()["message"] == "userId must be a query parameter!"
    # TODO: test case with valid token & userId


def test_tokenRefresh(test_client):
    url = "/user/refreshToken"
    res = test_client.get(url)
    assert res.status_code == 405
    # hit the endpoint without refresh token in header
    res = test_client.post(url)
    assert res.status_code == 401
    #get the tokens
    tokenDict = loginUser(test_client, validEmail, validPassword)
    # try refresh with access token in header
    res = test_client.post(url, headers={"Authorization":"Bearer " + tokenDict["accessToken"]})
    assert res.status_code == 422
    # try the refresh token in header
    res = test_client.post(url, headers={"Authorization": "Bearer " + tokenDict["refreshToken"]})
    assert res.status_code == 200
    newAccessToken = res.get_json()["accessToken"]
    assert isinstance(newAccessToken, str)
    assert len(newAccessToken) > 0
    # new access token cannot be equal to older one
    assert newAccessToken != tokenDict["accessToken"]
    assert newAccessToken != tokenDict["refreshToken"]
    # validate that the username returned by api is the username used in the login call
    assert res.get_json()["userId"] == decode_token(newAccessToken)["identity"]


def test_changePassword(test_client):
    url = "/user/changePassword"
    # GET not available
    res = test_client.get(url)
    assert res.status_code == 405
    # this endpoint cannot be accessed without valid JWT
    res = test_client.post(url)
    assert res.status_code == 401
    #login and try again
    tokenDict = loginUser(test_client, validEmail, validPassword)
    # Using refresh token will fail. API expects accessToken
    res = test_client.post(url, headers = {"Authorization" : f'Bearer {tokenDict["refreshToken"]}'})
    assert res.status_code == 422
    # Use accessToken but don't provide json data
    res = test_client.post(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 400
    # provide incorrect data
    # newPassword does not meet validation criteria
    json = {"existingPassword": "123", "newPassword": "123"}
    res = test_client.post(url, json=json, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 400
    assert res.get_json()["message"].startswith("Newpassword")
    # pass incorrect existing password
    json = {"existingPassword": "123", "newPassword": "1234567"}
    res = test_client.post(url, json=json, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 400
    assert res.get_json()["message"] == "Existing password incorrect!"
    # pass correct passwords
    # pass incorrect existing password
    newPassword = "12345678"
    json = {"existingPassword": validPassword, "newPassword": newPassword}
    res = test_client.post(url, json=json, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 200
    assert res.get_json() == {}
    # login with old password should fail
    res = test_client.post("/login",json={"email":validEmail, "password":validPassword})
    assert res.status_code == 403
    # login with new password should succeed
    res = test_client.post("/login", json={"email": validEmail, "password": newPassword})
    assert res.status_code == 200
    # Change the password back to original password so that subsequent test cases are not affected
    json = {"existingPassword": newPassword, "newPassword": validPassword}
    res = test_client.post(url, json=json, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 200
    assert res.get_json() == {}
    # login with old password should succeed
    res = test_client.post("/login", json={"email": validEmail, "password": validPassword})
    assert res.status_code == 200
    # login with new password should fail
    res = test_client.post("/login", json={"email": validEmail, "password": newPassword})
    assert res.status_code == 403

