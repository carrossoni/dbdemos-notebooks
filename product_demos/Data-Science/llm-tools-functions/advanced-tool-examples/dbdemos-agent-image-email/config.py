# Databricks notebook source
# MAGIC %md 
# MAGIC ## Configuration file
# MAGIC
# MAGIC Please change your catalog and schema here to run the demo on a different catalog.
# MAGIC
# MAGIC <!-- Collect usage data (view). Remove it to disable collection or disable tracker during installation. View README for more details.  -->
# MAGIC <img width="1px" src="https://ppxrzfxige.execute-api.us-west-2.amazonaws.com/v1/analytics?category=data-science&org_id=1444828305810485&notebook=config&demo_name=chatbot-rag-llm&event=VIEW">

# COMMAND ----------

catalog = "dbdemos_agent_email_image"
dbName = db = "dbdemos_agent_email_image_schema"
volume_name = "dbdemos_agent_email_image_volume"

#Below are the secrets used to configure the email image functions for pat token and host (xxx.cloud.databricks.com)
secret_scope = "dbdemos"
email_image_token = "llm-agent-tools-email-image-token"
email_image_host = "llm-agent-tools-email-image-host"

#Below are the secrets used to configure the email sender (xxx@gmail.com), password and receiver (xxxx@gmail.com, xxx1@gmail.com)
sender_email = "llm-agent-tools-email-image-sender-email"
sender_password = "llm-agent-tools-email-image-sender-password"
receiver_email = "llm-agent-tools-email-image-receiver-email"