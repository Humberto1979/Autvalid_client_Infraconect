# F3 Config: toda configuracao variavel vem de variaveis de ambiente.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "infraconect"
    db_user: str = "app"
    db_password: str = "changeme"

    app_port: int = 5000

    # Pool de conexoes (psycopg_pool).
    pool_min: int = 1
    pool_max: int = 5

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()