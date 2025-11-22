# create_admin_amin.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from api.utils.crypto import hash_password
from shared.config.settings import settings
from datetime import datetime

async def create_admin_amin():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]
    users = db["users"]
    
    # YOUR Admin credentials
    email = "aminaminhelali@gmail.com"
    password = "ameenameen"
    
    # Delete if exists
    existing = await users.find_one({"email": email})
    if existing:
        print(f"🗑️  Deleting existing user: {email}")
        await users.delete_one({"email": email})
    
    # Create ADMIN (not normal user!)
    admin_user = {
        "email": email,
        "full_name": "Amin Helali",
        "hashed_password": hash_password(password),
        "is_verified": True,
        "mfa_enabled": True,
        "role": "admin",  # ← ADMIN ROLE!
        "custom_permissions": [],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None,
        "created_by": None,
        "mfa_secret": None
    }
    
    result = await users.insert_one(admin_user)
    
    print("="*70)
    print("✅ ADMIN CREATED SUCCESSFULLY!")
    print("="*70)
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print(f"🎭 Role: ADMIN 👑")
    print(f"🆔 MongoDB ID: {result.inserted_id}")
    print("="*70)
    
    # Verify in database
    check = await users.find_one({"email": email})
    if check:
        print(f"\n✅ VERIFIED IN DATABASE:")
        print(f"   Email: {check['email']}")
        print(f"   Name: {check['full_name']}")
        print(f"   Role: {check['role']}")
        print(f"   Active: {check['is_active']}")
        print(f"   Verified: {check['is_verified']}")
        
    
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_amin())