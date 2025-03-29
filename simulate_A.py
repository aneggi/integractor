from integactor import Generator
import json
import random
import time

# Define the moke data generation output from this actor
def mock_main():
    data = {
        'id': random.randint(1, 100000),
        'sensor_data1': random.uniform(0, 100), 
        'sensor_data2': random.uniform(-100, 100),
        'timestamp': time.time()
    }
    return json.dumps(data)

# Here define production code which is used to generate real output of the actor
def production_main():
    data = {
        'realdata': "yes"
    }
    return json.dumps(data)

# Set the generator
generator = Generator(mock_output=mock_main, production_output=production_main , exchange_name="ex2", routing_key="rk1")

# Run the Flask app
if __name__ == "__main__":
    generator.run(host='0.0.0.0', port=5552)