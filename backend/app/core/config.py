from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/dropradar"
    
    # API Keys & External Services
    openpagerank_api_key: str = "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84"
    expireddomains_cookie: str = ""
    proxy_url: str = ""
    
    # App Config
    debug: bool = False
    app_name: str = "DropRadar"
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # 允许忽略额外的环境变量
    )


settings = Settings()