# Import necessary libraries for email, web scraping, file handling, logging, and subprocess execution
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import smtplib
import requests
import pandas as pd
import time
import logging
import os
import subprocess
from datetime import datetime

# Set up logging to record information, errors, and debugging messages
logging.basicConfig(filename='web_scraping_log.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Function to initiate a session and obtain cookies after logging in
def iniciar_sesion_y_obtener_cookies():
    # Configure Chrome options for Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Run Chrome in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox") # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    driver = webdriver.Chrome(options=chrome_options)
    try:
        # Navigate to the login page and log in
        driver.get("https://my.essilorluxottica.com/")
        username_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "signInName")))
        username_input.send_keys("username")
        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "continueButtonMyLux")))
        continue_button.click()
        password_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))
        password_input.send_keys("password")
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "next")))
        login_button.click()

        # Wait for the homepage to load and then get cookies
        WebDriverWait(driver, 60).until(lambda d: "https://my.essilorluxottica.com/myl-es/es-ES/homepage" in d.current_url)
        driver.get("https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-es/usercontext")
        time.sleep(5) # Wait for any dynamic data to load
        cookies = driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    except Exception as e:
        # Log any exception that occurs during the login process
        logging.exception("Error al intentar iniciar sesión y extraer cookies.")
        return None
    finally:
        # Clean up the driver by closing the browser
        driver.quit()
        logging.info("Navegador cerrado.")

# Functions for handling the processed products data
def guardar_ultimo_producto_procesado(sku):
    # Save the last processed product SKU to a file
    with open('ultimo_producto_procesado.txt', 'w') as f:
        f.write(sku)

def leer_ultimo_producto_procesado():
    # Read the last processed product SKU from a file
    try:
        with open('ultimo_producto_procesado.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Functions for formatting product names
def format_product_name_variant_1(name):
    # Format product name by replacing spaces and slashes with hyphens and adding a leading zero
    return '0' + name.replace(" ", "-").replace("/", "-").lower()

def format_product_name_variant_2(name):
    # Format product name by replacing spaces with hyphens, removing slashes, and adding a leading zero
    return '0' + name.replace(" ", "-").replace("/", "").lower()

# Function to get product data from an API endpoint
def get_product_data(product_name, cookies):
    # Call the API with two different name formatting variants and return the product data if found
    formatted_name_1 = format_product_name_variant_1(product_name)
    product_url_1 = f"https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-es/es-ES/pages/identifier/{formatted_name_1}"
    response = requests.get(product_url_1, cookies=cookies)
    if response.status_code == 200 and 'contents' in response.json()['data']:
        return response.json()
    formatted_name_2 = format_product_name_variant_2(product_name)
    product_url_2 = f"https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-es/es-ES/pages/identifier/{formatted_name_2}"
    response = requests.get(product_url_2, cookies=cookies)
    if response.status_code == 200 and 'contents' in response.json()['data']:
        return response.json()
    return None

# Function to download and convert an image
def descargar_y_convertir_imagen(url, sku):
    # Set the directory path and ensure it exists
    path_to_images = '/your/directory/'
    os.makedirs(path_to_images, exist_ok=True)
    # Sanitize the SKU and create filenames for AVIF and PNG formats
    sanitized_sku = sku.replace('/', '_').replace(' ', '_')
    file_name = f"{sanitized_sku}.avif"
    file_path = os.path.join(path_to_images, file_name)
    # Download the image and convert it to PNG
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        png_file_name = f"{sanitized_sku}.png"
        png_file_path = os.path.join(path_to_images, png_file_name)
        subprocess.run(['convert', file_path, png_file_path], check=True)
        return png_file_path
    return None

# Function to send an email notification
def send_email(subject, body, receiver_email):
    # Email configuration and sending logic
    sender_email = "test@test.com"
    password = "password"
    receiver_email = receiver_email
    smtp_server = "smtp.server.com"
    port = 465  # For SSL

    # Compose the email and send it
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP_SSL(smtp_server, port)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()

# Main workflow starts here
session_cookies = iniciar_sesion_y_obtener_cookies()
if not session_cookies:
    exit()

# Load the CSV file and prepare for processing
df = pd.read_csv('archivo.csv')
df['base_image'] = df['base_image'].astype(str)
ultimo_sku_procesado = leer_ultimo_producto_procesado()
comenzar_desde_el_principio = ultimo_sku_procesado is None
sku_to_image_path = {}

# Iterate over the dataframe and process each product

for index, row in df.iterrows():
    # Process logic for each product, including fetching product data and downloading images
    sku = row['sku']
    if comenzar_desde_el_principio or sku > ultimo_sku_procesado:
        product_name = row['name']
        if pd.isna(row['parent_sku']):
            product_data = get_product_data(product_name, session_cookies)
            if product_data:
                token = product_data['data']['contents'][0]['tokenValue']
                data_url = f"https://my.essilorluxottica.com/fo-bff/api/priv/v1/myl-es/es-ES/products/variants/{token}/attachments?type=PHOTO_360"
                data_response = requests.get(data_url, cookies=session_cookies)
                if data_response.status_code == 200:
                    data_json = data_response.json()
                    if 'attachments' in data_json.get('data', {}).get('catalogEntryView', [{}])[0]:
                        image_url = data_json['data']['catalogEntryView'][0]['attachments'][1]['attachmentAssetPath']
                        image_path = descargar_y_convertir_imagen(image_url, sku)
                        df.loc[index, 'base_image'] = image_path
                        sku_to_image_path[sku] = image_path
                        df.loc[df['parent_sku'] == sku, 'base_image'] = image_path
                else:
                    logging.error(f"Fallo al obtener imagen para {product_name}, código estado: {data_response.status_code}.")
            else:
                logging.error(f"No se obtuvieron datos para {product_name}.")
        else:
            parent_sku = row['parent_sku']
            if parent_sku in sku_to_image_path:
                df.loc[index, 'base_image'] = sku_to_image_path[parent_sku]
        guardar_ultimo_producto_procesado(sku)
        if (index + 1) % 10 == 0:
            df.to_csv('resultados_imagenes_checkpoint.csv', index=False)

# Save the final results to a CSV file
df.to_csv('resultados_imagenes_final.csv', index=False)

# Send an email notification at the end of the process
current_time = datetime.now().strftime("%H:%M:%S")
send_email(
    "Terminado extraccion datos luxottica",
    f"Ya hemos terminado con la extraccion de todas las fotos. Hora de finalización: {current_time}",
    "test@test.com"
)
