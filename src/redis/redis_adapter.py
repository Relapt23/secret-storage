class RedisAdapter:
    def update(self, secret_key: str, secret: str) -> str:
        pass

    def get(self, secret_key: str) -> str | None:
        pass

    def delete(self, secret_key: str) -> bool:
        pass
