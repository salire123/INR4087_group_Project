# Social Media API Documentation

## Authentication

### Register a New User
- **URL**: `/auth/register`
- **Method**: `POST`
- **Description**: Create a new user account
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "string"
  }
  ```
- **Response**:
  - `201 Created`: User created successfully
    ```json
    {
      "message": "User created successfully",
      "user_id": "integer"
    }
    ```
  - `400 Bad Request`: User already exists
  - `500 Server Error`: An error occurred

### Login
- **URL**: `/auth/login`
- **Method**: `POST`
- **Description**: Authenticate and receive a JWT token
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**:
  - `200 OK`: Authentication successful
    ```json
    {
      "token": "string"
    }
    ```
  - `400 Bad Request`: Invalid password
  - `404 Not Found`: User not found
  - `500 Server Error`: An error occurred

### Logout
- **URL**: `/auth/logout`
- **Method**: `POST`
- **Description**: Invalidate the current JWT token
- **Headers**: `Authorization: Bearer {token}`
- **Response**:
  - `200 OK`: User logged out successfully
  - `401 Unauthorized`: Token is missing or invalid
  - `500 Server Error`: An error occurred

### Renew Token
- **URL**: `/auth/renew_token`
- **Method**: `POST`
- **Description**: Renew an existing valid JWT token
- **Headers**: `Authorization: Bearer {token}`
- **Response**:
  - `200 OK`: Token renewed successfully
    ```json
    {
      "token": "string"
    }
    ```
  - `401 Unauthorized`: Token is missing or invalid
  - `500 Server Error`: An error occurred

## Posts

### Create Post
- **URL**: `/post/create_post`
- **Method**: `POST`
- **Description**: Create a new post
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string",
    "media_url": "string (optional)"
  }
  ```
- **Response**:
  - `201 Created`: Post created successfully
  - `400 Bad Request`: Missing required fields or token
  - `401 Unauthorized`: Invalid token
  - `500 Server Error`: An error occurred

### Get Posts
- **URL**: `/post/get_posts`
- **Method**: `GET`
- **Description**: Get a filtered, paginated list of posts
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `per_page`: Number of posts per page (default: 10)
  - `user_id`: Filter by user ID (optional)
  - `search`: Search term for title or content (optional)
- **Response**:
  - `200 OK`: List of posts returned
  - `400 Bad Request`: Invalid pagination parameters
  - `500 Server Error`: An error occurred

### Get Single Post
- **URL**: `/post/get_post`
- **Method**: `GET`
- **Description**: Get a single post by ID
- **Query Parameters**:
  - `post_id`: ID of the post
- **Response**:
  - `200 OK`: Post details
  - `400 Bad Request`: Missing post ID
  - `404 Not Found`: Post not found
  - `500 Server Error`: An error occurred

### Update Post
- **URL**: `/post/update_post`
- **Method**: `PUT`
- **Description**: Update an existing post
- **Headers**: `Authorization: Bearer {token}`
- **Query Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string",
    "media_url": "string (optional)"
  }
  ```
- **Response**:
  - `200 OK`: Post updated successfully
  - `400 Bad Request`: Missing required fields or post ID
  - `401 Unauthorized`: Invalid token or not the post owner
  - `404 Not Found`: Post not found
  - `500 Server Error`: An error occurred

### Delete Post
- **URL**: `/post/delete_post`
- **Method**: `DELETE`
- **Description**: Delete an existing post
- **Headers**: `Authorization: Bearer {token}`
- **Query Parameters**:
  - `post_id`: ID of the post
- **Response**:
  - `200 OK`: Post deleted successfully
  - `400 Bad Request`: Missing post ID
  - `401 Unauthorized`: Invalid token or not the post owner
  - `404 Not Found`: Post not found
  - `500 Server Error`: An error occurred

### Create Comment
- **URL**: `/post/create_comment`
- **Method**: `POST`
- **Description**: Add a comment to a post
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**:
  ```json
  {
    "post_id": "string",
    "comment": "string"
  }
  ```
- **Response**:
  - `201 Created`: Comment added successfully
  - `400 Bad Request`: Missing required fields
  - `401 Unauthorized`: Invalid token
  - `404 Not Found`: Post not found
  - `500 Server Error`: An error occurred

### Like Post
- **URL**: `/post/{post_id}/like`
- **Method**: `GET`
- **Description**: Like a post
- **Headers**: `Authorization: Bearer {token}`
- **Response**:
  - `200 OK`: Post liked successfully
  - `401 Unauthorized`: Invalid token
  - `404 Not Found`: Post not found
  - `500 Server Error`: An error occurred

## History

### Get User History
- **URL**: `/history/{username}`
- **Method**: `GET`
- **Description**: Get a user's history
- **Response**:
  - `200 OK`: User history returned
    ```json
    {
      "history": [
        {
          "_id": "string",
          "user_id": "integer",
          "post_id": "string",
          "timestamp": "datetime"
        }
      ]
    }
    ```
  - `404 Not Found`: User not found
  - `500 Server Error`: An error occurred

### Add Read History
- **URL**: `/history/add_read_history`
- **Method**: `POST`
- **Description**: Add a post to a user's read history
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**:
  ```json
  {
    "post_id": "string",
    "username": "string"
  }
  ```
- **Response**:
  - `200 OK`: Read history added successfully
  - `400 Bad Request`: Missing required fields
  - `401 Unauthorized`: Invalid token
  - `404 Not Found`: User not found
  - `500 Server Error`: An error occurred

### Add Like
- **URL**: `/history/add_like`
- **Method**: `POST`
- **Description**: Add a like to a post
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**:
  ```json
  {
    "post_id": "string",
    "username": "string"
  }
  ```
- **Response**:
  - `200 OK`: Like added successfully
  - `400 Bad Request`: Missing required fields
  - `401 Unauthorized`: Invalid token
  - `404 Not Found`: User or post not found
  - `500 Server Error`: An error occurred

### Remove Like
- **URL**: `/history/remove_like`
- **Method**: `POST`
- **Description**: Remove a like from a post
- **Headers**: `Authorization: Bearer {token}`
- **Request Body**:
  ```json
  {
    "post_id": "string",
    "username": "string"
  }
  ```
- **Response**:
  - `200 OK`: Like removed successfully
  - `400 Bad Request`: Missing required fields
  - `401 Unauthorized`: Invalid token
  - `404 Not Found`: User or post not found
  - `500 Server Error`: An error occurred

## Error Responses

All endpoints may return these common error responses:

- `400 Bad Request`: Invalid input or missing required parameters
- `401 Unauthorized`: Authentication failure or missing authentication
- `404 Not Found`: Requested resource not found
- `500 Server Error`: Unexpected server error

Example error response:
```json
{
  "message": "Error description"
}
```