# Databricks notebook source
# MAGIC %md
# MAGIC #Configure configuration properties
# MAGIC ---
# MAGIC
# MAGIC ## **Add desired catalog name, schema name and volume name in the config file**
# MAGIC ## 
# MAGIC Defaults are:
# MAGIC
# MAGIC catalog = "dbdemos_agent_email_image"
# MAGIC dbName = db = "dbdemos_agent_email_image_schema"
# MAGIC volume_name = "dbdemos_agent_email_image_volume"
# MAGIC secret_scope = "dbdemos"
# MAGIC
# MAGIC ## **Make sure you configure secrets:**
# MAGIC ## 
# MAGIC For best security and reproducibility the functions use Databricks secrets to get Token and other values, `if you change any name of the scope or secret below, please also change in the config file before running`
# MAGIC
# MAGIC Open a terminal from your cluster
# MAGIC Create the scope: `databricks secrets create-scope dbdemos`
# MAGIC
# MAGIC Add your token in the scope: `databricks secrets put-secret --json '{
# MAGIC   "scope": "dbdemos",
# MAGIC   "key": "llm-agent-tools-email-image-token",
# MAGIC   "string_value": "<your pat token here>"
# MAGIC }
# MAGIC
# MAGIC Add your token in the scope: `databricks secrets put-secret --json '{
# MAGIC   "scope": "dbdemos",
# MAGIC   "key": "llm-agent-tools-email-image-host",
# MAGIC   "string_value": "<your host (xxxxxx.cloud.databricks.com) here>"
# MAGIC }
# MAGIC
# MAGIC Add your token in the scope: `databricks secrets put-secret --json '{
# MAGIC   "scope": "dbdemos",
# MAGIC   "key": "llm-agent-tools-email-image-sender-email",
# MAGIC   "string_value": "<your email (xxx@gmail.com) here>"
# MAGIC }
# MAGIC
# MAGIC Add your token in the scope: `databricks secrets put-secret --json '{
# MAGIC   "scope": "dbdemos",
# MAGIC   "key": "llm-agent-tools-email-image-sender-password",
# MAGIC   "string_value": "<your email password here>"
# MAGIC }
# MAGIC
# MAGIC Add your token in the scope: `databricks secrets put-secret --json '{
# MAGIC   "scope": "dbdemos",
# MAGIC   "key": "llm-agent-tools-email-image-receiver-email",
# MAGIC   "string_value": "<your email receiver (can use quotes to include more) here>"
# MAGIC }
# MAGIC

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

spark.sql(f"""CREATE OR REPLACE FUNCTION {catalog}.{dbName}.product_rating_average_by_category (
  state STRING
  COMMENT 'Customer state. Example: "SP"'
)
RETURNS TABLE (
  product_category_name STRING,
  average_rating_score DOUBLE
)
COMMENT 'Returns the average rating score by product category for a given state, catalog, and schema.
Example of use: SELECT * FROM dbdemos_agent_email_image.agent_demo.product_rating_average_by_category("SP")'
RETURN
  SELECT
    p.product_category_name AS product_category_name,
    AVG(r.review_score) AS average_rating_score
  FROM
    {catalog}.{dbName}.order_reviews_dataset r
    JOIN {catalog}.{dbName}.orders_dataset o ON r.order_id = o.order_id
    JOIN {catalog}.{dbName}.customers_dataset c ON o.customer_id = c.customer_id
    JOIN {catalog}.{dbName}.order_items_dataset i ON o.order_id = i.order_id
    JOIN {catalog}.{dbName}.products_dataset p ON i.product_id = p.product_id
  WHERE
    c.customer_state = product_rating_average_by_category.state
  GROUP BY
    p.product_category_name
  ORDER BY
    average_rating_score DESC;
""")

# COMMAND ----------

spark.sql(f"""CREATE OR REPLACE FUNCTION {catalog}.{dbName}.products_quantity_by_state ()
RETURNS TABLE (
  state STRING,
  products_quantity BIGINT
)
COMMENT 'Returns the quantity of products sold by state.
Example of use: SELECT * FROM dbdemos_agent_email_image.agent_demo.products_quantity_by_state()'
RETURN
  SELECT
    c.customer_state AS state,
    COUNT(i.product_id) AS products_quantity
  FROM
    {catalog}.{dbName}.orders_dataset o
    JOIN {catalog}.{dbName}.customers_dataset c ON o.customer_id = c.customer_id
    JOIN {catalog}.{dbName}.order_items_dataset i ON o.order_id = i.order_id
    JOIN {catalog}.{dbName}.products_dataset p ON i.product_id = p.product_id
  GROUP BY
    c.customer_state 
  ORDER BY
    products_quantity DESC;
""")

# COMMAND ----------

# MAGIC %md
# MAGIC **For the functions below, make sure you've configured the secrets properly and correct names input on the config file**
# MAGIC
# MAGIC

# COMMAND ----------

sql_statement = f"""
CREATE OR REPLACE FUNCTION {catalog}.{dbName}.generate_images_with_secrets (
  best_category STRING
  COMMENT 'Category with the best reviews. Example: "electronics"',
  worst_category STRING
  COMMENT 'Category with the worst reviews. Example: "furniture"',
  databricks_token STRING
  COMMENT 'token passed via a secret',
  databricks_host STRING
  COMMENT 'host passed via a secret'
)
RETURNS STRUCT<image_paths: ARRAY<STRING>, prompt_image: STRING, best_category: STRING, worst_category: STRING>
COMMENT 'Generates images of an innovative product combining the provided categories and saves it in a Databricks Volume. This functions needs to be called by the wrapper function and not directly 
Example of use: select dbdemos_agent_email_image.dbdemos_agent_email_image_schema.generate_images_with_secrets("electronics", "furniture", secret("dbdemos", "llm-agent-tools-email-image-token"),secret("dbdemos", "llm-agent-tools-email-image-host") )'
LANGUAGE PYTHON
AS $$
import requests
import os
import base64
import json
from databricks.sdk import WorkspaceClient

def generate_images(best_category, worst_category, databricks_token, databricks_host):
    w = WorkspaceClient(host=databricks_host, token=databricks_token)
    
    BASE_URL = f"https://{{databricks_host}}/serving-endpoints"
    
    HEADERS = {{
        "Authorization": f"Bearer {{databricks_token}}",
        "Content-Type": "application/json"
    }}

    def make_api_call(endpoint, payload):
        response = requests.post(f"{{BASE_URL}}/{{endpoint}}/invocations", headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()

    def upload_to_volume(file_content, file_path):
        url = f"https://{{databricks_host}}/api/2.0/fs/files{{file_path}}"
        headers = {{
            "Authorization": f"Bearer {{databricks_token}}",
            "Content-Type": "application/octet-stream"
        }}
        response = requests.put(url, headers=headers, data=file_content)

    prompt_llama = f"Generate a prompt in English to be used for generating an AI image of a product design from the category {{worst_category}} but that is highly related to the category {{best_category}}"
    llama_payload = {{
        "messages": [{{"role": "user", "content": prompt_llama}}],
        "max_tokens": 256
    }}
    llama_response = make_api_call("databricks-meta-llama-3-1-70b-instruct", llama_payload)
    prompt_image = llama_response['choices'][0]['message']['content']

    image_payload = {{
        "prompt": prompt_image,
        "n": 4,
        "seed": 42,
        "size": "square"
    }}
    image_response = make_api_call("databricks-shutterstock-imageai", image_payload)
    images_data = [i['b64_json'] for i in image_response['data']]

    volume_base_path = "/Volumes/{catalog}/{dbName}/{volume_name}/generated_images"
    image_paths = []
    for i, img_data in enumerate(images_data):
        img_bytes = base64.b64decode(img_data)
        file_path = f"{{volume_base_path}}/image_{{i+1}}.jpg"
        upload_to_volume(img_bytes, file_path)
        image_paths.append(file_path)

    return (image_paths, prompt_image, best_category, worst_category)

return generate_images(best_category, worst_category, databricks_token, databricks_host)
$$


;
"""

spark.sql(sql_statement)




# COMMAND ----------

# MAGIC %md
# MAGIC Wrapper function, if you changed the name of the scope and/or secret you need to also change here

# COMMAND ----------

# Create the SQL statement with the variables
sql_statement = f"""
CREATE OR REPLACE FUNCTION {catalog}.{dbName}.generate_images (
  best_category STRING,
  worst_category STRING
)
RETURNS STRUCT<image_paths: ARRAY<STRING>, prompt_image: STRING, best_category: STRING, worst_category: STRING>
LANGUAGE SQL
COMMENT 'Wrapper function that calls generate_images_with_secrets with fixed secrets.
Example of use: SELECT {catalog}.{dbName}.generate_images("electronics", "furniture")'
RETURN 
  SELECT generate_images_with_secrets(
    best_category,
    worst_category,
    secret("{secret_scope}", "{email_image_token}"),
    secret("{secret_scope}", "{email_image_host}")
  )
;
"""

# Execute the SQL statement
spark.sql(sql_statement)

# COMMAND ----------

# MAGIC %md
# MAGIC **Send Email Function:**
# MAGIC
# MAGIC  `Note that this function uses Gmail as smpt`
# MAGIC

# COMMAND ----------

# Create the SQL statement with the variables
sql_statement = f"""
CREATE OR REPLACE FUNCTION {catalog}.{dbName}.send_email_with_secrets (
  image_paths ARRAY<STRING>,
  prompt_image STRING,
  best_category STRING,
  worst_category STRING,
  databricks_token STRING,
  databricks_host STRING,
  sender_email STRING,
  sender_password STRING,
  receiver_email STRING
)
RETURNS STRING
COMMENT 'Sends an email with the generated images and description. This functions needs to be called by the wrapper function and not directly 
Example of use: SELECT {catalog}.{dbName}.send_email_with_secrets(array("/Volumes/{catalog}/{dbName}/generated_images/image_1.jpg", "/Volumes/{catalog}/{dbName}/generated_images/image_2.jpg", "/Volumes/{catalog}/{dbName}/generated_images/image_3.jpg", "/Volumes/{catalog}/{dbName}/generated_images/image_4.jpg"), "PROMPT THAT GENERATED THE IMAGE", "category1", "category2", secret("dbdemos", "llm-agent-tools-email-image-token"), secret("dbdemos", "llm-agent-tools-email-image-host"), secret("dbdemos", "sender-email"), secret("dbdemos", "sender-password"), secret("dbdemos", "receiver-email"))'
LANGUAGE PYTHON
AS
$$
import requests
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

def send_email(image_paths, prompt_image, best_category, worst_category, databricks_token, databricks_host, sender_email, sender_password, receiver_email):
    BASE_URL = f"https://{{databricks_host}}/serving-endpoints"
    DATABRICKS_INSTANCE = databricks_host
    HEADERS = {{
        "Authorization": f"Bearer {{databricks_token}}",
        "Content-Type": "application/json"
    }}

    def make_api_call(endpoint, payload):
        response = requests.post(f"{{BASE_URL}}/{{endpoint}}/invocations", headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()

    def download_file(file_path):
        url = f"https://{{DATABRICKS_INSTANCE}}/api/2.0/fs/files{{file_path}}"
        headers = {{
            "Authorization": f"Bearer {{databricks_token}}"
        }}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content

    email_body_prompt = f'''Create an email in English to present a new product idea aimed at boosting our company\'s sales. Use the category with the worst reviews, {{worst_category}}, and create a product related to the category with the best reviews, {{best_category}}. The product description is: {{prompt_image}}.

    The email should contain the following sections, all formatted in HTML:

    1. Email subject (use the <subject> tag)
    2. Initial greeting
    3. Brief introduction
    4. Product name and description
    5. Reason for product creation
    6. Technical specifications
    7. Conclusion
    8. Farewell
    9. Signature as "Innovation and AI Team"

    The email needs to look like a real corporate email. Do not sound like a machine. Do not put sessions like "Introduction" or "Conclusion", give names that sound natural in a company email.

    Use the following formatting guidelines:
    - Use <h2> for section titles
    - Use <p> for paragraphs
    - Use <ul> and <li> for unordered lists
    - Use <strong> for bold text
    - Use <em> for italic text

    At the end of the email, include 4 product images using the following pattern:
    <div class="product-images">
      <img src="cid:image1">
      <img src="cid:image2">
      <img src="cid:image3">
      <img src="cid:image4">
    </div>

    Return ONLY the email body in HTML, without additional comments.'''

    email_content_payload = {{
        "messages": [{{"role": "user", "content": email_body_prompt}}],
        "max_tokens": 1000
    }}
    email_content_response = make_api_call("databricks-meta-llama-3-1-70b-instruct", email_content_payload)
    email_body = email_content_response['choices'][0]['message']['content']

    subject_payload = {{
        "messages": [
            {{"role": "user", "content": email_body_prompt}},
            {{"role": "assistant", "content": email_body}},
            {{"role": "user", "content": "now generate the subject of this email. Do not reply with anything other than the subject, I will use the response directly in the subject. Do not start with 'Here is a the answer' or anything like this. Start with the e-mail body already"}}
        ],
        "max_tokens": 50
    }}
    subject_response = make_api_call("databricks-meta-llama-3-70b-instruct", subject_payload)
    email_subject = subject_response['choices'][0]['message']['content']

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = email_subject
    message.attach(MIMEText(email_body, "html"))

    for i, img_path in enumerate(image_paths[:4]):
        img_data = download_file(img_path)
        image = MIMEImage(img_data)
        image.add_header('Content-ID', f'<image{{i+1}}>')
        image.add_header('Content-Disposition', 'inline', filename=f'image{{i+1}}.jpg')
        message.attach(image)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        return "Email sent successfully!"
    except Exception as e:
        return f"An error occurred: {{str(e)}}"
    finally:
        server.quit()

return send_email(image_paths, prompt_image, best_category, worst_category, databricks_token, databricks_host, sender_email, sender_password, receiver_email)
$$

;
"""

# Execute the SQL statement
spark.sql(sql_statement)

# COMMAND ----------

# MAGIC %md
# MAGIC Wrapper function, if you changed the name of the scope and/or secret you need to also change here

# COMMAND ----------

sql_statement = f"""

CREATE OR REPLACE FUNCTION {catalog}.{dbName}.send_email (
  image_paths ARRAY<STRING>,
  prompt_image STRING,
  best_category STRING,
  worst_category STRING
)
RETURNS STRING
LANGUAGE SQL
COMMENT 'Wrapper function that calls send_email_with_secrets with fixed secrets.
Example of use: SELECT send_email(array("/Volumes/{catalog}/{volume_name}/generated_images/image_1.jpg", "/Volumes/{catalog}/{volume_name}/generated_images/image_2.jpg", "/Volumes/{catalog}/{volume_name}/generated_images/image_3.jpg", "/Volumes/{catalog}/{volume_name}/generated_images/image_4.jpg"), "PROMPT THAT GENERATED THE IMAGE", "category1", "category2")'
RETURN 
  SELECT send_email_with_secrets(
    image_paths,
    prompt_image,
    best_category,
    worst_category,
    secret("{secret_scope}", "{email_image_token}"),
    secret("{secret_scope}", "{email_image_host}"),
    secret("{secret_scope}", "{sender_email}"),
    secret("{secret_scope}", "{sender_password}"),
    secret("{secret_scope}", "{receiver_email}")
  )
;
"""

# Execute the SQL statement
spark.sql(sql_statement)