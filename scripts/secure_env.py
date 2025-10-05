#!/usr/bin/env python3
"""
Automated API Key Protection System
Encrypts/decrypts sensitive environment files for the Cardiology AI project
"""

import os
import sys
import base64
import json
import argparse
import re
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

class SecureEnvManager:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root or os.getcwd())
        self.encrypted_dir = self.project_root / ".encrypted"
        self.key_file = self.project_root / ".encryption_key"
        self.sensitive_files = [".env", ".env.local", ".env.production", ".env.staging"]
        
        # Create encrypted directory
        self.encrypted_dir.mkdir(exist_ok=True)
    
    def generate_key(self, password=None):
        """Generate encryption key from password"""
        if not password:
            password = getpass.getpass("Enter encryption password: ")
        
        password_bytes = password.encode()
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        
        # Store salt and key info
        key_data = {
            "salt": base64.b64encode(salt).decode(),
            "key": key.decode()
        }
        
        with open(self.key_file, 'w') as f:
            json.dump(key_data, f)
        
        print(f"🔑 Encryption key generated and saved to {self.key_file}")
        return key
    
    def load_key(self, password=None):
        """Load encryption key"""
        if not self.key_file.exists():
            return self.generate_key(password)
        
        try:
            with open(self.key_file, 'r') as f:
                key_data = json.load(f)
            
            if not password:
                password = getpass.getpass("Enter encryption password: ")
            
            salt = base64.b64decode(key_data["salt"])
            password_bytes = password.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            return key
            
        except Exception as e:
            print(f"❌ Failed to load encryption key: {e}")
            return None
    
    def encrypt_file(self, file_path, password=None):
        """Encrypt a sensitive file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"⚠️  File {file_path} does not exist")
            return False
        
        key = self.load_key(password)
        if not key:
            return False
        
        fernet = Fernet(key)
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt data
        encrypted_data = fernet.encrypt(file_data)
        
        # Save encrypted file
        encrypted_file = self.encrypted_dir / f"{file_path.name}.enc"
        with open(encrypted_file, 'wb') as f:
            f.write(encrypted_data)
        
        print(f"🔐 Encrypted {file_path} → {encrypted_file}")
        return True
    
    def decrypt_file(self, encrypted_file_path, output_path=None, password=None):
        """Decrypt a file"""
        encrypted_file_path = Path(encrypted_file_path)
        
        if not encrypted_file_path.exists():
            print(f"❌ Encrypted file {encrypted_file_path} does not exist")
            return False
        
        key = self.load_key(password)
        if not key:
            return False
        
        fernet = Fernet(key)
        
        # Read encrypted data
        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            # Decrypt data
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Determine output path
            if not output_path:
                output_path = encrypted_file_path.name.replace('.enc', '')
            
            output_path = Path(output_path)
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"🔓 Decrypted {encrypted_file_path} → {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to decrypt {encrypted_file_path}: {e}")
            return False
    
    def encrypt_all_sensitive(self, password=None):
        """Encrypt all sensitive files"""
        print("🔐 Encrypting all sensitive files...")
        
        encrypted_count = 0
        for file_name in self.sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                if self.encrypt_file(file_path, password):
                    encrypted_count += 1
        
        print(f"✅ Encrypted {encrypted_count} files")
        return encrypted_count > 0
    
    def decrypt_all_sensitive(self, password=None):
        """Decrypt all sensitive files"""
        print("🔓 Decrypting all sensitive files...")
        
        decrypted_count = 0
        for encrypted_file in self.encrypted_dir.glob("*.enc"):
            original_name = encrypted_file.name.replace('.enc', '')
            output_path = self.project_root / original_name
            
            if self.decrypt_file(encrypted_file, output_path, password):
                decrypted_count += 1
        
        print(f"✅ Decrypted {decrypted_count} files")
        return decrypted_count > 0
    
    def scan_for_api_keys(self, directory=None):
        """Scan for API keys in files"""
        if not directory:
            directory = self.project_root
        
        directory = Path(directory)
        
        # API key patterns
        patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI
            r'OPENAI_API_KEY=sk-',
            r'API_KEY=.*[a-zA-Z0-9]{20,}',
            r'SECRET_KEY=.*[a-zA-Z0-9]{20,}',
            r'ACCESS_TOKEN=.*[a-zA-Z0-9]{20,}',
        ]
        
        found_keys = []
        
        # Files to exclude from scanning
        exclude_patterns = [
            '*.enc',  # Encrypted files
            '.git/*',  # Git directory
            '__pycache__/*',  # Python cache
            '*.pyc',  # Compiled Python
            'node_modules/*',  # Node modules
        ]
        
        # Scan all text files
        for file_path in directory.rglob("*"):
            if (file_path.is_file() and 
                not any(file_path.match(pattern) for pattern in exclude_patterns) and
                not file_path.name.startswith('.')):
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            found_keys.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'pattern': pattern,
                                'matches': matches
                            })
                            
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        if found_keys:
            print("⚠️  API keys found in the following files:")
            for item in found_keys:
                print(f"   📄 {item['file']}")
                print(f"      Pattern: {item['pattern']}")
                print(f"      Matches: {len(item['matches'])} key(s) found")
            print("\n💡 Recommendation: Move these keys to .env files and encrypt them")
        else:
            print("✅ No API keys found in repository")
        
        return found_keys

def main():
    parser = argparse.ArgumentParser(description="Secure Environment Manager for Cardiology AI")
    parser.add_argument("action", 
                       choices=["encrypt", "decrypt", "scan", "encrypt-all", "decrypt-all"],
                       help="Action to perform")
    parser.add_argument("--file", help="Specific file to encrypt/decrypt")
    parser.add_argument("--password", help="Encryption password (will prompt if not provided)")
    parser.add_argument("--output", help="Output file path for decryption")
    
    args = parser.parse_args()
    
    manager = SecureEnvManager()
    
    if args.action == "encrypt":
        if not args.file:
            print("❌ --file required for encrypt action")
            sys.exit(1)
        manager.encrypt_file(args.file, args.password)
    
    elif args.action == "decrypt":
        if not args.file:
            print("❌ --file required for decrypt action")
            sys.exit(1)
        manager.decrypt_file(args.file, args.output, args.password)
    
    elif args.action == "encrypt-all":
        manager.encrypt_all_sensitive(args.password)
    
    elif args.action == "decrypt-all":
        manager.decrypt_all_sensitive(args.password)
    
    elif args.action == "scan":
        found_keys = manager.scan_for_api_keys()
        if found_keys:
            print(f"\n🔍 Found {len(found_keys)} file(s) with potential API keys")
            sys.exit(1)  # Exit with error code if keys found
        else:
            print("🔒 Repository is secure - no API keys detected")

if __name__ == "__main__":
    main()