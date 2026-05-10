from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """全局配置类，自动从 ``.env`` 文件加载环境变量。

    提供数据库连接字符串等便捷属性，所有字段均可在环境变量中覆盖。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    APP_NAME: str = Field(default="Smart API Assistant")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)

    DEEPSEEK_API_KEY: str = Field(default="")
    DEEPSEEK_BASE_URL: str = Field(default="")
    DEEPSEEK_MODEL: str = Field(default="")
    DASHSCOPE_API_KEY: str = Field(default="")
    DASHSCOPE_BASE_URL: str = Field(default="")
    EMBEDDING_MODEL: str = Field(default="")
    
    CHROMA_HOST: str = Field(default="")
    CHROMA_PORT: int = Field(default="")
    CHROMA_CONNECTION: str = Field(default="api_docs")

    REDIS_HOST: str = Field(default="")
    REDIS_PORT: int = Field(default="")
    REDIS_DB: int = Field(default="")
    REDIS_SESSION_TTL: int = Field(default=1800)
    
    POSTGRES_HOST: str = Field(default="")
    POSTGRES_PORT: int = Field(default="")
    POSTGRES_USER: str = Field(default="")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="")

    @property
    def DATABASE_URL(self) -> str:
        """
        拼接 PostgreSQL 连接字符串。
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()