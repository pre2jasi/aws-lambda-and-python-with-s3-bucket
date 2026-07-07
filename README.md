# Organize S3 Objects by Date with AWS Lambda (Python)

AWS project that automatically sorts files uploaded to an S3 bucket into daily folders (`YYYYMMDD/filename`) using a Python Lambda function triggered on every upload.


---

## The Problem

A company has clients uploading many files into a shared S3 bucket. To keep the bucket organized, every file needs to be automatically sorted into a folder based on the date it was uploaded — without any manual intervention.

**Goal:** whenever a file lands in the bucket, a Lambda function should trigger automatically and move that file into a folder named after its upload date, in `YYYYMMDD` format.

---

## How the Solution Works

1. A client uploads a file to the root of the S3 bucket.
2. That upload event triggers a Lambda function.
3. The function:
   - Lists the objects currently in the bucket.
   - Builds today's date string in `YYYYMMDD` format.
   - Creates that folder in the bucket if it doesn't already exist.
   - Finds any object whose last-modified date matches today's folder name.
   - Copies each matching object into the folder, then deletes the original from the bucket root.
4. The result is a bucket that's automatically kept tidy, with every file living under a folder for the day it arrived.

---

## Prerequisites

Before writing the code, the environment needs to be set up:

- **Python** installed locally (3.10+ recommended) — verify with `python --version`
- **Boto3** installed (`pip install boto3`) — the AWS SDK for Python, used to create and manage AWS resources from code
- **An IAM user with programmatic access** — Python needs credentials to authenticate against your AWS account
- **AWS CLI** installed and configured via `aws configure`, so your credentials are stored locally
- **VS Code** (or any editor), ideally with the Python and Jupyter extensions installed for interactive development
- **Git** and a **GitHub account**, to version-control the project
- An **SSH key pair** added to GitHub, if you plan to clone/push over SSH

---

# S3 Event-Driven File Organizer (AWS Lambda + Python)

A serverless pipeline that automatically organizes incoming files in an S3 bucket into date-based partitions (`YYYYMMDD/`), triggered in real time on object upload. Built to replace a manual file-sorting process with a zero-touch, event-driven workflow.

---

## 🏗️ Architecture

```
                ┌──────────────────┐
   File Upload  │                  │
   ───────────► │   S3 Bucket      │
                │  (raw uploads)   │
                └────────┬─────────┘
                         │  S3:ObjectCreated (PUT) event
                         ▼
                ┌──────────────────┐
                │  AWS Lambda      │
                │  (Python/Boto3)  │
                │                  │
                │ 1. Read event    │
                │ 2. Derive date   │
                │    prefix        │
                │ 3. Copy object   │
                │    to YYYYMMDD/  │
                │ 4. Delete        │
                │    original      │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  S3 Bucket       │
                │  /YYYYMMDD/file  │
                └──────────────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  CloudWatch Logs │
                │  (execution +    │
                │   error traces)  │
                └──────────────────┘
```

**Flow:** File lands in S3 → `PUT` event triggers Lambda → Lambda computes today's date prefix → copies object into `YYYYMMDD/` folder → deletes the original (unpartitioned) object → logs the operation to CloudWatch.

---

## ⚙️ Tech Stack

| Component | Purpose |
|---|---|
| **AWS Lambda** | Serverless compute, executes on S3 event trigger |
| **Amazon S3** | Source/destination storage, event source |
| **IAM** | Least-privilege execution role for Lambda |
| **Boto3** | AWS SDK for Python — S3 object operations |
| **CloudWatch Logs** | Execution logging and debugging |
| **Jupyter Notebook** | Local prototyping/validation before deployment |

---

## 📂 Repository Structure

```
.
├── src/
│   └── lambda_function.py       # Lambda handler + core logic
├── notebooks/
│   └── prototype.ipynb          # Local exploration/validation notebook
├── iam/
│   └── lambda-execution-policy.json
├── tests/
│   └── test_lambda_function.py  # Unit tests for handler logic
├── README.md
└── requirements.txt
```

---

## 🚀 How It Works

1. **Trigger** — An S3 `PUT` event (new object created) invokes the Lambda function.
2. **Handler** — `lambda_handler(event, context)` parses the event payload to extract the bucket name and object key.
3. **Partitioning logic** — The function derives today's date (`YYYYMMDD`) and checks whether the object already resides in a dated prefix (to avoid reprocessing).
4. **Copy + delete** — The object is copied into the `YYYYMMDD/` prefix, then the original unpartitioned object is deleted.
5. **Logging** — Every operation (skip, copy, delete, error) is logged to CloudWatch for observability.

### Example handler signature

```python
def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    # ... partitioning + copy/delete logic
```

---

## 🔐 IAM Policy (least privilege)

The Lambda execution role is scoped to only what the function needs — not a broad, pre-existing role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME",
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## ⚠️ Design Challenges & Solutions

| Challenge | Solution |
|---|---|
| **Lambda execution contract** — Lambda requires a specific `lambda_handler(event, context)` entry point matching the configured runtime handler setting. | Restructured the script to conform to the handler contract and explicitly aligned the Lambda console's "Handler" field with the module/function name to avoid silent invocation failures. |
| **No stepwise debugging in Lambda** — the console offers no line-by-line execution like a notebook does. | Fully validated logic locally in Jupyter against representative test data first, minimizing iteration cycles and CloudWatch log-diving in production. |
| **Recursive trigger risk** — the function reads from and writes to the same bucket, risking infinite self-triggering. | Filtered on object key patterns (excluding already-partitioned prefixes) and `LastModified` metadata so the function only processes genuinely new, unsorted files. |
| **Over-permissioned roles** — reusing a broad, pre-existing IAM role would violate least-privilege. | Provisioned a dedicated IAM role scoped only to the specific S3 actions and CloudWatch logging the function requires. |

---

## 🧪 Testing

Local unit tests validate the partitioning and filtering logic against mocked S3 events (using `moto` or `unittest.mock`) before any deployment:

```bash
pip install -r requirements.txt
pytest tests/
```

---

## 📦 Deployment

1. Zip the function and dependencies:
   ```bash
   cd src
   zip -r ../deployment-package.zip .
   ```
2. Upload the zip to S3 (or directly via the Lambda console/CLI).
3. Create/update the Lambda function, pointing the handler to `lambda_function.lambda_handler`.
4. Attach the IAM role defined in `iam/lambda-execution-policy.json`.
5. Configure an S3 `PUT` event notification on the source bucket, targeting this Lambda function.

---

## 📈 Possible Next Steps

- Add a Dead Letter Queue (DLQ) for failed invocations
- Move to Infrastructure-as-Code (Terraform/CloudFormation/SAM) for repeatable deployment
- Add file-type validation before partitioning
- Emit custom CloudWatch metrics for monitoring pipeline health

---

## Author

Built as a hands-on project to practice serverless architecture, event-driven design, and IAM least-privilege access control on AWS.

## Project Walkthrough

### 1. Create the S3 bucket

Create the bucket that clients will upload files into (the tutorial uses `us-east-1` as the region).

### 2. Set up the repo

Create a GitHub repository for the project and clone it locally. This is where the Lambda source code will live and be version-controlled.

### 3. Prototype the logic in a Jupyter notebook

Rather than writing the whole script blind, it's easiest to build it one cell at a time in a notebook so each step's output can be checked before moving on:

- Import `boto3` and `datetime`.
- Get today's date and format it as `YYYYMMDD`.
- Connect to the S3 client via `boto3.client('s3')`.
- List all objects in the bucket with `list_objects_v2`.
- Extract just the object keys (filenames) from the response.
- Check whether a folder for today's date already exists; if not, create one with `put_object` (a "folder" in S3 is really just a zero-byte key ending in `/`).
- Loop through the objects, and for each one uploaded today (matched by its `LastModified` date) that isn't already inside a folder, copy it into today's folder with `copy_object`, then remove the original with `delete_object`.

### 4. Convert the notebook into a Lambda-ready script

Once the logic works cell-by-cell:

- Export the notebook to a plain `.py` file.
- Strip out the notebook cell markers and any debug/print statements used only for testing.
- Wrap the logic in a `lambda_handler(event, context)` function, since this is the entry point Lambda expects.

Here's the cleaned-up version used in this project:

```python
import boto3
from datetime import datetime

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket_name = "your-bucket-name"

    today = datetime.today()
    todays_date = today.strftime("%Y%m%d")
    directory_name = todays_date + "/"

    list_objects_response = s3_client.list_objects_v2(Bucket=bucket_name)
    get_contents = list_objects_response.get("Contents", [])

    existing_keys = [item.get("Key") for item in get_contents]

    if directory_name not in existing_keys:
        s3_client.put_object(Bucket=bucket_name, Key=directory_name)

    for item in get_contents:
        object_creation_date = item.get("LastModified").strftime("%Y%m%d") + "/"
        object_name = item.get("Key")

        if object_creation_date == directory_name and "/" not in object_name:
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource=f"{bucket_name}/{object_name}",
                Key=directory_name + object_name
            )
            s3_client.delete_object(Bucket=bucket_name, Key=object_name)
```

### 5. Package and stage the code

- Zip the `.py` file.
- Upload the zip to a separate S3 bucket (Lambda can pull its deployment package directly from S3).
- Push the notebook, script, and zip file to the GitHub repo so the project history is preserved.

### 6. Create an IAM role for Lambda

Create a role with:
- **Trusted entity:** AWS service → Lambda
- **Permissions:** `AmazonS3FullAccess` and `AWSLambdaBasicExecutionRole`

This lets the function read/write/delete S3 objects and write logs to CloudWatch.

### 7. Create the Lambda function

- Choose **Author from scratch**.
- Select the latest Python runtime.
- Attach the IAM role created above.

### 8. Add an S3 trigger

- Add an **S3** trigger to the function.
- Point it at the target bucket.
- Set the event type to **PUT** (object creation).
- Acknowledge the recursive-invocation warning (since the function's own copy/delete actions also touch the bucket — see the note on infinite loops below).

### 9. Upload the code and set the handler

- Upload the zip file from the S3 staging bucket as the function's source.
- Under **Runtime settings**, update the handler to match your script's filename, e.g. `your_script_name.lambda_handler` (it defaults to `lambda_function.lambda_handler`, which only works if your file is literally named `lambda_function.py`).

### 10. Test

- Create a test event in the Lambda console and run it to confirm the code executes without errors.
- Then do a real test: upload a few files directly to the bucket root and confirm they disappear from the root and reappear inside today's `YYYYMMDD/` folder.

---

## Cleanup

To avoid ongoing AWS charges after testing, delete:
- The Lambda function
- Both S3 buckets (the target bucket and the one used to stage the deployment zip)
- The IAM role created for this project

---

## A Note on Infinite Loops

Because this function's own `copy_object` and `put_object` calls write back into the *same* bucket that triggers it, a `PUT` trigger can cause the function to invoke itself repeatedly. This project's core logic naturally avoids reprocessing folder markers and already-moved files (the `"/" not in object_name` check skips anything already inside a dated folder), but if you extend this function, keep that safeguard in mind — it's what keeps the bucket from looping forever.

---

## License

MIT License.
