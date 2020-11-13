validPassword: str = "1234"
emailRegistered = "smiley@xyz.com"

def loginUser(test_client, email, password):
    response = test_client.post("/login", json={"email": email,
                                                "password": password})
    return response.get_json()