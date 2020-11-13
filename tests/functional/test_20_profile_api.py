# Basic assumption: this test will be run after user tests. That will ensure that the account is registered
from tests.functional.common_functions import loginUser, validPassword, emailRegistered

def __validProfileData__():
    return {
        "fullName": "Test User 1",
        "city": "Mohali",
        "country": "India",
        "gender": "m",
        "age": 34,
        "occupation": "engineer",
        "mobileNumber": 9988776655
    }


def __invalidProfileData__():
    invalidProfile = __validProfileData__()
    invalidProfile["age"] = 134
    return invalidProfile


def test_getProfile(test_client):
    url = "/user/profile"
    # should not work without jwt
    res = test_client.get(url)
    assert res.status_code == 401
    tokenDict = loginUser(test_client, emailRegistered, validPassword)
    # At this time, the profile would not have been created
    res = test_client.get(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 404
    assert res.get_json() is None


def test_postProfile(test_client):
    url = "/user/profile"
    res = test_client.post(url)
    assert res.status_code == 401
    # try with jwt
    tokenDict = loginUser(test_client, emailRegistered, validPassword)

    # try passing invalid profile
    res = test_client.post(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                           json=__invalidProfileData__())
    assert res.status_code == 400
    assert isinstance(res.get_json()["message"], str)
    assert len(res.get_json()["message"]) > 0

    # valid profile will be not be created even if name is not provided
    res = test_client.post(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                           json={})
    assert res.status_code == 400
    assert res.get_json()["message"] == "Please provide your name!"
    # get the profile, it should not have been created
    get_res = test_client.get(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert get_res.status_code == 404
    assert get_res.get_json() is None


def test_putProfile(test_client):
    url = "/user/profile"
    res = test_client.put(url)
    assert res.status_code == 401
    # try with jwt
    tokenDict = loginUser(test_client, emailRegistered, validPassword)
    # try passing invalid profile
    res = test_client.put(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                          json=__invalidProfileData__())
    assert res.status_code == 400
    assert isinstance(res.get_json()["message"], str)
    assert len(res.get_json()["message"]) > 0

    # update with valid profile data
    res = test_client.put(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                          json=__validProfileData__())
    assert res.status_code == 201
    assert res.get_json() == {}

    # get the profile data and compare to data passed
    get_res = test_client.get(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert get_res.status_code == 200
    assert get_res.get_json()["fullName"] == __validProfileData__()["fullName"]
    assert get_res.get_json()["lastModifiedAt"] is not None

def test_putPostProfileDictWithUsername(test_client):
    """Check what happens if we pass username in the json -> should FAIL"""
    url = "/user/profile"
    tokenDict = loginUser(test_client, emailRegistered, validPassword)
    json = __validProfileData__()
    json["username"] = "some other user i want to change"
    # PUT
    res = test_client.put(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                          json=json)
    assert res.status_code == 400
    assert res.get_json()["message"] == "Username - Unknown field."

    # POST
    res = test_client.post(url, headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'},
                          json=json)
    assert res.status_code == 400
    assert res.get_json()["message"] == "Username - Unknown field."


def test_postProfilePicture(test_client):
    url = "/user/profile/pictureUpload"
    data = {}
    import io
    # should fail without auth
    res = test_client.post(url, data=data, content_type='multipart/form-data')
    assert res.status_code == 401
    # should fail after auth because of invalid input
    tokenDict = loginUser(test_client, emailRegistered, validPassword)
    res = test_client.post(url, data=data, content_type='multipart/form-data',
                           headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 400
    assert res.get_json()["message"] == "Key 'file' not a part of request!"
    # invalid file data, should fail
    data['file'] = (io.BytesIO(b"abcdef"), 'test.jpg')
    res = test_client.post(url, data=data, content_type='multipart/form-data',
                           headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    assert res.status_code == 400
    assert res.get_json()["message"] == "Invalid image file!"

    # upload size greater than 2mb
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        size_bytes = 3 * 1024 * 1024
        import os
        file_path = os.path.join(tmpdirname, "random")
        randomfile = open(file_path, "wb")
        randomfile.seek(size_bytes - 1)
        randomfile.write(b"\0")
        randomfile.close()
        data['file'] = (io.open(file_path,"rb"), 'test.jpg')
        res = test_client.post(url, data=data, content_type='multipart/form-data',
                               headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
        # should be REQUEST ENTITY TOO LARGE (413)
        assert res.status_code == 413

    # check with valid input png
    iFile = io.open("/Users/preetminhas/work/dw_server/tests/functional/test-image.png", "rb")
    data['file'] = (iFile, 'test.png')
    res = test_client.post(url, data=data, content_type='multipart/form-data',
                           headers={"Authorization": f'Bearer {tokenDict["accessToken"]}'})
    iFile.close()
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["filename"] is not None
    assert res_json["url"] is not None


def test_getPublicProfile(test_client):
    # this api can be called by non-logged in clients as well
    # invalid user id. Blank response object
    otherUserId = "abc"
    url = f"/profileById/{otherUserId}"
    res = test_client.get(url)
    print(res.get_json())
    assert res.status_code == 404
    assert res.get_json()["message"] == "User profile unavailable"

    # get valid user id from the login token
    tokenDict = loginUser(test_client, emailRegistered, validPassword)
    accessToken = tokenDict["accessToken"]
    payload = accessToken.split(".")[1]
    import base64
    padding = 4 - (len(payload) % 4)
    payload = payload + ("="*padding)
    payload = base64.urlsafe_b64decode(payload).decode('utf-8')
    import json
    identity = json.loads(payload)["identity"]
    print(identity)

    # use this identity to hit the profile endpoint
    url = f"/profileById/{identity}"
    res = test_client.get(url)
    assert res.status_code == 200
    assert res.get_json() is not None
    assert res.get_json()["fullName"] == __validProfileData__()["fullName"]
    assert "age" not in res.get_json()
    assert "occupation" not in res.get_json()

