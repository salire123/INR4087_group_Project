# API User Acceptance Testing (UAT) Plan Checklist

## Test Environment Setup

- [ ] Postman or similar API testing tool installed
- [ ] Valid user credentials for testing prepared
- [ ] Access to test environment confirmed
- [ ] Base URL configured: `http://localhost:5000` 

## 1. Authentication Tests

### Test Case 1.1: User Registration
- [ ] Send POST request to `/register` with valid user data
- [ ] Received status code 201
- [ ] Response includes "message" and "user_id"
- [ ] User ID noted: ________________

### Test Case 1.2: User Login
- [ ] Send POST request to `/login` with valid credentials
- [ ] Received status code 200
- [ ] Response includes valid token
- [ ] Token saved for subsequent tests

### Test Case 1.3: Token Renewal
- [ ] Send POST request to `/renew_token` with valid token
- [ ] Received status code 200
- [ ] Response includes new valid token
- [ ] New token saved for subsequent tests

### Test Case 1.4: User Logout
- [ ] Send POST request to `/logout` with valid token
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Token invalidated (verified by trying to use it again)

## 2. Post Management Tests

### Test Case 2.1: Create Post
- [ ] Send POST request to `/create_post` with valid token and post data
- [ ] Received status code 200
- [ ] Response includes "post_id"
- [ ] Post ID noted: ________________

### Test Case 2.2: Get Posts (List)
- [ ] Send GET request to `/get_posts` with pagination parameters
- [ ] Received status code 200
- [ ] Response includes "posts" array
- [ ] Response includes "pagination" object
- [ ] Created post appears in the list

### Test Case 2.3: Get Post (Single)
- [ ] Send GET request to `/get_post` with saved post_id
- [ ] Received status code 200
- [ ] Response includes complete post details
- [ ] Post details match what was created

### Test Case 2.4: Update Post
- [ ] Send PUT request to `/update_post` with valid token and updated data
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Get post to verify changes were applied correctly

### Test Case 2.5: Create Comment
- [ ] Send POST request to `/create_comment` with valid token and comment data
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Get post to verify comment was added successfully

### Test Case 2.6: Delete Post
- [ ] Send DELETE request to `/delete_post` with valid token and post_id
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Get post to verify it's no longer accessible

## 3. History Tests

### Test Case 3.1: Add Read History
- [ ] Create another test post (post_id: ________________)
- [ ] Send POST request to `/add_read_history` with username and post_id
- [ ] Received status code 200
- [ ] Response includes success message

### Test Case 3.2: Get History
- [ ] Send GET request to `/history/testuser123`
- [ ] Received status code 200
- [ ] Response includes "history" array
- [ ] Added post appears in history

### Test Case 3.3: Add Like
- [ ] Send POST request to `/add_like` with username and post_id
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Get post to verify like count increased

### Test Case 3.4: Remove Like
- [ ] Send POST request to `/remove_like` with username and post_id
- [ ] Received status code 200
- [ ] Response includes success message
- [ ] Get post to verify like count decreased

## 4. Error Case Tests

### Test Case 4.1: Invalid Login
- [ ] Send POST request to `/login` with incorrect password
- [ ] Received status code 400
- [ ] Response includes appropriate error message

### Test Case 4.2: Create Post Without Token
- [ ] Send POST request to `/create_post` without Authorization header
- [ ] Received status code 400
- [ ] Response includes appropriate error message

### Test Case 4.3: Access Protected Endpoint with Invalid Token
- [ ] Send POST request to `/create_post` with invalid token
- [ ] Received status code 401
- [ ] Response includes appropriate error message

## Issues Found During Testing

| Issue # | Endpoint | Description | Severity | Status |
|---------|----------|-------------|----------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Notes
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

## Test Summary

- [ ] All tests passed
- [ ] Some tests failed (see Issues Found section)
- [ ] Testing completed on: ____ / ____ / ______
- [ ] Tested by: ______________________________