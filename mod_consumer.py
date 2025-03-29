import pika
import json
import random
import time
import threading
import configparser
from flask import Flask
from termcolor import colored


class Consumer:
    def __init__(self, config_file='config.ini', mock_callback=None,production_callback=None, queue_name="sensor_queue"):
    #def __init__(self, config_file='config.ini', queue_name="queuee", message_callback=None):
        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.timeout = self.config.get('TIMEOUT', 'notifications', fallback='8000')
        self.rabbitmq_host = self.config.get('CONNECTION', 'host')
        self.rabbitmq_port = self.config.get('CONNECTION', 'port')
        self.username = self.config.get('CONNECTION', 'user')
        self.password = self.config.get('CONNECTION', 'pass')

        self.queue_name = queue_name
        self.running = False
        self.thread = None

        self.production_activate = False

        self.mock_callback = mock_callback  # Function in main.py that handles messages
        self.production_callback = production_callback


        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Register Flask routes to start/stop consuming."""
        self.app.add_url_rule('/in/on/', 'start_consuming', self.start_consuming)
        self.app.add_url_rule('/in/off/', 'stop_consuming', self.stop_consuming)

        self.app.add_url_rule('/mode/moke', 'moke_mode', self.moke_mode)
        self.app.add_url_rule('/mode/production', 'production_mode', self.production_mode)

    def setup_rabbitmq_connection(self):
        """Establish RabbitMQ connection."""
        credentials = pika.PlainCredentials(self.username, self.password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port, credentials=credentials)
        )
        channel = connection.channel()
        args = {"x-message-ttl": 5000,"x-overflow": "drop-head"}  
        channel.queue_declare(queue=self.queue_name, durable=True, arguments=args)
        return connection, channel

    def receive_message(self):
        """Receives messages and calls the callback function."""
        connection, channel = self.setup_rabbitmq_connection()

        def callback(ch, method, properties, body):
            """Handle received messages."""
            message = body.decode()
            print(f"Received message: {message}")  # Debugging log
            if self.production_activate and self.production_callback:
                self.production_callback(message)
            elif self.mock_callback:
                self.mock_callback(message)
            else:
                print("No callback function provided!")

        channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Listening for messages on queue '{self.queue_name}'...")
        channel.start_consuming()

    def start_consuming(self):
        """Start consuming messages in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.receive_message)
            self.thread.start()
            return "Started consuming messages."
        return "Already running."

    def stop_consuming(self):
        """Stop consuming messages."""
        self.running = False
        return "Stopped consuming messages."
    
    def moke_mode(self):
        self.production_activate = False
        return "Moke mode."
    
    def production_mode(self):
        self.production_activate = True
        return "Production mode."

    def run(self, host='0.0.0.0', port=5555):
        """Run the Flask app to control the consumer."""
        self.app.run(host=host, port=port)