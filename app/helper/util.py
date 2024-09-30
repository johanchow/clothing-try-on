import random
import string
import hashlib

def generate_uuid(length = 16):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def hash_string(s, len=10):
  h = hashlib.new('sha256')#sha256 can be replaced with diffrent algorithms
  h.update(s.encode()) #give a encoded string. Makes the String to the Hash
  return h.hexdigest()[:len]
