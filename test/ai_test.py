import requests
from urllib.parse import urljoin
from openai import OpenAI
import json
import time
import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from time import sleep
import traceback
import socket

# Setup logging
log_dir = './log'
os.makedirs(log_dir, exist_ok=True)  # Create log directory if it doesn't exist
log_file = os.path.join(log_dir, f'syslog.log')

# Configure logging with syslog-like format
hostname = "AI-Test"  # Default hostname if not available
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more granularity
    format=f'%(asctime)s {hostname} %(name)s[%(process)d]: %(levelname)s %(message)s',  # Syslog-like format
    datefmt='%b %d %H:%M:%S',  # e.g., "Mar 18 14:30:45"
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(base_url="https://openroute.ai/api/v1", api_key=openai_key,)

# Load API documentation (assuming it exists in the specified path)
api_documentation_path = os.path.join("..", "api-documentation", "API_Documentation.md")
with open(api_documentation_path, 'r', encoding="utf-8") as file:
    api_documentation_content = file.read()

class RestrictedAPICaller:
    def __init__(self, base_url):
        """Initialize with a specific website's base URL and optional API key"""
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'User-Agent': 'Restricted-API-Client/1.0',
            # No default Content-Type; let requests handle it
            'Authorization': None  # Will be set dynamically if an API key is provided
        }

    def call_api(self, endpoint, method='GET', params=None, data=None, api_key=None, files=None):
        logger.debug(f"Preparing API call: {method} {endpoint} with params={params}, data={data}")
        try:
            full_url = urljoin(self.base_url, endpoint.lstrip('/'))
            if not full_url.startswith(self.base_url):
                logger.error(f"Endpoint outside domain: {endpoint}")
                return {"error": "Endpoint must stay within the specified website domain"}

            response = self._execute_request(full_url, method, params, data, api_key=api_key, files=files)
            response.raise_for_status()
            try:
                result = response.json()
                logger.info(f"API call succeeded: {method} {endpoint} - Response: {json.dumps(result)}")
                return result
            except json.JSONDecodeError:
                result = response.text
                logger.info(f"API call succeeded (non-JSON): {method} {endpoint} - Response: {result}")
                return result
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {method} {endpoint} - Error: {str(e)}")
            return {"error": f"API call failed: {str(e)}"}

    def _execute_request(self, url, method, params, data, files=None, api_key=None):
        method = method.upper()
        logger.debug(f"Executing request: {method} {url} with params={params}, data={data}")
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                if files:
                    # Ensure files is in the correct format (e.g., {'file': open(filepath, 'rb')})
                    response = requests.post(url, headers=self.headers, params=params, data=data)
                else:
                    response = requests.post(url, headers=self.headers, params=params, data=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, params=params, data=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params, data=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.debug(f"Request: {method} {url} - Headers: {self.headers} - Params: {params} - Data: {data} - Files: {files} ")
            logger.debug(f"Response: {response.status_code} - Headers: {response.headers} - Content: {response.text}")

            # Parse the JSON response and extract the token if it exists
            try:
                response_data = response.json()  # Convert JSON string to dictionary
                api_key = response_data.get("token")  # Safely get the token (returns None if not found)
            except json.JSONDecodeError:
                # If response is not JSON, log it and leave api_key as None
                logger.warning(f"Response is not JSON: {response.text}")
                api_key = None

            if api_key:
                self.headers['Authorization'] = f"Bearer {api_key}"
                logger.info(f"Using provided API key: {api_key}")

            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - Error: {str(e)}")
            raise

def generate_user_api_call(base_url, user_email, call_history, call_number, token=None, last_call=False):
    """Generate a single API call with memory of previous calls, handling unstable AI."""
    if last_call:
        logger.debug(f"Generating API call for last call with token: {token}")
        last_call_text = "you must logout now if you can"
    else:
        last_call_text = ""


    token_text = f'"{token}"' if token else "null"
    prompt = f"""
    You are simulating a user browsing a website with the base URL: {base_url}.
    The user’s email is {user_email}. This is call number {call_number} out of 30. password is password123
    Generate a single API call to mimic realistic browsing behavior, using the context
    of previous calls and responses below. Include the user’s email in relevant params
    or data where appropriate (e.g., for login, profile, or posts). Restrict the call
    to the base URL.

    Here is the API documentation for the website:
    {api_documentation_content}

    Previous Calls and Responses:
    {json.dumps(call_history, indent=2)}


    Examples of browsing behavior:
    - GET /products (view products)
    - GET /products/{{id}} (view specific product from previous list)
    - POST /comments (post a comment on a product)
    - GET /search?q=query (search based on previous results)

    Return the result as a raw JSON object (do not wrap it in Markdown code blocks like ```json):
    {{
        "endpoint": "/path",
        "method": "GET|POST|PUT|DELETE",
        "params": {{"key": "value"}} or null,
        "data": {{"key": "value"}} or null
    }}

    file you can upload:
    - .\\2_20250317062136_Screenshot 2024-09-24 094054.png

    token:
    {token_text}

    {last_call_text}
    """
    max_retries = 15  # Increased retries for unstable free model
    for attempt in range(max_retries):
        logger.debug(f"Attempt {attempt + 1}/{max_retries} to generate API call for {user_email}, call {call_number}")
        try:
            # Increase timeout to 30 seconds
            response = openai_client.chat.completions.create(
                extra_body={},
                model="google/gemma-3-1b-it:free",
                messages=[{"role": "user", "content": prompt}],
                timeout=30  # Add timeout parameter if supported, or handle via requests
            )

            #logger.debug(f"Raw OpenAI response: {response}") # too much data
            api_call_text = response.choices[0].message.content
            logger.debug(f"Raw API call text: {repr(api_call_text)}")
            
            # Clean potential Markdown or extra whitespace
            cleaned_text = api_call_text.strip().removeprefix("```json").removesuffix("```").strip()
            logger.debug(f"Cleaned API call text: {repr(cleaned_text)}")
            
            # Check if response is empty or incomplete
            if not cleaned_text or "{" not in cleaned_text or "}" not in cleaned_text:
                logger.warning(f"Attempt {attempt + 1} returned incomplete response: {repr(cleaned_text)}")
                if attempt == max_retries - 1:
                    raise ValueError("Failed to generate a valid API call")
                sleep(1)  # Wait longer before retrying
                continue
            
            api_call = json.loads(cleaned_text)
            logger.info(f"Successfully parsed API call: {json.dumps(api_call)}")
            return api_call
            
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Attempt {attempt + 1} failed - Error: {str(e)} - Raw text: {repr(api_call_text if 'api_call_text' in locals() else 'No response')}")
            if attempt == max_retries - 1:
                raise 
            sleep(1)  # Increased delay for retries

def simulate_user_browsing_with_memory():
    base_url = "http://localhost:5000"
    api_client = RestrictedAPICaller(base_url)
    token = {}
    
    eveyuser_run_set = 2
    num_users = 3
    calls_per_set = 10
    
    for run_set in range(1, eveyuser_run_set + 1):
        logger.info(f"Starting Time Set {run_set} for {num_users} users")
        for user_id in range(1, num_users + 1):
            user_email = f"testuser{user_id}@email.com"
            logger.info(f"Starting user simulation for {user_email} in Time Set {run_set}")
            
            call_history = []
            
            for i in range(1, calls_per_set + 1):
                logger.info(f"Generating Call {i}/{calls_per_set} for {user_email}")

                token_text = token.get(user_email)
                if not token_text:
                    logger.debug(f"No token found for {user_email}")
                
                api_call = generate_user_api_call(
                    base_url, 
                    user_email, 
                    call_history, 
                    i, 
                    token=token_text, 
                    last_call=(i == calls_per_set)
                )
                
                
                if isinstance(api_call, dict) and "error" in api_call:
                    logger.error(f"Error generating API call: {api_call}")
                    break
                
                logger.debug(f"Generated API call: {json.dumps(api_call, indent=2)}")

                if "token" in api_call:
                    token[user_email] = api_call["token"]
                    logger.info(f"Updated token for {user_email}: {token[user_email]}")

                endpoint_base = api_call["endpoint"].split("?")[0]
                files = None
                
                # Handle file upload with try-except
                try:
                    if endpoint_base in ["/posts/update_post", "/posts/create_post"]:
                        file_path = ".\\2_20250317062136_Screenshot 2024-09-24 094054.png"
                        if os.path.exists(file_path):
                            files = {"file": open(file_path, "rb")}
                        else:
                            logger.warning(f"File not found: {file_path}")
                            continue

                    result = api_client.call_api(
                        endpoint=api_call["endpoint"],
                        method=api_call.get("method", "GET"),
                        params=api_call.get("params"),
                        data=api_call.get("data"),
                        files=files
                    )
                    
                    call_entry = {"call": api_call, "response": result}
                    call_history.append(call_entry)
                    
                    print(f"Call {i}/{calls_per_set} - {api_call['method']} {api_call['endpoint']}")
                    print(json.dumps(result, indent=2))
                    print("-" * 30)
                    
                except Exception as e:
                    logger.error(f"Error in API call: {str(e)}")
                finally:
                    if files and "file" in files:
                        files["file"].close()
                
                time.sleep(2)
            
            logger.info(f"Completed simulation for {user_email} in Time Set {run_set}")
            if user_id < num_users:
                logger.info("Waiting before next user...")
                time.sleep(5)

if __name__ == "__main__":
    try:
        logger.info("-"*30)
        logger.info("Starting user browsing simulation...")
        simulate_user_browsing_with_memory()
    except Exception as e:
        logger.error(f"An error occurred: {traceback.format_exc()}")
        raise