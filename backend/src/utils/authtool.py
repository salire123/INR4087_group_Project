import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

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
        
        Returns:
            Dict[str, Any]: 解码后的 Token 数据
        """
        try:
            if token in JWTManager._blacklist:
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
        if token not in JWTManager._blacklist:
            JWTManager._blacklist.append(token)
        return None
    
    def remove_ExpiredToken(self) -> None:
        """
        清除过期 Token
        """
        for token in JWTManager._blacklist[:]:  # 使用副本遍历，避免修改时出错
            payload = self.check_token(token)
            if payload is None:
                JWTManager._blacklist.remove(token)
        return None
