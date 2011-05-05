#!/usr/bin/python
# vim: set fileencoding=utf-8 noet ts=4 sw=4 sts=4 tw=79 :

import time, threading, multiprocessing
from Queue import Queue
import controller, arduino

from constants import *

# from controller import *

DAEMON_RUNNING = True

# ArduinoHypervisor is the class that handles the supervising of the N threads
# (one for each Arduino) and attaches the modules to the arduino they demand.
class ArduinoHypervisor:
	class ArduinoHandler():
		# ArduinoHandler is the class that handles each Arduino in a concurrent
		# way so inputs/outputs are nonblocking and transfered when the buffers
		# allow us to, controller-agnostic.
		def __init__(self, arduino, parentcv):
			self.arduino = arduino
			self.id = arduino.get_id()
			self.parentcv = parentcv
			self.in_queue = Queue()
			self.out_queue =Queue()
			self.listeners = []

		def get_id(self):
			return self.id

		def addListener(self, callback):
			"""Adds a listener to the list of listeners to be warned about
			updates in this arduino channel
			"""
			self.listeners.append(callback)

		def queue_put(self, str):
			"""This function allows to put data on the output queue in order to
			be sent to the Arduino
			"""
			self.out_queue.put(msg, block=True)

		def run_once(self):
			"""Main Handler loop:

			While the daemon is started, it will read bytes from the Arduino
			serial port and send data if it is required to.
			"""
			byte = self.arduino.read_byte(False)
			if byte == None:
				if self.out_queue.empty():
					#sleep(0.01)
					pass
			else:
				#self.parentcv.acquire()
				try:
					if byte == BYTE_STX:
						msg = self.arduino.read_until(BYTE_ETX)
						msg = msg[:-1]
					else:
						msg = byte
					self.in_queue.put(msg, block=False)
					#self.parentcv.notify()
				finally:
					#self.parentcv.release()
					pass

			# Do we have to send data?
			if not self.out_queue.empty():
				# Send one message
				try:
					msg = self.out_queue.get_nowait()
					self.arduino.write(msg)
					self.out_queue.task_done()
				except:
					print 'Data was not avaliable in out_queue'


		def getListeners(self):
			return self.listeners

	## End of class ArduinoHandler


	def __init__(self, device_list):
		self.arduino_handlers = {}
		self.cv = threading.Condition()

		print 'Lista de dispositivos: %s' % device_list
		for path in device_list:
			try:
				device = self.ArduinoHandler(arduino.Arduino(path), self.cv)
			except Exception as e:
				print('Error while initializing device %s: %s' %
						(path, e))
				continue
			id = device.get_id()
			self.arduino_handlers[id] = device
			print 'Got device with ID=%s' % id

	def get_handler(self, id):
		if self.arduino_handlers.has_key(id):
			return self.arduino_handlers[id]
		else:
			return None

	def watchdog_once(self):
		"""This function runs a multiprocessing queue
		so that each arduino handler won't lock while
		waiting from info to be done
		"""
		#self.cv.acquire()
		try:
			#self.cv.wait(10)
			for (id,arduino) in self.arduino_handlers.iteritems():
				if not arduino.in_queue.empty():
					msg = arduino.in_queue.get()
					print 'There is info on the arduino query!'
					print '   Handling info: %s' % msg
					for listener in arduino.getListeners():
						print '     Sending to listener %s' % listener
						#new_process = Process(target=listener.recv_msg,
						#		attrs=[msg, arduino.out_queue])
						#new_process.daemonic = True
						#new_process.start()
						listener.recv_msg(msg, arduino.out_queue)

		except KeyboardInterrupt:
			DAEMON_RUNNING = False
		finally:
			#self.cv.release()
			pass

		time.sleep(0.001)
	
		
		pass


	def run(self):
		"""This funcion runs each arduinoHandler in a separate thread.
		Then waits for processing from them to call a pool of workers
		(see self.loop(self))
		"""

		threads = []

		#worker_pool = multiprocessing.Pool(processes=2, maxtasksperchild=10) # Py3K
		#worker_pool = multiprocessing.Pool(processes=2)

		global DAEMON_RUNNING

		while DAEMON_RUNNING:
			for (id, obj) in self.arduino_handlers.iteritems():
				obj.run_once()
			
			self.watchdog_once()


def run():
	hypervisor = ArduinoHypervisor(arduino.device_list())

	# Take all controllers:
	modules = controller.load_all()
	workers = {}
	for module_name, module in modules.iteritems():
		arduino_id = module.arduino_id
		if arduino_id in workers:
			workers[arduino_id].append(module)
		else:
			workers[arduino_id] = [module]

	for arduino_id, mod_list in workers.iteritems():
		for module in mod_list:
			handler = hypervisor.get_handler(arduino_id)
			if handler != None:
				handler.addListener(module)

	hypervisor.run()
	return None



