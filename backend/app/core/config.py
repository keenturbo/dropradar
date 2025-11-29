from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/dropradar"
    
    # API Keys & External Services
    openpagerank_api_key: str = "w00wkkkwo4c4sws4swggkswk8oksggsccck0go84"
    expireddomains_cookie: str = ""
    proxy_url: str = ""
    
    # AI Generation (Optional)
    anthropic_api_key: str = ""  # Claude API Key
    google_api_key: str = ""  # Gemini API Key
    ai_provider: str = "claude"  # claude 或 gemini
    ai_model_claude: str = "claude-3-5-sonnet-20241022"
    ai_model_gemini: str = "gemini-2.0-flash-exp"
    
    # App Config
    debug: bool = False
    app_name: str = "DropRadar"
    
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # 允许忽略额外的环境变量
    )


settings = Settings()