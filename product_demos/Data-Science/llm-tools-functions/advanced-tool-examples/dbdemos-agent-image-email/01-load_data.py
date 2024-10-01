# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # Composable AI systems: Building an agent that helps to design a new product and boost sales!
# MAGIC
# MAGIC ## What's a composable AI system
# MAGIC
# MAGIC LLMs are great at answering generated questions. However, this alone isn't enough to provide value to your customers.
# MAGIC
# MAGIC To be able to provide valuable answers, extra information is requred, specific to the user (your customer contract ID, the last email they sent to your support, your most recent sales report etc.).
# MAGIC
# MAGIC Composable AI systems are designed to answer this challenge. They are more advanced AI deployments, composed of multiple entities (tools) specialized in different action (retrieving information or acting on external systems). <br/>
# MAGIC
# MAGIC At a high level, you build & present a set of custom functions to the AI. The LLM can then reason about it, deciding which tool should be called and information gathered to answer the customer need.
# MAGIC
# MAGIC ## Building Composable AI Systems with Databricks Mosaic AI agent framework
# MAGIC
# MAGIC
# MAGIC Databricks simplifies this by providing a built-in service to:
# MAGIC
# MAGIC - Create and store your functions (tools) leveraging UC
# MAGIC - Execute the functions in a safe way
# MAGIC - Reason about the tools you selected and chain them together to properly answer your question. 
# MAGIC
# MAGIC At a high level, here is the AI system we will implement in this demo:
# MAGIC
# MAGIC <img src="https://github.com/databricks-demos/dbdemos-resources/blob/main/images/product/llm-tools-functions/llm-tools-functions-flow.png?raw=true" width="900px">
# MAGIC
# MAGIC
# MAGIC <!-- Collect usage data (view). Remove it to disable collection or disable tracker during installation. View README for more details.  -->
# MAGIC <img width="1px" src="https://ppxrzfxige.execute-api.us-west-2.amazonaws.com/v1/analytics?category=data-science&notebook=00-AI-function-tools-introduction&demo_name=llm-tools-functions&event=VIEW">

# COMMAND ----------

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
# MAGIC For best security and reproducibility the functions use Databricks secrets to get Token and other values, `if you change any name of the scope or secret below, please also change in the config file before running script 02-create_functions`
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

# MAGIC %run ./_resources/00-init $reset_all=true