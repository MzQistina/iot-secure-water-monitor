from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import json, base64
import hashlib

def encrypt_data(data_dict, public_key_path):
    session_key = get_random_bytes(16)
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(json.dumps(data_dict).encode())

    recipient_key = RSA.import_key(open(public_key_path).read())
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    encrypted_session_key = cipher_rsa.encrypt(session_key)

    return {
        "session_key": base64.b64encode(encrypted_session_key).decode(),
        "nonce": base64.b64encode(cipher_aes.nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "tag": base64.b64encode(tag).decode()
    }

def decrypt_data(encrypted_payload, private_key_path):
    encrypted_session_key = base64.b64decode(encrypted_payload['session_key'])
    nonce = base64.b64decode(encrypted_payload['nonce'])
    ciphertext = base64.b64decode(encrypted_payload['ciphertext'])
    tag = base64.b64decode(encrypted_payload['tag'])

    private_key = RSA.import_key(open(private_key_path).read())
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(encrypted_session_key)

    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    decrypted_data = cipher_aes.decrypt_and_verify(ciphertext, tag)

    return json.loads(decrypted_data.decode())

def pad(s):
    return s + (16 - len(s) % 16) * chr(16 - len(s) % 16)

def unpad(s):
    return s[:-ord(s[len(s)-1:])]

def hash_data(data):
    return hashlib.sha256(str(data).encode()).hexdigest()

def aes_encrypt(data_dict, key):
    data = pad(json.dumps(data_dict))
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(data.encode('utf-8'))
    return json.dumps({
        'iv': base64.b64encode(cipher.iv).decode(),
        'ciphertext': base64.b64encode(ct_bytes).decode()
    })

def aes_decrypt(enc_json, key):
    enc = json.loads(enc_json)
    iv = base64.b64decode(enc['iv'])
    ct = base64.b64decode(enc['ciphertext'])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct).decode('utf-8'))
    return json.loads(pt)
