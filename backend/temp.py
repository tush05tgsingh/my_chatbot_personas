from jose import JWTError, jwt

secret = "mysecret"
data = {"sub": "123"}

token = jwt.encode(data, secret, algorithm="HS256")
decoded = jwt.decode(token, secret, algorithms=["HS256"])

print(decoded)