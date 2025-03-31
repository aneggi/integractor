import pika
import json
import random
import time
import threading
import configparser
from flask import Flask
from termcolor import colored

class Producer:
    def __init__(self, config_file='config.ini', mock_output=None,production_output=None, exchange_name="sensor_queue", routing_key="sensor2"):
        # Configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.timeout = self.config.get('TIMEOUT', 'sensorA', fallback='8000')
        self.sleep_duration_in_seconds = int(self.config.get('SLEEP', 'ballpositions', fallback='1'))
        
        self.rabbitmq_host = self.config.get('CONNECTION', 'host')
        self.rabbitmq_port = self.config.get('CONNECTION', 'port')
        self.username = self.config.get('CONNECTION', 'user')
        self.password = self.config.get('CONNECTION', 'pass')
        
        #self.exchange_name = "exchangee"
        self.random_acceptance_rate = 1001  # percentage of passing message on 1000
        
        self.running = False
        self.thread = None
        self.production_activate = False
        
        # Moke data generation callback (provided by main app)
        self.mock_output = mock_output
        self.production_output = production_output
        self.exchange_name = exchange_name  # Set the queue name
        self.routing_key = routing_key  # Set the routing key
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register Flask routes."""
        self.app.add_url_rule('/out/on/', 'start_publishing', self.start_publishing)
        self.app.add_url_rule('/out/off', 'stop_publishing', self.stop_publishing)

        self.app.add_url_rule('/mode/moke', 'moke_mode', self.moke_mode)
        self.app.add_url_rule('/mode/production', 'production_mode', self.production_mode)

    def setup_rabbitmq_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials
            )
        )
        channel = connection.channel()
        # Declare the queue with the provided queue name
        #channel.queue_declare(queue=self.queue_name)
        return connection, channel

    def publish_message(self, channel):
        selector = random.uniform(0, 1000)
        if selector < self.random_acceptance_rate:
            # Use the moke_output callback to generate the message
            if self.production_activate and self.production_output:
                message = self.production_output()    
            elif self.mock_output and not self.production_activate:
                message = self.mock_output()  # Call the function passed from the main app
            else:
                # Fallback if no generator is provided (you can handle it differently)
                message = json.dumps({'error': 'No moke_output or production_output provided'})
            
            channel.basic_publish(exchange=self.exchange_name, routing_key=self.routing_key, body=message, properties=pika.BasicProperties(expiration=self.timeout))
            print(colored(f'Sent data to {self.exchange_name}: {message}', 'green', attrs=['bold']))

    def publish_loop(self):
        connection, channel = self.setup_rabbitmq_connection()
        try:
            while self.running:
                self.publish_message(channel)
                time.sleep(self.sleep_duration_in_seconds)
        except KeyboardInterrupt:
            print("Stopped by user")
        finally:
            connection.close()

    def start_publishing(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.publish_loop)
            self.thread.start()
            return "Started publishing sensor data."
        return "Already running."

    def stop_publishing(self):
        self.running = False
        return "Stopped publishing sensor data."
    
    def moke_mode(self):
        self.production_activate = False
        return "Moke mode."
    
    def production_mode(self):
        self.production_activate = True
        return "Production mode."

    def run(self, host='0.0.0.0', port=5552):
        """Run the Flask app."""
        self.app.run(host=host, port=port)


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

        self.mock_callback = mock_callback  
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
        args = {}  #"x-message-ttl": 5000, "x-overflow": "drop-head"
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


class Transformer:
    def __init__(self, config_file='config.ini', mock_callback=None,production_callback=None, queue_name="sensor_queue",exchange_name="exchange_not_defined", routing_key="sensor2"):
        # Configuration
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.timeout = self.config.get('TIMEOUT', 'sensorA', fallback='8000')
        self.sleep_duration_in_seconds = int(self.config.get('SLEEP', 'ballpositions', fallback='1'))
        
        self.rabbitmq_host = self.config.get('CONNECTION', 'host')
        self.rabbitmq_port = self.config.get('CONNECTION', 'port')
        self.username = self.config.get('CONNECTION', 'user')
        self.password = self.config.get('CONNECTION', 'pass')
        
        self.exchange_name = exchange_name #"exchangee"
        self.random_acceptance_rate = 1001  # percentage of passing message on 1000
        
        self.running = False
        self.thread = None
        self.production_activate = False
        
        self.mock_callback = mock_callback  
        self.production_callback = production_callback
    
        self.forward_activate = False
        self.queue_name = queue_name  #input
        self.routing_key = routing_key  # output
        
        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Register Flask routes."""
        self.app.add_url_rule('/out/on/', 'start_publishing', self.start_publishing)
        self.app.add_url_rule('/out/off', 'stop_publishing', self.stop_publishing)

        self.app.add_url_rule('/in/on/', 'start_consuming', self.start_consuming)
        self.app.add_url_rule('/in/off/', 'stop_consuming', self.stop_consuming)

        self.app.add_url_rule('/mode/moke', 'moke_mode', self.moke_mode)
        self.app.add_url_rule('/mode/production', 'production_mode', self.production_mode)

    def setup_rabbitmq_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                credentials=credentials
            )
        )
        channel = connection.channel()
        # Declare the queue with the provided queue name
        args = {"x-message-ttl": 5000,"x-overflow": "drop-head"}  
        channel.queue_declare(queue=self.queue_name, durable=True, arguments=args)
        #channel.queue_declare(queue=self.queue_name)
        return connection, channel

    
        
    def publish_message(self, message):

        print(colored(f'Self:{self} and Message:{message}', 'red', attrs=['bold']))
        connection, channel = self.setup_rabbitmq_connection()
        if not self.forward_activate:
            print(colored(f'Forward disabled.', 'red', attrs=['bold']))
            return "Forward disabled."
        else:
            message = json.dumps({'error': 'No moke_output or production_output provided'})
            channel.basic_publish(exchange=self.exchange_name, routing_key=self.routing_key, body=message, properties=pika.BasicProperties(expiration=self.timeout))
            print(colored(f'Sent data to {self.exchange_name}: {message}', 'green', attrs=['bold']))
        connection.close()

        

    def start_publishing(self):
        if self.forward_activate:
            return "Already active."
        self.forward_activate = True
        return "Output forward activated."
        
    def stop_publishing(self):
        self.forward_activate = False
        return "Stopped forward messages."
    
    def moke_mode(self):
        self.production_activate = False
        return "Moke mode."
    
    def production_mode(self):
        self.production_activate = True
        return "Production mode."
    
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

    def run(self, host='0.0.0.0', port=5552):
        """Run the Flask app."""
        self.app.run(host=host, port=port)