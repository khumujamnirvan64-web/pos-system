from pydantic_settings import SettingsConfigDict, BaseSettings

class Setting(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SIGN_UP_KEY: str
    SIGN_UP_ALGORITHM: str
    SIGNUP_EXP_MINUTE: int

    ACCESS_TOKEN_KEY: str
    ACCESS_TOKEN_ALGORITHM: str
    ACCESS_EXP_MINUTE: int

    FIRST_USER_NAME: str
    FIRST_USER_PASSWORD: str
    FIRST_USER_EMAIL: str

    GMAIL: str
    APP_PASSWORD: str

    PASSWORD_SECRET_KEY: str
    PASSWORD_ALGORITHM: str
    PASSWORD_EXP_MINUTE: int

    REFRESH_TOKEN_EXP_DAY: int

    @property
    def DB_URL(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env"
    )

settings = Setting() # type: ignore