from functools import partial, wraps
import simpy

import matplotlib, numpy
import matplotlib.pyplot as plt
import networkx as nx

_routers = {}
_links = {}
_flows = {}


def trace(env, callback):
	def get_wrapper(env_step, callback):
		@wraps(env_step)
		def tracing_step():
			if len(env._queue):
				t, prio, eid, event = env._queue[0]
				callback(t, prio, eid, event)
			return env_step()
		return tracing_step
	env.step = get_wrapper(env.step, callback)

def monitor(data, t, prio, eid, event):
	data.append((t, eid, type(event)))

class WorkFlow:
	def __init__(self,topology,name):
		self.topology = topology
		self.name = name

	def receive(self,packet):
		return

	def start(self):
		print self.env.now,"start file transfer",self.name
		rate_limiter = 0
		while not self.completed:
			packet_size = min(self.block_size,self.data_size - self.received)
			if packet_size + rate_limiter > self.max_rate:
				rate_limiter = 0
				yield self.env.timeout(1)
			rate_limiter += packet_size
			packet_name = self.name+"-"+str(self.packet_total + 1)
			packet = Packet(topology=self.topology,size=packet_size,flow=self,name=packet_name,path=self.path)
			port_in = self.path[0]
			success = port_in.router.forward(packet=packet, port_in=port_in)
			if not success:
				rate_limiter -= packet_size
				yield self.env.timeout(1)
			else:	
				self.packet_total += 1	
				yield self.env.timeout(0)	


	def failed(self, packet,net_elem):
		if self.completed:
			return
		if net_elem != None:
			print self.env.now,self.name,"drop packet ",packet.name ,"where",net_elem.name
		else:
			print self.env.now,self.name,"drop packet ",packet.name ,'broken link'
		if self.env.now > (len(self.drop_data) - 1):
			padding = numpy.zeros(self.env.now - len(s,elf.drop_data) + 1)
			if len(padding) > 0:
				self.drop_data.extend(padding)
		self.drop_data[self.env.now] += 1
		self.packet_drop += 1




class DataTransfer:
	def __init__(self,name,src,dst,topology,data_size,max_rate,block_size=1,path=None):
		self.topology = topology
		self.env = self.topology.env
		self.name = name
		self.data_size = data_size
		self.received = 0
		self.path = path
		self.max_rate = max_rate
		self.packet_drop = 0
		self.packet_total = 0
		self.completed = False
		self.block_size = block_size
		self.start_time = self.env.now
		self.end_time = 0
		self.throughput_data = []
		self.drop_data = []
		self.src = src
		self.dst = dst
		#if self.path == None:



	def receive(self,packet):
		if self.completed:
			return
		self.received += packet.size
		# print self.env.now,self.name,"packet received",packet.name,packet.size,self.received
		if self.env.now > (len(self.throughput_data) - 1):
			padding = numpy.zeros(self.env.now - len(self.throughput_data) + 1)
			if len(padding) > 0:
				self.throughput_data.extend(padding)
		
		self.throughput_data[self.env.now] += packet.size

		if (self.received >= self.data_size):
			p = 100
			if self.packet_total != 0:
				p = self.packet_drop*100/self.packet_total
			self.completed = True
			self.end_time = self.env.now
			duration = self.start_time - self.end_time
			average_rate = packet.size / duration
			if len(self.throughput_data) > len(self.drop_data):
				self.drop_data.extend(numpy.zeros(len(self.throughput_data) - len(self.drop_data)))
			print self.env.now,self.name,'success',self.received,'packets',self.packet_total,'average',average_rate,'drop',self.packet_drop,' ',p,'%'

	def start(self):
		print self.env.now,"start file transfer",self.name
		rate_limiter = 0
		while not self.completed:
			packet_size = min(self.block_size,self.data_size - self.received)
			if packet_size + rate_limiter > self.max_rate:
				rate_limiter = 0
				yield self.env.timeout(1)
			rate_limiter += packet_size
			packet_name = self.name+"-"+str(self.packet_total + 1)
			packet = Packet(topology=self.topology, size=packet_size,flow=self,name=packet_name,path=self.path)
			port_in = self.path[0]
			success = port_in.router.forward(packet=packet, port_in=port_in)
			if not success:
				rate_limiter -= packet_size
				yield self.env.timeout(1)
			else:	
				self.packet_total += 1	
				yield self.env.timeout(0)	


	def failed(self, packet,net_elem):
		if self.completed:
			return
		if net_elem != None:
			print self.env.now,self.name,"drop packet ",packet.name ,"where",net_elem.name
		else:
			print self.env.now,self.name,"drop packet ",packet.name ,'broken link'
		if self.env.now > (len(self.drop_data) - 1):
			padding = numpy.zeros(self.env.now - len(self.drop_data) + 1)
			if len(padding) > 0:
				self.drop_data.extend(padding)
		self.drop_data[self.env.now] += 1
		self.packet_drop += 1

	def plot(self):
		#print self.throughput_data
		#print self.drop_data
		plt.plot(self.throughput_data,label=self.name + "throughput")
		plt.plot(self.drop_data,label=self.name + "drop")
		#plt.plot(self.throughput_data,self.drop_data)
		plt.xlabel('time in seconds')
		plt.ylabel('size')

class Packet:
	def __init__ (self,topology,name,size,flow,path=[]):
		self.topology = topology
		self.env = toplogy.env
		self.name = name
		self.size = size
		self.path = path
		self.flow = flow
		self.hop = 0

	def next_port(self, current_port):
		if not current_port in self.path:
			return None
		next_port = self.path[self.path.index(current_port) + 1]
		return next_port			

	def is_last_port(self, current_port):
		return self.path[-1] == current_port

	def receive(self):
		self.flow.receive(self)

	def failed(self,net_elem):
		if self.flow != None:
			self.flow.failed(packet=self,net_elem=net_elem)



class Router:
	def __init__(self,name,topology=None,capacity=None):
		self.topology = topology
		self.env = topology.env
		self.name = name
		self.all_ports = {}
		self.fabric_links = {}
		self.topology = topology
		self.capacity=capacity

	def forward(self, port_in, packet):
		if packet.is_last_port(current_port=port_in):
			packet.receive()
			return
		next_port = packet.next_port(current_port = port_in)
		if next_port != None:
			link = port_in.get_link_out(remote_port=next_port)
			return next_port.send(packet=packet, link_out=link)
		else:
			packet.failed(net_elem=port_in)

	def add_port(self,port=None,name=None,capacity=None):
		if port == None:
			if capacity == None:
				if self.capacity == None:
					print "either the router or the port must have a capacity set to something else than None"
					return None
				capacity = self.capacity
			port_nb = str(len(self.all_ports) + 1)
			if name == None:
				name =port_nb
			else:
				name = name + ":" + port_nb
			port = Port(name=name,topology=self.topology,capacity=capacity)
			port.router = self
		self.all_ports[port.name] = port
		for p in self.all_ports.values():
			if p == port:
				continue
			link_name_a_b = self.name + ":" + port.name + "->" + self.name + ":" + p.name
			if not link_name_a_b in self.fabric_links:
				link = Link(name=link_name_a_b,capacity=min(port.capacity,p.capacity),latency=0,topology=self.topology)
				self.fabric_links[link.name] = name
				port.links_out[link.name] = link
				p.links_in[link.name] = link
				link.port_in = port
				link.port_out = p
				self.topology.all_links[link.name] = link
			link_name_b_a = self.name + ":" + p.name + "->" + self.name + ":" + port.name
			if not link_name_b_a in self.fabric_links:
				link = Link(name=link_name_b_a,capacity=min(port.capacity,p.capacity),latency=0,topology=self.topology)
				self.fabric_links[link.name] = name
				port.links_out[link.name] = link
				p.links_in[link.name] = link
				link.port_in = port
				link.port_out = p
				self.topology.all_links[link.name] = link
		return port

	def __str__(self):
		return self.name
	def __repr__(self):
		return self.__str__()

class Port:
	def __init__ (self,name,topology,capacity):
		self.topology = topology
		self.env = topology.env
		self.name = name
		self.links_in = {}
		self.links_out = {}		
		self.capacity = capacity
		self.interface = simpy.Container(env=self.topology.env,capacity=self.capacity,init=self.capacity)
		if self.env != None:
			self.set_env(self.env)
		self.router = None

	def set_env(self, env):
		self.env = env
		self.env.process(self.release_interface())

	def release_interface(self):
		while True:
			amount = self.capacity - self.interface.level
			#print self.env.now,self.name,"transmit",self.capacity-self.interface.level,'remains',self.interface.level
			if amount > 0:
				yield self.interface.put(amount)
			yield self.env.timeout(1)

	def send(self,packet,link_out):
		if self.interface.level < packet.size:
			packet.failed(net_elem=self)
			return False
		self.env.process(self.do_send(packet=packet, link_out=link_out))
		return True

	def do_send(self,packet,link_out):
		#print self.env.now,self.name,"send",packet.name,packet.size,'avail capacity',self.interface.level,'drop',packet.flow.packet_drop
		if self.interface.level < packet.size:
			packet.failed(net_elem=self)
			return
		timeout = self.env.timeout(1)
		res = yield self.interface.get(packet.size) | timeout
		if timeout in res:
			packet.failed(net_elem=self)
		else:
			#print self.env.now,self.name,"send",packet.name,packet.size,'avail capacity',self.interface.level,'drop',packet.flow.packet_drop
			link_out.put(packet)

	def __str__(self):
		return self.name
		
class Link:
	def __init__(self,name, topology, latency=0, capacity=0):
		self.name = name
		self.topology = topology
		self.env = topology.env
		self.latency = latency
		self.capacity = 0
		if self.capacity != 0:
			self.store = simpy.Store(self.env, capacity=self.capacity)
		else:
			self.store = simpy.Store(self.env)
		if self.env != None:
			self.set_env(self.env)
		self.port_in = None
		self.port_out = None

	def set_env(self,env):
		self.env = env
		self.receive = self.env.process(self.receive())

	def latency(self, packet):
		yield self.env.timeout(self.latency)
		self.store.put(packet)

	def put(self, packet):
		if (self.latency >0):
			self.env.process(self.latency(packet))
		else:
			self.store.put(packet)
	
	def receive(self):
		# print self.env.now,self.name,'ready'
		while True:
			packet = yield self.store.get()
			if self.port_in == None or self.port_in.router == None:
				packet.failed(net_elem=self)
				return
			self.port_in.router.forward(packet=packet,port_in = self.port_in)
			
def plot_all(env,files):
	while True:
		for f in files:
			f.plot()
		plt.show()
		yield(env.timeout(1))

def plot_it():
	for f in _flows:
		f.plot()
	plt.legend()
	plt.show()	


class Endpoint(Router):
	def __init__(self,name,topology,capacity,rate=0):
		Router.__init__(self,name=name,capacity=capacity,topology=topology)
		self.rate = rate
		self.topology.all_routers[self.name] = self

	def connect(self,router,latency=0):
		if isinstance(router, basestring):
			if router in self.topology.all_routers:
				router = self.topology.all_routers[router]
			else:
				router = Router(name=router,capacity=capacity,topology=self.topology)
				self.topology.all_routers[router.name] = router
		self.topology.add_link(self, router, capacity=self.capacity, latency=latency)


class Topology:
	def __init__(self,name="Unknown",env=None,time_factor=1.0):
		self.name = name
		self.all_routers = {}
		self.all_links = {} 
		self.time_factor = time_factor
		self.env = env
		if self.env == None:
			 self.env = simpy.rt.RealtimeEnvironment(factor=self.time_factor,strict=False)

	def get_router(self,name):
		if name in self.routers:
			return self.routers[name]
		else:
			return None

	def add_routers(self,routers):
		for router in routers:
			self.add_router(router = router)

	def add_links(self, links):
		for router_a, router_b, capacity, latency in links:
			r_a = self.get_router(router_a)
			if r_a == None:
				print router_a, "does not exist"
				return None
			r_b = self.get_router(router_b)
			if r_b == None:
				print router_b, "does not exist"
				return None	
			self.add_link(router_a=r_a, router_b=r_b, capacity=capacity, latency=latency)

	def add_router(self, router):
		if isinstance(router,basestring) and not router in self.all_routers:
				router = Router(name=router, topology=self)
		else:
				rooter = self.all_routers[rooter]
		router.topology = self
		self.all_routers[router.name] = router


	def add_link(self, router_a, router_b, capacity, latency):
		if isinstance(router_a,basestring):
			if router_a in self.all_routers:
				router_a = self.all_routers[router_a]
			else:
				router = Router(name=router_a,capacity=capacity,topology=self)
				self.all_routers[router_a] = router
				router_a = rooter
		else:
			if not router_a.name in self.all_routers:
				self.all_routers[router_a.name] = router_a

		if isinstance(router_b,basestring):
			if router_b in self.all_routers:
				router_b = self.all_routers[router_b]
			else:
				router = Router(name=router_b,capacity=capacity,topology=self)
				self.all_routers[router_b] = router
				router_b = rooter
		else:
			if not router_b.name in self.all_routers:
				self.all_routers[router_b.name] = router_b 

		port_a = router_a.add_port(name=router_a.name + "->" + router_b.name,capacity=capacity)
		port_b = router_b.add_port(name=router_b.name + "->" + router_b.name,capacity=capacity)

		link_a_b = Link(name = router_a.name+":"+port_a.name+"->"+router_b.name+":"+router_b.name, latency=latency, capacity=capacity,topology=self)
		link_b_a = Link(name = router_b.name+":"+router_b.name+"->"+router_a.name+":"+port_a.name, latency=latency, capacity=capacity,topology=self)
		port_a.links_out[link_a_b] = link_a_b
		port_b.links_in[link_a_b] = link_a_b
		link_a_b.port_in = port_a
		link_a_b.port_out = port_b
		port_b.links_out[link_b_a] = link_b_a
		port_a.links_in[link_b_a] = link_b_a
		link_b_a.port_in = port_b
		link_b_a.port_out = port_a
		self.all_links[link_a_b.name] = link_a_b
		self.all_links[link_b_a.name] = link_b_a

	def background_event(self, tick=1):
		print "BACKGROUND", self.env._factor
		while True:
			print "TICK",self.env.now,1/self.env.factor
			yield self.env.timeout(1/self.env.factor)

	def start_simulation(self, duration):
		print "Simulation starts at ",self.env.now, "and will run until ", self.env.now + duration
		self.env.process(self.background_event())
		self.env.run(until=self.env.now + duration)
		print "Simulation stops at",self.env.now

	def stop_simulation(self):
		self.env.run(until=self.env.now +1)

	def get_graph(self):
		graph = nx.Graph()
		for link in self.all_links.values():
				port_a = link.port_in
				port_b = link.port_out
				graph.add_edge(port_a,port_b)
		return graph

	def draw(self):
		graph = self.get_graph()
		pos=nx.spring_layout(graph)
		nx.draw_networkx_edges(graph,pos)
		nx.draw_networkx_nodes(graph,pos,node_size=100,alpha=0.5,color='b')
		nx.draw_networkx_labels(graph,pos,font_size=8,font_family='sans-serif')
		plt.axis('off')
		plt.show()

	def test(self):
		print "Begin"

		topo = Topology("test topology", time_factor=1)

		topo.add_routers(['router1','router2'])
		topo.add_link(router_a='router1',router_b='router2',capacity=10,latency=0) 

		server1 = Endpoint(name='server1',topology=topo,capacity=10,rate=8)
		server1.connect('router1')
		server2 = Endpoint(name='server2',topology=topo,capacity=10,rate=8)
		server2.connect('router2')

		flow1 = DataTransfer(name="flow1",
		                     src=server1,
		                     dst=server2,
		                     data_size=1000,
		                     block_size=10,
		                     max_rate=8,
		                     topology=topo)

		print "start"
		topo.start_simulation(duration=20)
		print "stop"

