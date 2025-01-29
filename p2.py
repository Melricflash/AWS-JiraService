import boto3
from dotenv import load_dotenv
import os
from jira import JIRA

load_dotenv()

# Environment Variables
AWS_ACCESS = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION")
p2QueueURL = os.getenv("p2Queue_URL")
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_KEY = os.getenv("JIRA_API_KEY")
JIRA_PROJ = os.getenv("JIRA_PROJECT_KEY")

# Setup SQS client
sqs = boto3.client('sqs',
                   aws_access_key_id = AWS_ACCESS,
                   aws_secret_access_key = AWS_SECRET,
                   region_name = AWS_REGION # Move to environment later
                   )

# Create a Jira Client authenticated with email and key
jiraClient = JIRA(
    server = JIRA_URL,
    basic_auth = (JIRA_EMAIL, JIRA_KEY)
)

def p2JiraPush():
    while True:
        # Fetch the message from the queue

        try:
            # Attempt to read from the queue
            response = sqs.receive_message(
                QueueUrl = p2QueueURL,
                MaxNumberOfMessages = 1,  # Just get one item from the queue for now
                WaitTimeSeconds = 20
            )

            if 'Messages' in response:
                queueMessage = response['Messages'][0]
                messageID = queueMessage['MessageId'] # Could be used for a JIRA ticket
                receipt = queueMessage['ReceiptHandle']
                contents = queueMessage['Body']

                # Parse the message contents
                parsedContents = eval(contents)
                title = parsedContents['title']
                description = parsedContents['description']

                print(title)
                print(description)


                # Create an issue dictionary
                issueContents = {
                    "project": {'key': 'IEMELRIC'},
                    "summary": title,
                    "description": description,
                    "issuetype": {'name': 'Task'}, # Task, Epic and Subtask are available!!
                }

                # Turn into a jira issue
                issue = jiraClient.create_issue(fields = issueContents)
                print(f"Created JIRA issue for: {messageID}")

                # Delete from SQS
                sqs.delete_message(QueueUrl = p2QueueURL, ReceiptHandle = receipt)
                print("Deleted message from SQS...")

            else:
                print("No messages found in queue...")

        except Exception as err:
            print(f"An error occurred: {err}")


p2JiraPush()