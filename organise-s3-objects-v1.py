# %% [markdown]
# **Find and Terminate EC2 Instances with SSH Open to the World**
# 
# **What this script does:**
# 1. Finds all security groups that allow SSH (port 22) from anywhere (0.0.0.0/0)
# 2. Finds all running or stopped EC2 instances using those security groups
# 3. Terminates those EC2 instances
# 
# **Why this matters:** Leaving SSH open to the world is a major security risk. This is the type of automation you'd build with AWS Lambda to keep your environment secure.

# %% [markdown]
# **Step 1: Import Modules and Connect to AWS**

# %%

def lambda_handler(event, context):
    import boto3
    from datetime import datetime


    # %% [markdown]
    # **Step 2: Create variable to call today's date**

    # %%
    today = datetime.today()

    # %% [markdown]
    # **See what the response looks like**

    # %%
    today

    # %% [markdown]
    # **Format the date to match the project instruction YYYYMMDD and hold value in anothr variable**

    # %%
    todays_date = today.strftime("%Y%m%d")

    # %% [markdown]
    # **See what the output look like**

    # %%
    todays_date

    # %% [markdown]
    # **Step 3: call boto3 client in aws**

    # %%

    s3_client = boto3.client('s3')

    # %% [markdown]
    # **Set our bucket name to bucket in aws**

    # %%
    bucket_name = "nubby-organise-s3-objects"


    # %%
    import boto3
    sts = boto3.client('sts')
    print(sts.get_caller_identity())

    # %% [markdown]
    # **Step 4: list all objects in bucket**

    # %%
    list_objects_response = s3_client.list_objects_v2(Bucket=bucket_name)

    # %% [markdown]
    # **See what the response looks like**

    # %%
    list_objects_response

    # %% [markdown]
    # **Get the value of the "contents" key from the response**

    # %%
    get_contents = list_objects_response.get("Contents")

    # %% [markdown]
    # **See what the contents look like**

    # %%
    get_contents

    # %% [markdown]
    # **Step 5: Filter Out all contentds and put them in a list **

    # %%
    get_all_s3_objects_and_folder_names = []

    for item in get_contents:
        s3_object_name = item.get("Key")

        get_all_s3_objects_and_folder_names.append(s3_object_name)

    # %% [markdown]
    # **See the list of all contents**

    # %%
    get_all_s3_objects_and_folder_names

    # %% [markdown]
    # **Step 6: Create a folder for today's date in s3.**

    # %%
    directory_name = todays_date + "/"

    # %% [markdown]
    # **See the folder created for todays date**

    # %%
    directory_name

    # %% [markdown]
    # **Step 7: check if folder exist for todays date in the s3 bucket**

    # %%
    if directory_name not in get_all_s3_objects_and_folder_names:
        s3_client.put_object(Bucket=bucket_name, Key=(directory_name))

    # %% [markdown]
    # **Now add objects that was uploade today into the folder baed on 2 conditions: first check if lat modified date match our folder name and then check if pbject doesn t have a / at the end and also delete upload file from bucket since they are in the folder already**

    # %%
    for item in get_contents:
        object_create_date = item.get("LastModified").strftime("%Y%m%d") + "/"
        object_name = item.get("Key")

        if object_create_date == directory_name and "/" not in object_name:
            s3_client.copy_object(Bucket=bucket_name, CopySource=bucket_name+"/"+ object_name, Key=directory_name+object_name)
            s3_client.delete_object(Bucket=bucket_name, Key=object_name)

    # %% [markdown]
    # **Step 8: End of code**


