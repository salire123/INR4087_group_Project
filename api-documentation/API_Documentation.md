# API Documentation for Backend Routes

## Overview

This documentation covers the backend routes for the social media platform. The API is organized into several modules:

- **Authentication** - User registration, login, and token management
- **User Management** - User subscriptions and information
- **Posts** - Creating, retrieving, updating, and deleting posts
- **History** - User reading history and post interactions
- **Analytics** - Data visualization and user metrics

## Authentication (`auth_bp`)

### Register a new user
```
POST /auth/register
```
**Form Parameters:**
- `username` - Unique username
- `password` - User's password
- `email` - User's email address

**Response:**
- `201` - User successfully created
- `400` - User or email already exists
- `500` - Server error

### Login
```
POST /auth/login
```
**Form Parameters:**
- `username` - Username
- `password` - User's password

**Headers (optional):**
- `Authorization: Bearer <token>` - For already authenticated users

**Response:**
- `200` - Successful login with JWT token
- `400` - Invalid password
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Logout
```
POST /auth/logout
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Response:**
- `200` - Successfully logged out
- `401` - Missing or invalid token
- `500` - Server error

### Renew Token
```
POST /auth/renew_token
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Response:**
- `200` - New token provided
- `401` - Missing or invalid token
- `500` - Server error

## User Management (`user_bp`)

### Subscribe to a User
```
POST /user/subscribe
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Form Parameters:**
- `subscribe_to` - Username to subscribe to

**Response:**
- `200` - Successfully subscribed
- `400` - Already subscribed or missing parameters
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Unsubscribe from a User
```
POST /user/unsubscribe
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Form Parameters:**
- `unsubscribe_to` - Username to unsubscribe from

**Response:**
- `200` - Successfully unsubscribed
- `400` - Not subscribed or missing parameters
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Check User Information
```
GET /user/check_user_info?username=<username>
```
**Query Parameters:**
- `username` - Target username

**Response:**
- `200` - User information
- `400` - Missing username
- `404` - User not found
- `500` - Server error

## Posts (`post_bp`)

### Create Post
```
POST /posts/create_post
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Form Parameters:**
- `title` - Post title
- `content` - Post content
- `media_file` - Optional file upload

**Response:**
- `200` - Post created successfully with post_id
- `400` - Missing required fields
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Get Posts
```
GET /posts/get_posts
```
**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Posts per page (default: 10)
- `user_id` - Filter by user (optional)
- `search` - Search term (optional)

**Response:**
- `200` - List of posts with pagination info
- `400` - Invalid pagination parameters
- `500` - Server error

### Get Single Post
```
GET /posts/get_post?post_id=<post_id>
```
**Query Parameters:**
- `post_id` - Post identifier

**Response:**
- `200` - Post details
- `400` - Missing post ID
- `404` - Post not found
- `500` - Server error

### Delete Post
```
DELETE /posts/delete_post?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Response:**
- `200` - Post deleted
- `400` - Missing parameters
- `401` - Invalid token
- `403` - Not post owner
- `404` - Post not found
- `500` - Server error

### Update Post
```
PUT /posts/update_post?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Form Parameters:**
- `title` - Updated title (optional)
- `content` - Updated content (optional)
- `media_file` - New media file (optional)

**Response:**
- `200` - Post updated
- `400` - Missing parameters or no changes
- `401` - Invalid token
- `403` - Not post owner
- `404` - Post not found
- `500` - Server error

### Create Comment
```
POST /posts/create_comment?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Form Parameters:**
- `comment` - Comment content

**Response:**
- `200` - Comment created
- `400` - Missing parameters
- `401` - Invalid token
- `404` - Post or user not found
- `500` - Server error

### Get Most Read Posts Today
```
GET /posts/most_read_today
```
**Response:**
- `200` - List of most-read posts
- `500` - Server error

## History and Interactions (`history_bp`)

### Get User History and Likes
```
GET /history/get_history_like?username=<username>
```
**Query Parameters:**
- `username` - Target username

**Response:**
- `200` - User's history and likes
- `404` - User not found or no history
- `500` - Server error

### Add Read History
```
POST /history/add_read_history?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Response:**
- `200` - History added or timestamp updated
- `400` - Missing parameters
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Add Like to Post
```
POST /history/add_like?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Response:**
- `200` - Like added or already liked
- `400` - Missing parameters
- `401` - Invalid token
- `404` - User not found
- `500` - Server error

### Remove Like from Post
```
DELETE /history/remove_like?post_id=<post_id>
```
**Headers:**
- `Authorization: Bearer <token>` - Required

**Query Parameters:**
- `post_id` - Post identifier

**Response:**
- `200` - Like removed
- `400` - Missing parameters
- `401` - Invalid token
- `404` - User not found or post not liked
- `500` - Server error

## Analytics (`analyze_bp`)

### Analyze Posts Per Day
```
GET /analyze/analyze_eachday_post
```
**Response:**
- `200` - PNG image of posts per day chart
- `500` - Server error

### Top Ten Users by Subscribers
```
GET /analyze/top_ten_user_subscriber
```
**Response:**
- `200` - PNG image of top users chart
- `500` - Server error

## Error Handling

All API endpoints follow a consistent error handling pattern:
- Detailed server-side logging with client IP address
- Standardized JSON error responses with appropriate HTTP status codes
- Comprehensive exception handling with full stack traces in logs

## Authentication

Most endpoints require authentication via JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Invalid tokens or expired sessions will result in a `401 Unauthorized` response.
