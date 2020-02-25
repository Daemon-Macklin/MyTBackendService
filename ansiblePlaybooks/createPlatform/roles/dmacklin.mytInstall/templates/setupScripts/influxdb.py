#!/usr/bin/python3

from influxdb import InfluxDBClient

client = InfluxDBClient('localhost')

client.create_database("MyTData")
