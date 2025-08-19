from integractor import Consumer
import json
import random
import time




# Define the moke data generation output from this actor
def mock_main(message):
    print(f"Mock Processing message in main.py: {message}")
    

# Here define production code which is used to generate real output of the actor
def production_main(message):
    print(f"Production Processing message in main.py: {message}")

# Set the consumer
consumer = Consumer( mock_callback=mock_main, production_callback=production_main,queue_name="qD")

def main():
    consumer.run(host='0.0.0.0', port=5555)

# Run the Flask app
if __name__ == "__main__":
    main()

