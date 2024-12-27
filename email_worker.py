import pika
import json
import os
import asyncio
from aiosmtplib import send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

async def send_email(to_email, subject, body):
    message = MIMEMultipart()
    message["From"] = SMTP_USERNAME
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        await send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def process_notification(notification):
    status = notification["status"]
    details = notification["details"]
    to_email = notification["email"]

    subject = f"Scholarship Notification: {status}"
    body = f"Dear {notification['name']},\n\nYour scholarship status is: {status}.\n{details}\n\nBest regards,\nScholarship Team"
    await send_email(to_email, subject, body)

def consume_messages():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    print("Connected to RabbitMQ")

    channel.queue_declare(queue='notification_queue', durable=True)

    def callback(ch, method, properties, body):
        notification = json.loads(body)

        # Run the async email process in an event loop
        asyncio.run(process_notification(notification))

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='notification_queue', on_message_callback=callback)
    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    consume_messages()
