#!/bin/sh

# Set default values for environment variables if not provided
: ${REMOTE_ADDRESS:='default_address:1883'}
: ${REMOTE_USERNAME:='default_username'}
: ${REMOTE_PASSWORD:='default_password'}

# Substitute environment variables in the template configuration file
envsubst < /mosquitto/config/mosquitto.conf.template > /mosquitto/config/mosquitto.conf

# Start mosquitto with the generated configuration file
mosquitto -c /mosquitto/config/mosquitto.conf