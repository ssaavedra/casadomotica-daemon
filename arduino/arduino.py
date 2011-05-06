#!/bin/python
# vim: set fileencoding=utf-8 noet ts=4 sw=4 sts=4 tw=79 :

import os, sys, re, time

from serial import Serial
from constants import *

class Arduino:

	def __init__(self, serialport):
		"""Takes the string of the serial port
		and connects to that port, binding the
		Arduino object to it.
		"""
		print('Instanciado Arduino dispositivo %s' % serialport)
		try:
			self.serialport = Serial(serialport, 9600)
			self.error = False
			self.id = None
		except:
			self.error = True
			self.id = -666
			raise

	def read_byte(self, block=False):
		"""Lee un byte.
		Si block=True lee con espera activa hasta
		que exista algún byte que leer, porque no
		funciona sin espera activa.
		"""
		if block == False and self.serialport.inWaiting() < 1:
			return None
		return self.serialport.read(1);


	def read_until(self, until):
		buffer = []
		while buffer[-1] != until:
			if self.serialport.inWaiting() < 1:
				return buffer
			buffer += self.serialport.read(1);
		return buffer

	def write(self, str):
		return self.serialport.write(str)

	def write_byte(self, byte):
		return self.serialport.write(chr(byte))

	def get_id(self):
		if self.error:
			return self.id

		if self.id != None:
			return self.id

		# Consume all bytes for this query
		self.serialport.flushInput()
		print 'Lendo o ID..'
		while self.id == None:
			self.write_byte(QUERY_IDENT)
			self.id = self.serialport.read(1)
			self.serialport.flush()
			self.serialport.flushInput()
		return self.id



def device_list():
	if not os.path.isdir('/dev'):
		raise EnvironmentError('You have no /dev dir!')

	devices = os.listdir('/dev')

	plat = sys.platform.lower()

	if plat[:5] == 'linux':
		arduino_re = re.compile('ttyUSB');

	elif plat[:6] == 'darwin':
		arduino_re = re.compile('tty\.usbserial')

	else:
		raise EnvironmentError('No compatible platform found' + \
				'in the auto-detecion')

	# Get the Arduino's for each device
	devices = [ ('/dev/' + (device)) for device in devices if arduino_re.match(device) != None ]
	return devices


