# Authentication API Documentation

This document outlines the API endpoints related to user authentication, including login, registration, logout, and token renewal.

## Endpoints

### 1. Login

- **URL**: `/login`
- **Method**: `POST`
- **Description**: Authenticates a user and returns a JWT token.
- **Request Body**:
  - `username` (string, required): The username of the user.
  - `password` (string, required): The password of the user.
- **Headers**:
  - `Authorization` (string, optional): Bearer token for already logged-in users.
- **Responses**:
  - **200 OK**: 
    - Content: 
      ```json
      {
        "token": "JWT_TOKEN"
      }
      ```
  - **400 Bad Request**: 
    - Content: 
      ```json
      {
        "message": "Invalid password"
      }
      ```
  - **404 Not Found**: 
    - Content: 
      ```json
      {
        "message": "User not found"
      }
      ```
  - **500 Internal Server Error**: 
    - Content: 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 2. Register

- **URL**: `/register`
- **Method**: `POST`
- **Description**: Registers a new user.
- **Request Body**:
  - `username` (string, required): The desired username.
  - `password` (string, required): The desired password.
  - `email` (string, required): The email address of the user.
- **Responses**:
  - **201 Created**: 
    - Content: 
      ```json
      {
        "message": "User created successfully",
        "user_id": "USER_ID"
      }
      ```
  - **400 Bad Request**: 
    - Content: 
      ```json
      {
        "message": "User already exists"
      }
      ```
  - **500 Internal Server Error**: 
    - Content: 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 3. Logout

- **URL**: `/logout`
- **Method**: `POST`
- **Description**: Logs out the user by invalidating the token.
- **Headers**:
  - `Authorization` (string, required): Bearer token of the user.
- **Responses**:
  - **200 OK**: 
    - Content: 
      ```json
      {
        "message": "User logged out successfully"
      }
      ```
  - **401 Unauthorized**: 
    - Content: 
      ```json
      {
        "message": "Token is missing"
      }
      ```
  - **500 Internal Server Error**: 
    - Content: 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 4. Renew Token

- **URL**: `/renew_token`
- **Method**: `POST`
- **Description**: Renews the JWT token if the current token is valid.
- **Headers**:
  - `Authorization` (string, required): Bearer token of the user.
- **Responses**:
  - **200 OK**: 
    - Content: 
      ```json
      {
        "token": "NEW_JWT_TOKEN"
      }
      ```
  - **401 Unauthorized**: 
    - Content: 
      ```json
      {
        "message": "Token is missing"
      }
      ```
  - **500 Internal Server Error**: 
    - Content: 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

