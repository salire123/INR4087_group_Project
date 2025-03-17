Below is a step-by-step User Acceptance Testing (UAT) plan for the Flask application API, designed for a new environment with no existing data. This plan tests all endpoints in a logical sequence, building upon previous steps to ensure comprehensive validation of the API's functionality. We'll use Postman (or a similar tool) to send requests and verify responses.

---

# User Acceptance Testing (UAT) Plan

**Objective:** Validate the functionality of all API endpoints in a new environment with no pre-existing data.

**Prerequisites:**
- The Flask application is deployed and running.
- MySQL (for user data), MongoDB (for posts and history), and MinIO (for media storage) are set up and connected to the application.
- Postman or a similar API testing tool is installed and ready.
- Base URL: Replace `<your-domain-or-ip>:<port>` with the actual server address (e.g., `http://localhost:5000`).

---

## Test Steps

### 1. Register a New User
**Purpose:** Create a new user account to enable further testing.

- **Endpoint:** `/register`
- **Method:** `POST`
- **Steps:**
  1. Open Postman.
  2. Set the request method to `POST`.
  3. Enter the URL: `http://<your-domain-or-ip>:<port>/register`.
  4. Set the content type to `multipart/form-data` (in the "Body" tab, select "form-data").
  5. Add the following key-value pairs:
     - `username`: "testuser"
     - `password`: "password123"
     - `email`: "testuser@example.com"
  6. Click "Send".
- **Expected Result:**
  - **Status:** `201 Created`
  - **Response:**
    ```json
    {"message": "User created successfully", "user_id": 1}
    ```
- **Notes:** The `user_id` may vary depending on the database; save it if needed.

---

### 2. Login with the New User
**Purpose:** Authenticate the user and obtain a JWT token for authorized requests.

- **Endpoint:** `/login`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/login`.
  3. Set the content type to `multipart/form-data`.
  4. Add the following key-value pairs:
     - `username`: "testuser"
     - `password`: "password123"
  5. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"token": "<jwt_token>"}
    ```
- **Notes:** Copy the `<jwt_token>` from the response; it will be used in subsequent steps requiring authorization.

---

### 3. Create a New Post
**Purpose:** Test post creation with optional media upload.

- **Endpoint:** `/create_post`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/create_post`.
  3. Set the content type to `multipart/form-data`.
  4. Add the following key-value pairs:
     - `title`: "My First Post"
     - `content`: "This is the content of my first post."
     - (Optional) `media_file`: Click the "Value" dropdown, select "File", and upload a sample image (e.g., `test.jpg`).
  5. Go to the "Headers" tab and add:
     - Key: `Authorization`
     - Value: `Bearer <jwt_token>` (use the token from step 2).
  6. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Post created", "post_id": "<post_id>"}
    ```
- **Notes:** The `<post_id>` will be a MongoDB ObjectId (e.g., `507f1f77bcf86cd799439011`). Save it for later steps.

---

### 4. Get Posts
**Purpose:** Retrieve the list of posts to verify the post was created.

- **Endpoint:** `/get_posts`
- **Method:** `GET`
- **Steps:**
  1. In Postman, set the request method to `GET`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/get_posts`.
  3. (Optional) Add query parameters in the "Params" tab:
     - `page`: `1`
     - `per_page`: `10`
     - `search`: "first"
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {
      "posts": [
        {
          "_id": "<post_id>",
          "title": "My First Post",
          "content": "This is the content of my first post.",
          "user_id": 1,
          "media_url": "<minio_url_if_uploaded>",
          "comments": [],
          "comment_count": 0,
          "created_at": "2025-03-17T<time>Z"
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
- **Notes:** Verify the post from step 3 appears. If a media file was uploaded, check the `media_url`.

---

### 5. Get a Single Post
**Purpose:** Retrieve details of the specific post created.

- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Steps:**
  1. In Postman, set the request method to `GET`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/get_post?post_id=<post_id>` (use the `<post_id>` from step 3).
  3. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {
      "post": {
        "_id": "<post_id>",
        "title": "My First Post",
        "content": "This is the content of my first post.",
        "user_id": 1,
        "media_url": "<minio_url_if_uploaded>",
        "comments": [],
        "comment_count": 0,
        "created_at": "2025-03-17T<time>Z"
      }
    }
    ```

---

### 6. Add a Comment to the Post
**Purpose:** Test adding a comment to the post.

- **Endpoint:** `/create_comment`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/create_comment?post_id=<post_id>`.
  3. Set the content type to `multipart/form-data`.
  4. Add the key-value pair:
     - `comment`: "This is a test comment."
  5. Add the `Authorization` header: `Bearer <jwt_token>`.
  6. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Comment created"}
    ```

---

### 7. Verify Comment in Post Details
**Purpose:** Confirm the comment was added to the post.

- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Steps:**
  1. Repeat step 5 (use the same URL: `http://<your-domain-or-ip>:<port>/get_post?post_id=<post_id>`).
  2. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:** The `comments` array should now include:
    ```json
    {
      "post": {
        "_id": "<post_id>",
        "title": "My First Post",
        "content": "This is the content of my first post.",
        "user_id": 1,
        "media_url": "<minio_url_if_uploaded>",
        "comments": [
          {
            "user_id": 1,
            "comment": "This is a test comment.",
            "created_at": "2025-03-17T<time>Z"
          }
        ],
        "comment_count": 1,
        "created_at": "2025-03-17T<time>Z"
      }
    }
    ```

---

### 8. Add Read History
**Purpose:** Add the post to the user's read history.

- **Endpoint:** `/add_read_history`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/add_read_history?post_id=<post_id>`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "History added"}
    ```
    *(If repeated, expect: `{"message": "History timestamp updated"}`)*

---

### 9. Add a Like to the Post
**Purpose:** Test liking the post.

- **Endpoint:** `/add_like`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/add_like?post_id=<post_id>`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Post liked successfully", "already_liked": false}
    ```

---

### 10. Get User History and Likes
**Purpose:** Verify the user's read history and likes.

- **Endpoint:** `/get_history_like`
- **Method:** `GET`
- **Steps:**
  1. In Postman, set the request method to `GET`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/get_history_like?username=testuser`.
  3. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {
      "_id": "<history_id>",
      "user_id": 1,
      "history": [
        {"post_id": "<post_id>", "timestamp": "2025-03-17T<time>Z"}
      ],
      "likes": [
        {"post_id": "<post_id>", "timestamp": "2025-03-17T<time>Z"}
      ]
    }
    ```

---

### 11. Remove Like from the Post
**Purpose:** Test removing the like from the post.

- **Endpoint:** `/remove_like`
- **Method:** `DELETE`
- **Steps:**
  1. In Postman, set the request method to `DELETE`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/remove_like?post_id=<post_id>`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Like removed successfully"}
    ```

---

### 12. Update the Post
**Purpose:** Test updating the post's title and content.

- **Endpoint:** `/update_post`
- **Method:** `PUT`
- **Steps:**
  1. In Postman, set the request method to `PUT`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/update_post?post_id=<post_id>`.
  3. Set the content type to `multipart/form-data`.
  4. Add the following key-value pairs:
     - `title`: "Updated Post Title"
     - `content`: "Updated content."
     - (Optional) `media_file`: Upload a new sample file (e.g., `new_test.jpg`).
  5. Add the `Authorization` header: `Bearer <jwt_token>`.
  6. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Post updated"}
    ```

---

### 13. Verify Updated Post
**Purpose:** Confirm the post reflects the updates.

- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Steps:**
  1. Repeat step 5 (use `http://<your-domain-or-ip>:<port>/get_post?post_id=<post_id>`).
  2. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:** The post should show the updated title and content:
    ```json
    {
      "post": {
        "_id": "<post_id>",
        "title": "Updated Post Title",
        "content": "Updated content.",
        "user_id": 1,
        "media_url": "<new_minio_url_if_uploaded>",
        "comments": [
          {
            "user_id": 1,
            "comment": "This is a test comment.",
            "created_at": "2025-03-17T<time>Z"
          }
        ],
        "comment_count": 1,
        "created_at": "2025-03-17T<time>Z"
      }
    }
    ```

---

### 14. Delete the Post
**Purpose:** Test deleting the post.

- **Endpoint:** `/delete_post`
- **Method:** `DELETE`
- **Steps:**
  1. In Postman, set the request method to `DELETE`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/delete_post?post_id=<post_id>`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "Post deleted"}
    ```

---

### 15. Verify Post Deletion
**Purpose:** Ensure the post no longer exists.

- **Endpoint:** `/get_post`
- **Method:** `GET`
- **Steps:**
  1. Repeat step 5 (use `http://<your-domain-or-ip>:<port>/get_post?post_id=<post_id>`).
  2. Click "Send".
- **Expected Result:**
  - **Status:** `404 Not Found`
  - **Response:**
    ```json
    {"message": "Post not found"}
    ```

---

### 16. Logout
**Purpose:** Invalidate the user's token.

- **Endpoint:** `/logout`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/logout`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"message": "User logged out successfully"}
    ```

---

### 17. Renew Token (Optional)
**Purpose:** Test renewing the JWT token (before logout, if desired).

- **Endpoint:** `/renew_token`
- **Method:** `POST`
- **Steps:**
  1. In Postman, set the request method to `POST`.
  2. Enter the URL: `http://<your-domain-or-ip>:<port>/renew_token`.
  3. Add the `Authorization` header: `Bearer <jwt_token>`.
  4. Click "Send".
- **Expected Result:**
  - **Status:** `200 OK`
  - **Response:**
    ```json
    {"token": "<new_jwt_token>"}
    ```
- **Notes:** Perform this step before logout if you want to test token renewal.

---

## Additional Notes
- **Error Testing:** Optionally, test error scenarios (e.g., invalid tokens, missing parameters, unauthorized actions) to verify proper error handling.
- **Media Uploads:** Ensure MinIO is accessible and media files are stored correctly; check `media_url` in responses.
- **Environment Setup:** If the application requires initial configuration (e.g., database schema creation), ensure it’s completed before testing.
- **Timestamps:** Responses include timestamps (e.g., `2025-03-17T<time>Z`); these will reflect the current date and time.

This UAT plan systematically tests all API endpoints, starting from a clean slate, ensuring the Flask application works as expected in a new environment. Let me know if you need further clarification or additional test cases!