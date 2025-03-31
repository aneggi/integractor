from integactor import Producer
import json
import random
import time

# Define the moke data generation output from this actor
def mock_main():
    data = {
        'id': random.randint(1, 100000),
        'pos_x': random.uniform(0, 500.5), 
        'pos_y': random.uniform(-1, 40.5),
        'pos_z': random.uniform(-5, 255),
        'timestamp': time.time()
    }
    return json.dumps(data)

# Here define production code which is used to generate real output of the actor
def production_main():
    data = {
        'realdata': "yes"
    }
    return json.dumps(data)

# Set the producer
producer = Producer(mock_output=mock_main, production_output=production_main , exchange_name="ex1", routing_key="rk9")

def main():
    producer.run(host='0.0.0.0', port=5553)

# Run the Flask app
if __name__ == "__main__":
    main()