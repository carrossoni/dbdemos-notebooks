# Databricks notebook source
# MAGIC %run ../config

# COMMAND ----------

dbutils.widgets.dropdown("reset_all_data", "false", ["true", "false"], "Reset all data")
dbutils.widgets.text("min_dbr_version", "14.3", "Min required DBR version")

# COMMAND ----------

# MAGIC %run ./00-global-setup-v2

# COMMAND ----------

reset_all_data = dbutils.widgets.get("reset_all_data") == "true"
DBDemos.setup_schema(catalog, db, reset_all_data, volume_name)

data_exists = False
try:
  data_exists = spark.catalog.tableExists('customers_dataset') and spark.catalog.tableExists('order_items_dataset') and spark.catalog.tableExists('order_reviews_dataset') and  spark.catalog.tableExists('orders_dataset') and  spark.catalog.tableExists('products_dataset')
  if data_exists:
    data_exists = spark.sql('select count(*) as c from customers_dataset').collect()[0]['c'] > 0
except Exception as e:
  print(f"folder doesn't exists, generating the data...")

# COMMAND ----------

import os

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
path = os.path.dirname(notebook_path)

source_dir = "file:/Workspace/"+path+"/_resources/files/"
destination_dir = "/Volumes/{}/{}/{}/files".format(catalog, db, volume_name)

# List all files in the source directory
files = dbutils.fs.ls(source_dir)

# Copy each file to the destination
for file in files:
    if file.isFile():
        source_path = os.path.join(source_dir, file.name)
        destination_path = os.path.join(destination_dir, file.name)
        dbutils.fs.cp(source_path, destination_path)
        print(f"Moved {file.name} to {destination_path}")

# COMMAND ----------

from databricks.sdk import WorkspaceClient

def get_shared_warehouse(name=None):
    w = WorkspaceClient()
    warehouses = w.warehouses.list()
    for wh in warehouses:
        if wh.name == name:
            return wh
    for wh in warehouses:
        if wh.name.lower() == "shared endpoint":
            return wh
    for wh in warehouses:
        if wh.name.lower() == "dbdemos-shared-endpoint":
            return wh
    #Try to fallback to an existing shared endpoint.
    for wh in warehouses:
        if "dbdemos" in wh.name.lower():
            return wh
    for wh in warehouses:
        if "shared" in wh.name.lower():
            return wh
    for wh in warehouses:
        if wh.num_clusters > 0:
            return wh       
    raise Exception("Couldn't find any Warehouse to use. Please create a wh first to run the demo and add the id here")


def display_tools(tools):
    display(pd.DataFrame([{k: str(v) for k, v in vars(tool).items()} for tool in tools]))

# COMMAND ----------

if not data_exists:
    # Define the volume path containing the CSV files
    volume_path = "/Volumes/{}/{}/{}/files".format(catalog, db, volume_name)

    # List all CSV files in the volume
    csv_files = [f.name for f in dbutils.fs.ls(volume_path) if f.name.endswith('.csv')]

    # Load each CSV file and save it as a table
    for csv_file in csv_files:
        table_name = csv_file.replace('.csv', '')
        df = spark.read.csv(
            f"{volume_path}/{csv_file}",
            header=True,
            inferSchema=True
        )
        df.write.mode('overwrite').saveAsTable(f"{catalog}.{db}.{table_name}")