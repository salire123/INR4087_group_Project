# API Documentation for Backend Routes

## Overview

This documentation covers the backend routes for a social media platform API built with Flask. The API is organized into several modules:

- **Authentication (`auth_bp`)** - User registration, login, logout, and token management
- **User Management (`user_bp`)** - Managing user subscriptions and retrieving user information
- **Posts (`post_bp`)** - Creating, retrieving, updating, and deleting posts and comments
- **History (`history_bp`)** - Managing user reading history and post interactions (likes)
- **Analytics (`analyze_bp`)** - Data visualization and platform metrics

The API uses MySQL for user data, MongoDB for posts and user history, MinIO for media storage, and Redis for caching and tracking post reads.

---

## Authentication (`auth_bp`)

### Register a New User
```
POST /auth/register
```
**Form Parameters:**
- `username` (string, required) - Unique username
- `password` (string, required) - User's password
- `email` (string, required) - User's email address

**Response:**
- `201` - `{ "message": "User created successfully", "user_id": <int> }`
- `400` - `{ "message": "User already exists" }` (if username or email is taken)
- `500` - `{ "message": "An error occurred during authentication" }`

**Notes:**
- Password is hashed using `werkzeug.security.generate_password_hash`.
- Creates a user in MySQL and a corresponding history document in MongoDB.

### Login
```
POST /auth/login
```
**Form Parameters:**
- `username` (string, required) - Username
- `password` (string, required) - User's password

**Headers (optional):**
- `Authorization: Bearer <token>` - For already authenticated users

**Response:**
- `200` - `{ "token": "<jwt_token>" }` or `{ "message": "User already logged in" }` (if token is valid)
- `400` - `{ "message": "Invalid password" }`
- `401` - `{ "message": "Invalid token" }` (if token is provided but invalid)
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred during authentication" }`

**Notes:**
- Uses JWT tokens for authentication with a 1-hour expiration.

### Logout
```
POST /auth/logout
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Response:**
- `200` - `{ "message": "User logged out successfully" }`
- `401` - `{ "message": "Token is missing" }` or `{ "message": "Token is invalid" }`
- `500` - `{ "message": "An error occurred during authentication" }`

**Notes:**
- Blacklists the token to invalidate it.

### Renew Token
```
POST /auth/renew_token
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Response:**
- `200` - `{ "token": "<new_jwt_token>" }`
- `401` - `{ "message": "Token is missing" }` or `{ "message": "Token is invalid" }`
- `500` - `{ "message": "An error occurred during authentication" }`

**Notes:**
- Generates a new token and blacklists the old one.

---

## User Management (`user_bp`)

### Subscribe to a User
```
POST /user/subscribe?username=<username>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `username` (string, required) - Username to subscribe to

**Response:**
- `200` - `{ "message": "Subscribed successfully" }`
- `400` - `{ "message": "Missing Subscribe_to" }`, `{ "message": "Already subscribed" }`, or `{ "message": "Cannot subscribe to self" }`
- `401` - `{ "message": "Missing token" }` or `{ "message": "Invalid token" }`
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred during subscription" }`

**Notes:**
- Updates `Subscriber_to` and `Subscribers` fields in MongoDB for both users.

### Unsubscribe from a User
```
POST /user/unsubscribe?username=<username>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `username` (string, required) - Username to unsubscribe from

**Response:**
- `200` - `{ "message": "Unsubscribed successfully" }`
- `400` - `{ "message": "Missing unsubscribe_to" }`, `{ "message": "Not subscribed" }`, or `{ "message": "Cannot unsubscribe from self" }`
- `401` - `{ "message": "Missing token" }` or `{ "message": "Invalid token" }`
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred during unsubscription" }`

**Notes:**
- Removes subscription entries from both users’ MongoDB documents.

### Check User Information
```
GET /user/check_user_info?username=<username>&user_id=<user_id>
```
**Query Parameters:**
- `username` (string, optional) - Target username
- `user_id` (int, optional) - Target user ID (at least one of `username` or `user_id` is required)

**Response:**
- `200` - `{ "_id": "<mongo_id>", "username": "<string>", "user_id": <int>, "history": [], "likes": [], "Subscriber_to": [], "Subscribers": [], ... }`
- `400` - `{ "message": "Missing username" }` (if neither `username` nor `user_id` is provided)
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred during user info check" }`

**Notes:**
- Returns user data from MongoDB.

---

## Posts (`post_bp`)

### Create Post
```
POST /posts/create_post
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Form Parameters:**
- `title` (string, required) - Post title
- `content` (string, required) - Post content
- `media_file` (file, optional) - Media file upload (stored in MinIO)

**Response:**
- `200` - `{ "message": "Post created", "post_id": "<mongo_id>" }`
- `400` - `{ "message": "Title and content are required and must not be empty" }` or `{ "message": "Token is required" }`
- `401` - `{ "message": "Invalid token" }`
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred while creating the post" }`

**Notes:**
- Media files are stored in MinIO with a unique filename.

### Get Posts
```
GET /posts/get_posts?page=<int>&per_page=<int>&user_id=<int>&search=<string>
```
**Query Parameters:**
- `page` (int, optional, default: 1) - Page number
- `per_page` (int, optional, default: 10) - Posts per page
- `user_id` (int, optional) - Filter by user ID
- `search` (string, optional) - Search term for title or content

**Response:**
- `200` - `{ "posts": [<post_objects>], "pagination": { "total": <int>, "page": <int>, "per_page": <int>, "pages": <int> } }`
- `400` - `{ "message": "Page and per_page must be positive integers" }` or `{ "message": "Invalid page or per_page value" }`
- `500` - `{ "message": "An error occurred during post retrieval" }`

**Notes:**
- Posts are sorted by `created_at` in descending order.

### Get Single Post
```
GET /posts/get_post?post_id=<mongo_id>
```
**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Response:**
- `200` - `{ "post": { "_id": "<mongo_id>", "title": "<string>", "content": "<string>", "user_id": <int>, ... } }`
- `400` - `{ "message": "Post ID is required" }`
- `404` - `{ "message": "Post not found" }`
- `500` - `{ "message": "An error occurred while retrieving the post" }`

### Delete Post
```
DELETE /posts/delete_post?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Response:**
- `200` - `{ "message": "Post deleted" }`
- `400` - `{ "message": "Post ID is required" }`
- `401` - `{ "message": "Invalid token" }`
- `403` - `{ "message": "Unauthorized" }` (if not the post owner)
- `404` - `{ "message": "Post not found" }`
- `500` - `{ "message": "An error occurred while deleting the post" }`

### Update Post
```
PUT /posts/update_post?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Form Parameters:**
- `title` (string, optional) - Updated title
- `content` (string, optional) - Updated content
- `media_file` (file, optional) - New media file (replaces existing if provided)

**Response:**
- `200` - `{ "message": "Post updated" }`
- `400` - `{ "message": "Post ID is required" }` or `{ "message": "No changes provided" }`
- `401` - `{ "message": "Invalid token" }`
- `403` - `{ "message": "Unauthorized" }` (if not the post owner)
- `404` - `{ "message": "Post not found" }`
- `500` - `{ "message": "An error occurred while updating the post" }`

### Create Comment
```
POST /posts/create_comment?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Form Parameters:**
- `comment` (string, required) - Comment content

**Response:**
- `200` - `{ "message": "Comment created" }`
- `400` - `{ "message": "Post ID and comment are required and must not be empty" }`
- `401` - `{ "message": "Invalid token" }`
- `404` - `{ "message": "Post not found" }`
- `500` - `{ "message": "An error occurred while creating the comment" }`

### Get Most Read Posts Today
```
GET /posts/most_read_today
```
**Response:**
- `200` - `{ "message": "Top posts retrieved", "top_posts": [{"post_id": "<mongo_id>", "read_count": <int>}, ...] }` or `{ "message": "No posts read today", "top_posts": [] }`
- `500` - `{ "message": "An error occurred while retrieving most read posts" }`

**Notes:**
- Uses Redis to track and return the top 10 most-read posts today.

---

## History and Interactions (`history_bp`)

### Get User History and Likes
```
GET /history/get_history_like?username=<username>
```
**Query Parameters:**
- `username` (string, required) - Target username

**Response:**
- `200` - `{ "_id": "<mongo_id>", "username": "<string>", "user_id": <int>, "history": [{"post_id": "<mongo_id>", "timestamp": "<iso_date>"}, ...], "likes": [{"post_id": "<mongo_id>", "timestamp": "<iso_date>"}, ...], ... }`
- `400` - `{ "message": "Username is required" }`
- `404` - `{ "message": "User not found" }` or `{ "message": "No history found" }`
- `500` - `{ "message": "An error occurred while retrieving history" }`

### Add Read History
```
POST /history/add_read_history?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Response:**
- `200` - `{ "message": "History added" }` or `{ "message": "History timestamp updated" }`
- `400` - `{ "message": "Post ID is required" }`
- `401` - `{ "message": "Invalid token" }`
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred while updating read history" }`

**Notes:**
- Increments read count in Redis and MongoDB.

### Add Like to Post
```
POST /history/add_like?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Response:**
- `200` - `{ "message": "Post liked successfully", "already_liked": false }` or `{ "message": "You've already liked this post", "already_liked": true }`
- `400` - `{ "message": "Post ID is required" }`
- `401` - `{ "message": "Invalid token" }`
- `404` - `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred while liking the post" }`

### Remove Like from Post
```
DELETE /history/remove_like?post_id=<mongo_id>
```
**Headers:**
- `Authorization: Bearer <token>` (required) - JWT token

**Query Parameters:**
- `post_id` (string, required) - MongoDB ObjectId of the post

**Response:**
- `200` - `{ "message": "Like removed successfully" }`
- `400` - `{ "message": "Post ID is required" }`
- `401` - `{ "message": "Invalid token" }`
- `404` - `{ "message": "You haven't liked this post" }` or `{ "message": "User not found" }`
- `500` - `{ "message": "An error occurred while removing the like" }`

---

## Analytics (`analyze_bp`)

### Analyze Posts Per Day
```
GET /analyze/analyze_eachday_post?image=<boolean>
```
**Query Parameters:**
- `image` (boolean, optional, default: false) - Return a PNG image if true, JSON data if false

**Response:**
- `200` (if `image=true`) - PNG image of posts per day chart
- `200` (if `image=false`) - `{ "data": { "<YYYY-MM-DD>": <int>, ... } }`
- `500` - `{ "message": "An error occurred during analysis" }`

**Notes:**
- Uses Matplotlib to generate a line chart.

### Top Ten Users by Subscribers
```
GET /analyze/top_ten_user_subscriber?image=<boolean>
```
**Query Parameters:**
- `image` (boolean, optional, default: false) - Return a PNG image if true, JSON data if false

**Response:**
- `200` (if `image=true`) - PNG image of top users bar chart
- `200` (if `image=false`) - `{ "data": [{"username": "<string>", "subscribers": <int>}, ...] }`
- `500` - `{ "message": "An error occurred during analysis" }`

**Notes:**
- Returns only users with at least one subscriber.

---

## Error Handling

- **Standardized Responses:** All endpoints return JSON with a `message` field on errors.
- **Logging:** Errors are logged server-side with client IP and full stack traces.
- **HTTP Status Codes:** Used consistently (e.g., `400` for bad requests, `401` for unauthorized, `500` for server errors).

---

## Authentication

- Most endpoints require a JWT token in the `Authorization` header:
  ```
  Authorization: Bearer <token>
  ```
- Tokens are validated using a custom JWT implementation (assumed in `current_app.config['JWT']`).
- Invalid or expired tokens return `401 Unauthorized`.

