Below is an API documentation for the provided Flask application code, which includes endpoints for post management, user history/likes, and authentication. This documentation follows a standard format with endpoint descriptions, request methods, parameters, responses, and examples.

---

# API Documentation

This API provides functionality for managing posts, user history, likes, and authentication in a social media-like application. It uses Flask Blueprints and integrates with MySQL (for user data), MongoDB (for posts and history), and MinIO (for media storage).

**Base URL:** `http://<your-domain-or-ip>:<port>`

**Authentication:** Most endpoints require a JWT token passed in the `Authorization` header as `Bearer <token>`.

**Date:** Current date is March 17, 2025 (as per system context).

---

## Table of Contents
1. [Post Management](#post-management)
   - [Create Post](#create-post)
   - [Get Posts](#get-posts)
   - [Get Post](#get-post)
   - [Delete Post](#delete-post)
   - [Update Post](#update-post)
   - [Create Comment](#create-comment)
2. [User History and Likes](#user-history-and-likes)
   - [Get User History and Likes](#get-user-history-and-likes)
   - [Add Read History](#add-read-history)
   - [Add Like](#add-like)
   - [Remove Like](#remove-like)
3. [Authentication](#authentication)
   - [Login](#login)
   - [Register](#register)
   - [Logout](#logout)
   - [Renew Token](#renew-token)

---

## Post Management

### Create Post
Create a new post with optional media file upload.

- **Endpoint:** `/create_post`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Authorization:** Required (`Bearer <token>`)
- **Request Parameters:**
  - `title` (form, string, required): The title of the post.
  - `content` (form, string, required): The content of the post.
  - `media_file` (file, optional): A media file to upload (e.g., image, video).
- **Responses:**
  - `200`: Post created successfully.
    ```json
    {"message": "Post created", "post_id": "507f1f77bcf86cd799439011"}
    ```
  - `400`: Missing or invalid parameters.
    ```json
    {"message": "Title and content are required and must not be empty"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: User not found.
    ```json
    {"message": "User not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while creating the post"}
    ```

---

### Get Posts
Retrieve a filtered, paginated list of posts.

- **Endpoint:** `/get_posts`
- **Method:** `GET`
- **Authorization:** Not required
- **Query Parameters:**
  - `page` (integer, optional, default=1): Page number.
  - `per_page` (integer, optional, default=10): Posts per page.
  - `user_id` (string/integer, optional): Filter by user ID.
  - `search` (string, optional): Search term for title or content (case-insensitive).
- **Responses:**
  - `200`: Posts retrieved successfully.
    ```json
    {
      "posts": [
        {
          "_id": "507f1f77bcf86cd799439011",
          "title": "My Post",
          "content": "Hello world!",
          "user_id": 1,
          "media_url": "http://minio.example.com/1_20250317123456_image.jpg",
          "comments": [],
          "comment_count": 0,
          "created_at": "2025-03-17T12:34:56Z"
        }
      ],
      "pagination": {
        "total": 1,
        "page": 1,
        "per_page": 10,
        "pages": 1
      }
    }
    ```
  - `400`: Invalid page or per_page values.
    ```json
    {"message": "Page and per_page must be positive integers"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Get Post
Retrieve a single post by ID.

- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Authorization:** Not required
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Responses:**
  - `200`: Post retrieved successfully.
    ```json
    {
      "post": {
        "_id": "507f1f77bcf86cd799439011",
        "title": "My Post",
        "content": "Hello world!",
        "user_id": 1,
        "media_url": "http://minio.example.com/1_20250317123456_image.jpg",
        "comments": [],
        "comment_count": 0,
        "created_at": "2025-03-17T12:34:56Z"
      }
    }
    ```
  - `400`: Missing post ID.
    ```json
    {"message": "Post ID is required"}
    ```
  - `404`: Post not found.
    ```json
    {"message": "Post not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Delete Post
Delete a post by ID (only the owner can delete).

- **Endpoint:** `/delete_post`
- **Method:** `DELETE`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Responses:**
  - `200`: Post deleted successfully.
    ```json
    {"message": "Post deleted"}
    ```
  - `400`: Missing token or post ID.
    ```json
    {"message": "Post ID is required"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `403`: Unauthorized (not the post owner).
    ```json
    {"message": "Unauthorized"}
    ```
  - `404`: Post or user not found.
    ```json
    {"message": "Post not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Update Post
Update a post by ID with optional media replacement (only the owner can update).

- **Endpoint:** `/update_post`
- **Method:** `PUT`
- **Content-Type:** `multipart/form-data`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Request Parameters:**
  - `title` (form, string, optional): Updated title.
  - `content` (form, string, optional): Updated content.
  - `media_file` (file, optional): New media file to replace existing one.
- **Responses:**
  - `200`: Post updated successfully.
    ```json
    {"message": "Post updated"}
    ```
  - `400`: Missing token, post ID, or no changes provided.
    ```json
    {"message": "No changes provided"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `403`: Unauthorized (not the post owner).
    ```json
    {"message": "Unauthorized"}
    ```
  - `404`: Post or user not found.
    ```json
    {"message": "Post not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while updating the post"}
    ```

---

### Create Comment
Add a comment to a post.

- **Endpoint:** `/create_comment`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Request Parameters:**
  - `comment` (form, string, required): The comment text.
- **Responses:**
  - `200`: Comment created successfully.
    ```json
    {"message": "Comment created"}
    ```
  - `400`: Missing token, post ID, or comment.
    ```json
    {"message": "Post ID and comment are required and must not be empty"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: Post or user not found.
    ```json
    {"message": "Post not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

## User History and Likes

### Get User History and Likes
Retrieve a user's history and liked posts.

- **Endpoint:** `/get_history_like`
- **Method:** `GET`
- **Authorization:** Not required
- **Query Parameters:**
  - `username` (string, required): The username of the user.
- **Responses:**
  - `200`: History and likes retrieved successfully.
    ```json
    {
      "_id": "507f1f77bcf86cd799439011",
      "user_id": 1,
      "history": [
        {"post_id": "507f191e810c19729de860ea", "timestamp": "2025-03-17T12:34:56Z"}
      ],
      "likes": [
        {"post_id": "507f191e810c19729de860eb", "timestamp": "2025-03-17T12:35:00Z"}
      ]
    }
    ```
  - `404`: User or history not found.
    ```json
    {"message": "User not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while retrieving history"}
    ```

---

### Add Read History
Add a post to the user's read history or update its timestamp if already present.

- **Endpoint:** `/add_read_history`
- **Method:** `POST`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Responses:**
  - `200`: History added or updated.
    ```json
    {"message": "History added"}
    ```
    ```json
    {"message": "History timestamp updated"}
    ```
  - `400`: Missing token or post ID.
    ```json
    {"message": "Post ID is required"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: User not found.
    ```json
    {"message": "User not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while updating read history"}
    ```

---

### Add Like
Add a like to a post or inform if already liked.

- **Endpoint:** `/add_like`
- **Method:** `POST`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Responses:**
  - `200`: Like added or already liked.
    ```json
    {"message": "Post liked successfully", "already_liked": false}
    ```
    ```json
    {"message": "You've already liked this post", "already_liked": true}
    ```
  - `400`: Missing token or post ID.
    ```json
    {"message": "Post ID is required"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: User not found.
    ```json
    {"message": "User not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while liking the post"}
    ```

---

### Remove Like
Remove a like from a post.

- **Endpoint:** `/remove_like`
- **Method:** `DELETE`
- **Authorization:** Required (`Bearer <token>`)
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post (MongoDB ObjectId).
- **Responses:**
  - `200`: Like removed successfully.
    ```json
    {"message": "Like removed successfully"}
    ```
  - `400`: Missing token or post ID.
    ```json
    {"message": "Post ID is required"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: User or like not found.
    ```json
    {"message": "You haven't liked this post"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred while removing the like"}
    ```

---

## Authentication

### Login
Authenticate a user and return a JWT token.

- **Endpoint:** `/login`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  - `username` (form, string, required): The username.
  - `password` (form, string, required): The password.
- **Responses:**
  - `200`: Login successful or already logged in.
    ```json
    {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
    ```
    ```json
    {"message": "User already logged in"}
    ```
  - `400`: Invalid password.
    ```json
    {"message": "Invalid password"}
    ```
  - `401`: Invalid token.
    ```json
    {"message": "Invalid token"}
    ```
  - `404`: User not found.
    ```json
    {"message": "User not found"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Register
Register a new user.

- **Endpoint:** `/register`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  - `username` (form, string, required): The username.
  - `password` (form, string, required): The password.
  - `email` (form, string, required): The email address.
- **Responses:**
  - `201`: User created successfully.
    ```json
    {
      "message": "User created successfully",
      "user_id": 1
    }
    ```
  - `400`: User already exists.
    ```json
    {"message": "User already exists"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Logout
Invalidate the user's token.

- **Endpoint:** `/logout`
- **Method:** `POST`
- **Authorization:** Required (`Bearer <token>`)
- **Responses:**
  - `200`: Logout successful.
    ```json
    {"message": "User logged out successfully"}
    ```
  - `401`: Missing or invalid token.
    ```json
    {"message": "Token is missing"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

### Renew Token
Renew an existing JWT token.

- **Endpoint:** `/renew_token`
- **Method:** `POST`
- **Authorization:** Required (`Bearer <token>`)
- **Responses:**
  - `200`: Token renewed successfully.
    ```json
    {"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}
    ```
  - `401`: Missing or invalid token.
    ```json
    {"message": "Token is missing"}
    ```
  - `500`: Server error.
    ```json
    {"message": "An error occurred during authentication"}
    ```

---

This documentation provides a comprehensive overview of the API endpoints, including their purpose, parameters, and possible responses. Let me know if you'd like to refine it further or add examples!