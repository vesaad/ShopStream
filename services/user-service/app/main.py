from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from app.models import UserRegister, UserLogin, UserResponse, TokenResponse
from app.database import db
from app.auth import hash_password, verify_password, create_access_token, verify_token
from app.kafka_producer import event_producer

app = FastAPI(
    title="User Service",
    description="Authentication & User Management Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "service": "user-service",
        "status": "healthy",
        "port": 8001
    }

@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister):
    """
    Register a new user
    - Publishes USER_REGISTERED event to Kafka
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            # Hash password
            hashed_password = hash_password(user.password)
            
            # Insert user
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash)
                OUTPUT INSERTED.id, INSERTED.username, INSERTED.email, INSERTED.created_at
                VALUES (?, ?, ?)
                """,
                (user.username, user.email, hashed_password)
            )
            result = cursor.fetchone()
            conn.commit()
            
            user_data = {
                "user_id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": str(result[3])
            }
            
            # Publish Kafka event
            event_producer.publish_user_event("USER_REGISTERED", user_data)
            
            return {
                "message": "User registered successfully",
                **user_data
            }
            
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if "username" in error_msg or "unique" in error_msg:
                raise HTTPException(status_code=400, detail="Username already exists")
            elif "email" in error_msg:
                raise HTTPException(status_code=400, detail="Email already exists")
            raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin):
    """
    Login user and return JWT token
    - Publishes USER_LOGIN event to Kafka
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username = ?",
            (credentials.username,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(credentials.password, user[3]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create JWT token
        token_data = {"user_id": user[0], "username": user[1]}
        access_token = create_access_token(token_data)
        
        # Publish event
        event_producer.publish_user_event("USER_LOGIN", {
            "user_id": user[0],
            "username": user[1],
            "email": user[2]
        })
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user[0],
            username=user[1]
        )

@app.get("/users/me", response_model=UserResponse)
def get_current_user(payload: dict = Depends(verify_token)):
    """Get current authenticated user"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (payload["user_id"],)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user[0],
            username=user[1],
            email=user[2],
            created_at=user[3]
        )

@app.get("/users", response_model=dict)
def list_users():
    """List all users (for testing/admin)"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, created_at FROM users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()
        
        return {
            "users": [
                {
                    "id": u[0],
                    "username": u[1],
                    "email": u[2],
                    "created_at": str(u[3])
                }
                for u in users
            ],
            "count": len(users)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)