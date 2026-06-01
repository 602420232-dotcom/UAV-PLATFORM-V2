"""
Production Secrets Generator
自动生成生产环境所需的全部密钥
"""

import secrets
import string
import json
from datetime import datetime

def generate_strong_password(length=32):
    """生成强密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret():
    """生成JWT密钥（至少32字符）"""
    return secrets.token_urlsafe(48)  # 48字节 = 64字符

def generate_api_key():
    """生成API密钥"""
    return f"uav_{secrets.token_urlsafe(32)}"

def main():
    print("=" * 60)
    print("Production Secrets Generator")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    secrets_dict = {
        "JWT_SECRET": generate_jwt_secret(),
        "DB_PASSWORD": generate_strong_password(32),
        "DB_ROOT_PASSWORD": generate_strong_password(48),
        "REDIS_PASSWORD": generate_strong_password(24),
        "WEATHER_API_KEY": generate_api_key(),
    }
    
    # 输出到终端
    print("Generated Secrets:")
    print("-" * 60)
    for key, value in secrets_dict.items():
        print(f"{key}:")
        print(f"  {value}\n")
    
    # 保存到.env.example文件
    env_file = ".env.production.example"
    with open(env_file, 'w') as f:
        f.write("# Production Environment Variables\n")
        f.write("# Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.write("# WARNING: Copy this file to .env.production and replace with real values\n\n")
        
        for key, value in secrets_dict.items():
            f.write(f"{key}={value}\n")
    
    print(f"Template saved to: {env_file}")
    print("\nWARNING: Please configure these secrets in production immediately!")
    print("=" * 60)

if __name__ == '__main__':
    main()
