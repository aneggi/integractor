from integractor import Consumer, Transformer
import json
import random
import time


#routing_key = 'notification'

# Define the moke data generation output from this actor
def mock_main(message):
    print(f"Mock Processing message in main.py: {message}")
    
    

# Here define production code which is used to generate real output of the actor
def production_main(message):
    print(f"Production Processing message in main.py: {message}")

    # Request to send data
    transformer.publish_message(message)

# Set the transformer
transformer = Transformer(mock_callback=mock_main, production_callback=production_main,queue_name="qC",exchange_name="exD",routing_key="rk5")

def main():
    transformer.run(host='0.0.0.0', port=5554)

# Run the Flask app
if __name__ == "__main__":
    main()

