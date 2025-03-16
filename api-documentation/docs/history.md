# User History API Documentation

This document provides details on the user history-related API endpoints, including retrieving user history, adding read history, and managing likes on posts.

## Endpoints

### 1. Get User History

- **Endpoint:** `/history/<string:username>`
- **Method:** `GET`
- **Description:** Retrieves the history of a user by their username.
- **Parameters:**
  - `username` (path parameter): The username of the user whose history is being retrieved.
- **Responses:**
  - **200 OK**
    - **Content:** 
      ```json
      {
        "history": [
          {
            "_id": "string",
            "user_id": "integer",
            "post_id": "string",
            "timestamp": "string"
          }
        ]
      }
      ```
  - **404 Not Found**
    - **Content:** 
      ```json
      {
        "message": "User not found"
      }
      ```
  - **500 Internal Server Error**
    - **Content:** 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 2. Add Read History

- **Endpoint:** `/add_read_history`
- **Method:** `POST`
- **Description:** Adds a post to the user's read history.
- **Parameters:**
  - `post_id` (form data): The ID of the post being added to the history.
  - `username` (form data): The username of the user.
- **Headers:**
  - `Authorization`: Bearer token for authentication.
- **Responses:**
  - **200 OK**
    - **Content:** 
      ```json
      {
        "message": "History added"
      }
      ```
  - **400 Bad Request**
    - **Content:** 
      ```json
      {
        "message": "Post ID is required"
      }
      ```
  - **404 Not Found**
    - **Content:** 
      ```json
      {
        "message": "User not found"
      }
      ```
  - **500 Internal Server Error**
    - **Content:** 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 3. Add Like

- **Endpoint:** `/add_like`
- **Method:** `POST`
- **Description:** Adds a like to a post by the user.
- **Parameters:**
  - `post_id` (form data): The ID of the post being liked.
  - `username` (form data): The username of the user.
- **Headers:**
  - `Authorization`: Bearer token for authentication.
- **Responses:**
  - **200 OK**
    - **Content:** 
      ```json
      {
        "message": "Like added"
      }
      ```
  - **400 Bad Request**
    - **Content:** 
      ```json
      {
        "message": "Post ID is required"
      }
      ```
  - **404 Not Found**
    - **Content:** 
      ```json
      {
        "message": "User not found"
      }
      ```
  - **500 Internal Server Error**
    - **Content:** 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```

### 4. Remove Like

- **Endpoint:** `/remove_like`
- **Method:** `POST`
- **Description:** Removes a like from a post by the user.
- **Parameters:**
  - `post_id` (form data): The ID of the post from which the like is being removed.
  - `username` (form data): The username of the user.
- **Headers:**
  - `Authorization`: Bearer token for authentication.
- **Responses:**
  - **200 OK**
    - **Content:** 
      ```json
      {
        "message": "Like removed"
      }
      ```
  - **400 Bad Request**
    - **Content:** 
      ```json
      {
        "message": "Post ID is required"
      }
      ```
  - **404 Not Found**
    - **Content:** 
      ```json
      {
        "message": "User not found"
      }
      ```
  - **500 Internal Server Error**
    - **Content:** 
      ```json
      {
        "message": "An error occurred during authentication"
      }
      ```