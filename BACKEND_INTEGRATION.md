# Backend Integration for DishDive

## Overview
This document outlines the integration between the Flutter frontend and Go backend for authentication in the DishDive application.

## Backend API Details

### Base Configuration
- **Base URL**: `http://10.0.2.2:8080` (for Android emulator)
- **Server Port**: 8080 (configured in `server/config.yaml`)
- **JWT Secret**: "DishDive" (configured in `server/config.yaml`)

### Authentication Endpoints

#### 1. User Registration
- **Endpoint**: `POST /Register`
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  ```
  user_name: string (username)
  password_hash: string (password)
  file: File (profile image)
  ```
- **Response** (201 Created):
  ```json
  {
    "user_id": 1,
    "user_name": "username",
    "image_link": "https://minio.dishdive.sit.kmutt.ac.th/dishdive/filename.jpg"
  }
  ```

#### 2. User Login
- **Endpoint**: `POST /Login`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "user_name": "username",
    "password_hash": "password"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "user_id": 1,
    "user_name": "username",
    "token": "jwt_token_here"
  }
  ```

#### 3. Get Current User
- **Endpoint**: `GET /GetCurrentUser`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "user_id": 1,
    "username": "username",
    "image_link": "https://minio.dishdive.sit.kmutt.ac.th/dishdive/filename.jpg",
    "password_hash": "hashed_password"
  }
  ```

## Frontend Implementation

### Key Files Updated

#### 1. Authentication Service (`lib/services/auth_service.dart`)
- Centralized API calls for authentication
- Error handling and response parsing
- Methods: `login()`, `register()`, `getCurrentUser()`

#### 2. API Configuration (`lib/Utils/api_config.dart`)
- Centralized API endpoint configuration
- Base URL and headers management
- Easy to modify for different environments

#### 3. Token Provider (`lib/provider/token_provider.dart`)
- Enhanced with SharedPreferences for token persistence
- Methods: `loadToken()`, `setToken()`, `clearToken()`, `isAuthenticated`
- Automatic token loading on app startup

#### 4. Login Page (`lib/Pages/Auth/login.dart`)
- Integrated with AuthService
- Proper error handling and loading states
- Token storage and navigation

#### 5. Register Page (`lib/Pages/Auth/register.dart`)
- Integrated with AuthService
- Form validation including image selection
- Proper error handling and loading states

#### 6. Main App (`lib/main.dart`)
- Token provider initialization
- Authentication-based routing

### Features Implemented

1. **User Registration**:
   - Form validation (all fields required, password confirmation)
   - Image upload validation
   - API integration with multipart/form-data
   - Success/error feedback
   - Navigation to login page

2. **User Login**:
   - Form validation
   - API integration with JSON payload
   - JWT token storage
   - Success/error feedback
   - Navigation to home page

3. **Token Management**:
   - Persistent token storage using SharedPreferences
   - Automatic token loading on app startup
   - Authentication state management
   - Secure logout with token cleanup

4. **Error Handling**:
   - Network error handling
   - API error response parsing
   - User-friendly error messages
   - Loading indicators

## Usage

### Prerequisites
1. Ensure the Go backend server is running on port 8080
2. Update the base URL in `api_config.dart` if needed:
   - Android Emulator: `http://10.0.2.2:8080`
   - iOS Simulator: `http://127.0.0.1:8080`
   - Physical Device: `http://YOUR_COMPUTER_IP:8080`

### Running the Application
1. Start the backend server: `cd server && go run .`
2. Run the Flutter app: `flutter run`
3. Register a new user or login with existing credentials

### Testing
- Test registration with various inputs and image uploads
- Test login with valid/invalid credentials
- Test token persistence by closing and reopening the app
- Test logout functionality

## Security Considerations

1. **Password Handling**: Passwords are sent as plain text to the backend where they are hashed using bcrypt
2. **JWT Tokens**: Stored securely in SharedPreferences and used for API authentication
3. **HTTPS**: In production, ensure all API calls use HTTPS
4. **Token Expiration**: Implement token refresh mechanism for production use

## Future Enhancements

1. **Token Refresh**: Implement automatic token refresh
2. **Biometric Authentication**: Add fingerprint/face ID support
3. **Social Login**: Integrate with Google/Facebook/Apple
4. **Password Reset**: Implement forgot password functionality
5. **User Profile Updates**: Complete the profile editing integration
