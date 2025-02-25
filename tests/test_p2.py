import threading
import pytest
import boto3
import os
from app import p2JiraPush

@pytest.fixture
def client(load_app):
    with load_app.test_client() as client:
        yield client

def test_get_message_from_p2(client, setup_sqs_queues, monkeypatch, mocker):
    queue_url = os.environ["p2Queue_URL"]

    # Patch p2Queue URL again as we load the app which may overwrite variables
    monkeypatch.setattr("app.p2QueueURL", queue_url)

    # Patch out the jira client using mocker
    mocker.patch("app.jiraClient", return_value=None)

    sqs_client = boto3.client("sqs", region_name="eu-north-1")

    # Compose a message to send to test SQS queue
    message = {
        "title": "Jira Title",
        "description": "test description",
    }

    # Send message to SQS
    sqs_client.send_message(QueueUrl=queue_url, MessageBody=str(message))

    thread = threading.Thread(target=p2JiraPush)
    thread.start()
    thread.join(timeout=5)

    # Attempt to stop the thread
    monkeypatch.setattr("app.stop_flag", True)
    thread.join()

    response = sqs_client.receive_message(QueueUrl = queue_url)
    assert "Messages" not in response
