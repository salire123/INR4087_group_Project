from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests
import io
import logging
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

API_URL = os.getenv('API_URL')


def get_api_url(endpoint):
    return f"{API_URL}/{endpoint}"

def fetch_user_info(user_id, headers):
    """Fetch user information by user ID."""
    response = requests.get(get_api_url(f'user/check_user_info?user_id={user_id}'), headers=headers)
    return response.json().get('username', 'Unknown User') if response.status_code == 200 else 'Unknown User'

def handle_api_response(response, success_status=200):
    """Handles API responses and returns JSON or raises an error."""
    if response.status_code != success_status:
        flash(response.json().get('message', 'Error occurred'), 'danger')
        return None
    return response.json()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        app.logger.debug(f"Username: {username}, Password: {password}, Email: {email}")

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        payload = {'username': username, 'password': password, 'email': email}
        response = requests.post(get_api_url('auth/register'), data=payload)

        if handle_api_response(response, 201):
            flash('User created successfully!', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        payload = {'username': request.form['username'], 'password': request.form['password']}
        response = requests.post(get_api_url('auth/login'), data=payload)

        if response.status_code == 200:
            session['token'] = response.json()['token']
            session['username'] = request.form['username']
            return redirect(url_for('post_page'))
        else:
            flash(response.json().get('message', 'Error occurred'), 'danger')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    if 'token' in session:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.post(get_api_url('auth/logout'), headers=headers)

        if handle_api_response(response):
            flash("You have been logged out.", "success")

    session.pop('token', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/post', methods=['GET'])
def post_page():
    username = session.get('username')
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    
    # Get page and per_page from query parameters, with defaults
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)  # Set to 5 posts per page

    response = requests.get(get_api_url('posts/get_posts'), headers=headers, params={'page': page, 'per_page': per_page})
    
    posts_data = handle_api_response(response)
    posts = posts_data.get('posts', [])
    
    # Handle pagination data
    pagination = posts_data.get('pagination', {})
    total_pages = pagination.get('pages', 1)
    
    for post in posts:
        post['username'] = fetch_user_info(post['user_id'], headers)
        for comment in post.get('comments', []):
            comment['username'] = fetch_user_info(comment['user_id'], headers)

        # Add read history
        read_history_response = requests.post(get_api_url(f'history/add_read_history'), headers=headers, params={'post_id': post['_id']})
        if read_history_response.status_code != 200:
            print(f"Failed to add read history for post")

    return render_template('post.html', posts=posts, username=username, total_pages=total_pages, current_page=page)

@app.route('/personal_page', methods=['GET'])
def personal_page():
    if 'token' in session:
        username = session.get('username')
        headers = {'Authorization': f'Bearer {session.get("token")}'}
        user_id_response = requests.get(get_api_url(f'user/check_user_info?username={username}'))
        user_id = handle_api_response(user_id_response).get('user_id')
        # Get page and per_page from query parameters, with defaults
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)  # Set to 5 posts per page

        response = requests.get(get_api_url('posts/get_posts'), headers=headers, params={'user_id':user_id,'page': page, 'per_page': per_page})
        posts_data = handle_api_response(response)
        posts = posts_data.get('posts', [])
        # Handle pagination data
        pagination = posts_data.get('pagination', {})
        total_pages = pagination.get('pages', 1)

        #response = requests.get(get_api_url('posts/get_posts'), headers=headers, params={'user_id': user_id})
        posts = handle_api_response(response).get('posts', [])
        return render_template('personal_page.html', posts=posts, username=username,total_pages=total_pages, current_page=page)
    flash('You need to login to view your personal page.', 'danger')
    return redirect(url_for('login'))

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'token' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            media_file = request.files.get('media_file')

            headers = {'Authorization': f'Bearer {session.get("token")}'}
            payload = {'title': title, 'content': content}

            if media_file:
                files = {'media_file': (media_file.filename, media_file.read(), media_file.content_type)}
                response = requests.post(get_api_url('posts/create_post'), data=payload, files=files, headers=headers)
            else:
                response = requests.post(get_api_url('posts/create_post'), data=payload, headers=headers)

            if handle_api_response(response):
                flash('Post created successfully!', 'success')
                return redirect(url_for('personal_page'))

        return render_template('create_post.html')
    flash('You need to login to create a post.', 'danger')
    return redirect(url_for('login'))

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    response = requests.delete(get_api_url(f'posts/delete_post?post_id={post_id}'), headers=headers)

    if handle_api_response(response):
        flash('Post deleted successfully!', 'success')

    return redirect(url_for('personal_page'))

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    response = requests.get(get_api_url(f'posts/get_post?post_id={post_id}'), headers=headers)
    
    if response.status_code != 200:
        flash('Post not found', 'danger')
        return redirect(url_for('personal_page'))

    post = handle_api_response(response).get('post')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        media_file = request.files.get('media_file')

        payload = {'title': title, 'content': content}

        if media_file:
            files = {'media_file': (media_file.filename, media_file.read(), media_file.content_type)}
            response = requests.put(get_api_url(f'posts/update_post?post_id={post_id}'), data=payload, files=files, headers=headers)
        else:
            response = requests.put(get_api_url(f'posts/update_post?post_id={post_id}'), data=payload, headers=headers)

        if handle_api_response(response):
            flash('Post updated successfully!', 'success')
            return redirect(url_for('personal_page'))

    return render_template('edit_post.html', post=post, post_id=post_id)


@app.route('/toggle_like/<post_id>', methods=['POST'])
def toggle_like(post_id):
    if 'token' in session:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        username = session.get('username')

        # Get user's like history
        user_info_response = requests.get(get_api_url('user/check_user_info'), headers=headers, params={'username': username})

        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            liked_posts = {like['post_id'] for like in user_info.get('likes', [])}

            if post_id in liked_posts:
                # Unlike the post
                unlike_response = requests.delete(get_api_url('history/remove_like'), headers=headers, params={'post_id': post_id})

                if unlike_response.status_code == 200:
                    flash("You unliked the post!", "success")                
                else:
                    flash("An error occurred while unliking the post.", "danger")
            else:
                # Like the post
                like_response = requests.post(get_api_url('history/add_like'), headers=headers, params={'post_id': post_id})

                if like_response.status_code == 200:
                    flash("You liked the post!", "success")
                else:
                    flash("An error occurred while liking the post.", "danger")
        else:
            flash("Could not retrieve user information.", "danger")

        return redirect(url_for('view_post', post_id=post_id))
    
    flash("You need to login to like a post.", "danger")
    return redirect(url_for('login'))

@app.route('/create_comment/<post_id>', methods=['POST'])
def create_comment(post_id):
    if 'token' in session:
        comment = request.form['comment']
        payload = {'comment': comment}
        headers = {'Authorization': f'Bearer {session["token"]}'}

        response = requests.post(get_api_url('posts/create_comment'), data=payload, headers=headers, params={'post_id': post_id})

        if handle_api_response(response):
            flash("Comment added successfully!", "success")
        else:
            flash("Error adding comment.", "danger")

        return redirect(url_for('view_post', post_id=post_id))
    flash("You need to login to add a comment.", "danger")
    return redirect(url_for('login'))

@app.route('/about', methods=['GET'])
def about_page():
    username = request.args.get('username')
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    
    response = requests.get(get_api_url(f'history/get_history_like?username={username}'), headers=headers)
    user_data = handle_api_response(response)

    # Extract relevant information
    subscriber_to = user_data.get('Subscriber_to', [])
    subscribers = user_data.get('Subscribers', [])
    account_created_at = user_data.get('account_created', 'Unknown Date')
    likes = user_data.get('likes', [])

    # Fetch titles for liked posts
    liked_posts = []
    for like in likes:
        post_id = like['post_id'] 
        post_response = requests.get(get_api_url(f'posts/get_post'), headers=headers, params={'post_id': post_id})
        post_data = handle_api_response(post_response)
        if post_data:
            title = post_data['post']['title']
            liked_posts.append({'post_id': post_id, 'title': title, 'timestamp': like['timestamp']})

    user_id_response = requests.get(get_api_url(f'user/check_user_info?username={username}'))
    user_id = handle_api_response(user_id_response).get('user_id')
    posts_response = requests.get(get_api_url('posts/get_posts'), headers=headers, params={'user_id': user_id})
    user_posts = handle_api_response(posts_response).get('posts', [])

    return render_template('about.html', username=username, subscriber_to=subscriber_to, 
                           subscribers=subscribers, account_created_at=account_created_at, 
                           liked_posts=liked_posts, user_posts=user_posts)


@app.route('/toggle_subscribe', methods=['POST'])
def toggle_subscribe():
    if 'token' in session:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        username = session.get('username')        
        username_to_subscribe = request.form.get('username')
        target_user_id_response = requests.get(get_api_url(f'user/check_user_info?username={username_to_subscribe}'))
        target_user_id = handle_api_response(target_user_id_response).get('user_id')
        
        # Get user's subscription data
        user_info_response = requests.get(get_api_url('user/check_user_info'), headers=headers, params={'username': username})

        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            subscribed_users = set(user_info.get('Subscriber_to', []))

            if target_user_id in subscribed_users:
                # Unsubscribe the user
                unsubscribe_response = requests.post(get_api_url('user/unsubscribe'), headers=headers, params={'username': username_to_subscribe})

                if unsubscribe_response.status_code == 200:
                    flash("You have unsubscribed from the user!", "success")
                else:
                    flash("An error occurred while unsubscribing.", "danger")
            else:
                # Subscribe the user
                subscribe_response = requests.post(get_api_url('user/subscribe'), headers=headers, params={'username': username_to_subscribe})

                if subscribe_response.status_code == 200:
                    flash("You have subscribed to the user!", "success")
                else:
                    flash("An error occurred while subscribing."+str(subscribe_response), "danger")
        else:
            flash("Could not retrieve user information.", "danger")

        return redirect(url_for('about_page', username=username_to_subscribe))
    
    flash("You need to login to manage subscriptions.", "danger")
    return redirect(url_for('login'))


@app.route('/top', methods=['GET'])
def top_posts():
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    most_read_response = requests.get(get_api_url('posts/most_read_today'), headers=headers)
    print("most_read_response",most_read_response)
    if most_read_response.status_code != 200:
        return f"Error fetching most read posts: {most_read_response.status_code} - {most_read_response.text}", most_read_response.status_code
    print("debug1")
    most_read_data = handle_api_response(most_read_response)
    post_ids = [post['post_id'] for post in most_read_data['top_posts']]
    
    print("debug2")
    posts = []
    for post_id in post_ids:
        post_response = requests.get(get_api_url('posts/get_post'), headers=headers, params={'post_id': post_id})
        post_data = handle_api_response(post_response)

        # Add read history
        read_history_response = requests.post(get_api_url(f'history/add_read_history'), headers=headers, params={'post_id': post_id})
        if read_history_response.status_code != 200:
            print(f"Failed to add read history for post")

        if post_data:
            user_id = post_data['post']['user_id']
            post_data['username'] = fetch_user_info(user_id, headers)
            posts.append(post_data)

        

    return render_template('top.html', posts=posts)

@app.route('/viewpost/<post_id>', methods=['GET'])
def view_post(post_id):
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    post_response = requests.get(get_api_url('posts/get_post'), headers=headers, params={'post_id': post_id})

    post_data = handle_api_response(post_response)
    post = post_data.get('post')
    user_id = post['user_id']
    post['username'] = fetch_user_info(user_id, headers)

    for comment in post.get('comments', []):
        comment['username'] = fetch_user_info(comment['user_id'], headers)

    return render_template('viewpost.html', post=post)

@app.route('/search', methods=['GET'])
def search_posts():
    search_query = request.args.get('search', '')
    headers = {'Authorization': f'Bearer {session.get("token")}'}
    response = requests.get(get_api_url('posts/get_posts'), headers=headers, params={'search': search_query})

    if response.status_code != 200:
        flash("Error fetching posts.", "danger")
        return redirect(url_for('home'))

    posts_data = handle_api_response(response)
    posts = posts_data.get('posts', [])

    for post in posts:
        post['username'] = fetch_user_info(post['user_id'], headers)
        for comment in post.get('comments', []):
            comment['username'] = fetch_user_info(comment['user_id'], headers)

    return render_template('search_results.html', posts=posts, search_query=search_query)

@app.route('/analyze/posts_per_day_chart', methods=['GET'])
def posts_per_day_chart():
    try:
        response = requests.get(get_api_url('analyze/analyze_eachday_post'), params={'image': 'true'})
        
        if response.status_code != 200:
            flash("Error fetching posts per day data.", "danger")
            return redirect(url_for('home'))

        return send_file(io.BytesIO(response.content), mimetype='image1/png')

    except Exception as e:
        logging.error(f"Error fetching posts per day chart: {e}", exc_info=True)
        flash("An error occurred while generating the chart.", "danger")
        return redirect(url_for('home'))

@app.route('/about_our_web', methods=['GET'])
def about_our_web():
    return render_template('about_our_web.html')

@app.route('/analyze/top_ten_user_chart', methods=['GET'])
def top_ten_user_subscribers():
    response = requests.get(get_api_url('analyze/top_ten_user_subscriber'))
    data = response.json()
    
    # Get the list of users
    users = data.get('data', [])
    
    # Sort users based on the number of subscribers in descending order
    sorted_users = sorted(users, key=lambda x: x['subscribers'], reverse=True)
    
    # Get the top ten users
    top_users = sorted_users[:10]

    # Fill remaining slots with placeholders if there are less than 10 users
    while len(top_users) < 10:
        top_users.append({'username': 'Not Found', 'subscribers': 0})

    return render_template('top_ten_user_subscribers.html', data=top_users)



if __name__ == '__main__':
    print(f"API URL: {API_URL}")
    app.run(debug=False, host='0.0.0.0', port=os.getenv('APP_PORT', 5000))