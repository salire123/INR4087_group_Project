import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from .db import redis_connection
from .env import Config

class JWTManager:
    """JWT 管理类，用于生成和解码 JWT Token"""
    
    # 类属性，所有实例共享同一个 blacklist
    _blacklist = []

    def __init__(self, secret: str, algorithm: str = "HS256"):
        """
        初始化 JWTManager
        
        Args:
            secret (str): 用于加密和解密的密钥
            algorithm (str): 加密算法，默认为 HS256
        """
        self.secret = secret
        self.algorithm = algorithm
        self._blacklist = "jwt_blacklist"

    def generate_token(self, payload: Dict[str, Any], expiration: int) -> str:
        """
        Generate JWT Token
        
        Args:
            payload (Dict[str, Any]): Data to encode (e.g., user information)
            expiration (int): Token expiration time in seconds
        
        Returns:
            str: Generated JWT token
        """
        token_payload = payload.copy()
        token_payload["exp"] = datetime.utcnow() + timedelta(seconds=expiration)
        
        # PyJWT encode returns bytes in newer versions (3.x), so we convert to string
        token = jwt.encode(token_payload, self.secret, algorithm=self.algorithm)
        
        # If jwt.encode returns bytes, decode to string
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token

    def check_token(self, token: str) -> Dict[str, Any]:
            """
            检查 JWT Token 是否有效
            
            Args:
                token (str): 要检查的 Token
                redis_host (str): Redis 主机地址
                redis_port (int): Redis 端口
                redis_db (int): Redis 数据库编号
            
            Returns:
                Dict[str, Any]: 解码后的 Token 数据
            """
            with redis_connection(0) as redis_client:
                try:
                    if redis_client.sismember(self._blacklist, token):
                        return None
                    payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
                    return payload
                except Exception as e:
                    return None
    
    def blacklist_token(self, token: str) -> None:
        """
        将 Token 加入黑名单
        
        Args:
            token (str): 要加入黑名单的 Token
        """
        with redis_connection(0) as redis:
            redis.sadd(self._blacklist, token)
        return None
    
    def remove_ExpiredToken(self) -> None:
        """
        清除过期 Token
        """
        with redis_connection(0) as redis_client:
                    blacklisted_tokens = redis_client.smembers(self._blacklist)
                    for token in blacklisted_tokens:
                        payload = self.check_token(token, 0)
                        if payload is None:
                            redis_client.srem(self._blacklist, token)
        return None
