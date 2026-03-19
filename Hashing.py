import hashlib
import pandas as pd

INPUT_FILE = 'Users.csv'
OUTPUT_FILE = 'Users_hashed.csv'


def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()


df = pd.read_csv(INPUT_FILE)
df['email'] = df['email'].str.strip()
df['password'] = df['password'].apply(hash_password)

df.to_csv(OUTPUT_FILE, index=False)
