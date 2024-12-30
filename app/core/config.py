import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Grading Service"
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")
    REGION = str(os.getenv('REGION'))
    USER_POOL_ID = str(os.getenv('USER_POOL_ID'))

    # AWS Cognito configuration
    COGNITO_KEYS_URL = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'

settings = Settings()