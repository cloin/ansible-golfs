# Ansible golfs
This is a demo that uses a golf ball from Puttlink, an app to connect to the golfball and stream data to MQTT where Ansible Automation Platform can pick up these messages and react to putting events in near real-time.

## Staff requirements
- Decently technical story teller to talk though edge application automation, mqtt, Event-Driven Ansible 

## Hardware requirements
- [Puttlink golfball](https://www.puttlink.com/shop)
    - Bluetooth golfball that streams sensor data over published bluetooth characteristics
    - They offer a package deal that includes an IR spotlight that I reccomend. The golfball has some optical sensors to measure rotation and they require a good amount of light. Position the IR light above the cup so that you're putting into the light.
    - There's a magnet included with each ball purchase that should be placed within the cup
- Raspberry Pi or other compute
    - Runs a python app to connect to bluetooth golfball and a MQTT broker to stream data to
- Putters
    - **Do not get rubber coated putters**, opt for some kind of metal that will create a heavier impact on the ball to ensure putts are registered
- Putting surface

## Software requirements
- Python app
- MQTT broker deployed locally
    - Golfball data will be written to this broker
- MQTT broker deployed remotely
    - The local broker should be configured to mirror messages to the remote broker
    - Event-Driven Ansible should be configured to subscribe to the remote broker
- Ansible Automation Platform (Automation Controller, Event-Driven Ansible Controller)

## Deployment
### Ansible Automation Platform
Deploy AAP with Controller and Event-Driven Ansible Controller. I typically make this a cloud deployment and typically in the same environment where the remote MQTT broker is deployed.
#### Automation Controller
- Credential for Mastodon account where messages will be published (Mastodon is like Twitter/X)
- Job template that will be called by Event-Driven Ansible Controller after every made putt

#### Event-Driven Ansible Controller
- Rulebook activation that subscribes to remote MQTT broker
- Rulebook should be configured to launch job template on Automation Controller

### MQTT
MQTT was selected for the small footprint, ease of configuration and is common in edge environments. There should be 2 brokers as part of this demo. The local broker will be configured to mirror all messages posted to the remote broker. The remote broker will be the event source for Event-Driven Ansible. When configured this way, the remote broker is always available and will not cause a running rulebook activation to fail. Furthermore, should there be network issues onsite (e.g. spotty wifi coverate) where the demo is deployed, data will stream to the local broker and the messages will be mirrored when connectivity is restored. 
#### Remote broker
- Deploy an MQTT broker on some cloud. This broker should be configured with basic auth so the local broker can mirror messages to the remote broker.
#### Local broker
- The included `podman-compose.yml` can be used to deploy the local broker. Substitute values in `podman-compose.yml` with the necessary username, password and address for the remote broker. These values are used to configure the mirrored pair of brokers. 

### Python application
This application uses bluetooth low energey (BLE) to connect to the golfball and subscribes to the BLE characteristics (ball rotation, ball in cup, ball speed, etc.). The application prints the sensor data published over these characteristics to the local MQTT broker which then mirrors the sensor data to the remote MQTT broker.

Run the application locally on the compute you have available. There are two flags accepted by the application which correspond to the address of the local MQTT broker (e.g. localhost) and the BLE address of the particular golf ball you have with you. Here's an example:

~~~
python app/main.py -m localhost:1883 -g PL2B1188
~~~

I've also bundled a python app that will retrieve the golfball BLE ID needed in the previous command. Run it like this:
~~~
python scan.py "^PL2B.*"
~~~
The above command scans for Puttlink devices in pairing mode and prints the devices characteristic UUIDs and should show the BLE ID of the golfball at the top of the output.