from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class SupabaseClient:
    _instance = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def _initialize_client(cls):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        cls._client = create_client(url, key)

    @classmethod
    def get_client(cls) -> Client:
        """Get the Supabase client instance"""
        if cls._client is None:
            cls._initialize_client()
        return cls._client

    @classmethod
    def signup(cls, email: str, password: str, chronotype: str):
        client = cls.get_client()
    
        
        db_chronotype = chronotype
        
        try:
            # Sign up a new user
            auth_response = client.auth.sign_up({
                'email': email,
                'password': password
            })

            if not auth_response.user:
                error_msg = getattr(auth_response, 'message', 'Unknown authentication error')
                raise Exception(f"Authentication failed: {error_msg}")
            
            # Create user profile in database
            from core.models.user import User
            
            try:
                hash_password = User.hashedpassword(password)
            except Exception as e:
                raise Exception(f"Password hashing failed: {str(e)}")

            profile_data = {
                "user_id": auth_response.user.id,
                "email": email,
                "hash_password": hash_password,
                "chronotype": db_chronotype
            }

            try:
                response = client.table("users").insert(profile_data).execute()
                
                if not response.data:
                    raise Exception("Database insert returned no data")
                    
                return response.data[0]
                
            except Exception as e:
                # Clean up auth user if profile creation fails
                try:
                    client.auth.admin.delete_user(auth_response.user.id)
                except:
                    pass
                
                raise Exception(f"Database profile creation failed: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Registration failed: {str(e)}")
    
    @classmethod
    def login(cls, email: str, password: str):
        """Log in an existing user"""
        client = cls.get_client()
        
        try:
            # Authenticate with Supabase Auth
            auth_response = client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if not auth_response.user:
                error_msg = getattr(auth_response, 'message', 'Unknown authentication error')
                raise Exception(f"Authentication failed: {error_msg}")
            
            # Retrieve user profile from database
            response = client.table("users").select("*").eq("user_id", auth_response.user.id).execute()

            if not response.data:
                raise Exception("User profile not found in database")
            
            return response.data[0]
            
        except Exception as e:
            raise Exception(f"Login failed: {str(e)}")