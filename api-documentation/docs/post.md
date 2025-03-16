# Post API Documentation

## Overview
This document outlines the API endpoints related to post management, including creating, retrieving, updating, and deleting posts, as well as adding comments to posts.

## Base URL
`/api/posts`

## Endpoints

### 1. Create Post
- **Endpoint:** `/create_post`
- **Method:** `POST`
- **Description:** Create a new post with optional media file upload.
- **Headers:**
  - `Authorization: Bearer <token>`
- **Form Data:**
  - `title` (string, required): The title of the post.
  - `content` (string, required): The content of the post.
  - `media_file` (file, optional): An optional media file to upload.
- **Responses:**
  - `200 OK`: Post created successfully.
    - Example: `{"message": "Post created", "post_id": "1234567890abcdef"}`
  - `400 Bad Request`: Missing required fields.
    - Example: `{"message": "Title and content are required and must not be empty"}`
  - `401 Unauthorized`: Invalid token.
    - Example: `{"message": "Invalid token"}`
  - `500 Internal Server Error`: An error occurred while creating the post.

### 2. Get Posts
- **Endpoint:** `/get_posts`
- **Method:** `GET`
- **Description:** Retrieve a filtered, paginated list of posts.
- **Query Parameters:**
  - `page` (integer, optional): The page number to retrieve (default is 1).
  - `per_page` (integer, optional): Number of posts per page (default is 10).
  - `user_id` (string, optional): Filter posts by user ID.
  - `search` (string, optional): Search term to filter posts by title or content.
- **Responses:**
  - `200 OK`: Posts retrieved successfully.
    - Example: 
      ```
      {
        "posts": [{"_id": "1234567890abcdef", "title": "Post Title", "content": "Post content", ...}],
        "pagination": {
          "total": 100,
          "page": 1,
          "per_page": 10,
          "pages": 10
        }
      }
      ```
  - `400 Bad Request`: Invalid pagination parameters.
    - Example: `{"message": "Page and per_page must be positive integers"}`
  - `500 Internal Server Error`: An error occurred while retrieving posts.

### 3. Get Post
- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Description:** Retrieve a single post by post ID.
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post to retrieve.
- **Responses:**
  - `200 OK`: Post retrieved successfully.
    - Example: `{"post": {"_id": "1234567890abcdef", "title": "Post Title", "content": "Post content", ...}}`
  - `400 Bad Request`: Missing post ID.
    - Example: `{"message": "Post ID is required"}`
  - `404 Not Found`: Post not found.
    - Example: `{"message": "Post not found"}`
  - `500 Internal Server Error`: An error occurred while retrieving the post.

### 4. Update Post
- **Endpoint:** `/update_post`
- **Method:** `PUT`
- **Description:** Update a post by post ID with optional media file replacement.
- **Headers:**
  - `Authorization: Bearer <token>`
- **Form Data:**
  - `post_id` (string, required): The ID of the post to update.
  - `title` (string, optional): The new title of the post.
  - `content` (string, optional): The new content of the post.
  - `media_file` (file, optional): An optional new media file to upload.
- **Responses:**
  - `200 OK`: Post updated successfully.
    - Example: `{"message": "Post updated"}`
  - `400 Bad Request`: Missing required fields or no changes provided.
    - Example: `{"message": "No changes provided"}`
  - `401 Unauthorized`: Invalid token.
    - Example: `{"message": "Invalid token"}`
  - `404 Not Found`: Post not found.
    - Example: `{"message": "Post not found"}`
  - `500 Internal Server Error`: An error occurred while updating the post.

### 5. Delete Post
- **Endpoint:** `/delete_post`
- **Method:** `DELETE`
- **Description:** Delete a post by post ID.
- **Headers:**
  - `Authorization: Bearer <token>`
- **Query Parameters:**
  - `post_id` (string, required): The ID of the post to delete.
- **Responses:**
  - `200 OK`: Post deleted successfully.
    - Example: `{"message": "Post deleted"}`
  - `400 Bad Request`: Missing post ID.
    - Example: `{"message": "Post ID is required"}`
  - `401 Unauthorized`: Invalid token.
    - Example: `{"message": "Invalid token"}`
  - `404 Not Found`: Post not found.
    - Example: `{"message": "Post not found"}`
  - `500 Internal Server Error`: An error occurred while deleting the post.

### 6. Create Comment
- **Endpoint:** `/create_comment`
- **Method:** `POST`
- **Description:** Create a comment on a post.
- **Headers:**
  - `Authorization: Bearer <token>`
- **Form Data:**
  - `post_id` (string, required): The ID of the post to comment on.
  - `comment` (string, required): The content of the comment.
- **Responses:**
  - `200 OK`: Comment created successfully.
    - Example: `{"message": "Comment created"}`
  - `400 Bad Request`: Missing required fields.
    - Example: `{"message": "Post ID and comment are required and must not be empty"}`
  - `401 Unauthorized`: Invalid token.
    - Example: `{"message": "Invalid token"}`
  - `404 Not Found`: Post not found.
    - Example: `{"message": "Post not found"}`
  - `500 Internal Server Error`: An error occurred while creating the comment.