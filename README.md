# Social Media Platform - Project Documentation

## Overview

This is a full-stack social media application built with a Python Flask backend and frontend. The application supports user registration, authentication, posting content with multimedia, commenting, liking, history tracking, and analytics.

## Architecture

The project follows a microservices architecture with the following components:

- **Frontend**: Flask web application that serves HTML templates and interacts with the backend API
- **Backend API**: RESTful API built with Flask providing authentication, post management, and analytics
- **Databases**:
  - MySQL: Stores user account information
  - MongoDB: Stores posts, comments, and user interaction history
  - Redis: Handles caching and real-time analytics
- **Storage**:
  - MinIO: Object storage for user-uploaded media files

## Features

- User authentication (register, login, logout)
- Create, read, update, and delete posts
- Upload images to posts
- Comment on posts
- Like/unlike posts
- User subscriptions
- User history tracking
- Analytics and data visualization
- Search functionality

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```bash
   cd int4087/project
   ```

3. Run the application using Docker Compose:
   ```bash
   cd docker
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:5000

## API Documentation

Detailed API documentation can be found in the [API Documentation](api-documentation/API_Documentation.md) file.

## Testing

The application includes a user acceptance testing (UAT) plan for comprehensive validation. See [UAT.md](api-documentation/UAT.md) for details.

## Project Structure

```
project/
├── api-documentation/    # API documentation and UAT plan
├── backend/              # Backend API source code
│   ├── src/              # Application source code
│   │   ├── routes/       # API route definitions
│   │   ├── utils/        # Utility functions
│   ├── requirements.txt  # Python dependencies
│   └── dockerfile        # Backend Docker configuration
├── frontend/             # Frontend application
│   ├── src/              # Application source code
│   │   ├── templates/    # HTML templates
│   ├── requirements.txt  # Python dependencies
│   └── dockerfile        # Frontend Docker configuration
├── docker/               # Docker configuration files
│   ├── docker-compose.yml # Container orchestration
│   ├── minio/            # MinIO configuration
│   ├── mongo/            # MongoDB configuration
│   └── mysql/            # MySQL configuration
└── test/                 # Test scripts
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## Technologies Used

- **Backend**: Python, Flask, JWT authentication
- **Frontend**: Flask, Bootstrap, HTML/CSS, JavaScript
- **Databases**: MySQL, MongoDB, Redis
- **Storage**: MinIO
- **Deployment**: Docker, Docker Compose

## License

This project is licensed under the MIT License - see the LICENSE file for details.