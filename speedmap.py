from ansible.runner import Runner

servers = ['raspi', 'proxbox', 'mint']

clients = servers

# for every server
for server in servers:

	# start iperf server
	iperf_cmd = 'iperf -s -D'

	results = Runner(
		module_name = 'command',
		module_args = iperf_cmd,
		pattern = server
		).run()

	#for every client
	for client in clients:
		print ('***** testing between ' + client + ' to ' + server + '*****') 
		#ping from client to server
		ping_cmd = 'ping -c 1 ' + server + ' | tail -1 | awk -F \'/\' \'{print $5}\''

		results = Runner(
			module_name = 'shell',
			module_args = ping_cmd,
			pattern = client
			).run()

		ping_stdout = results['contacted'][client]['stdout']
		ping_stderr = results['contacted'][client]['stderr']

		latency = ping_stdout
		print ('latency from ' + client + ' to ' + server + ': ' + latency + 'ms')
		print (ping_stderr)

		#iperf from client to server
		iperf_cmd = 'iperf -t 1 -c ' + server + ' | tail -1 | sed \'s/.*\(...............\)/\\1/\''

		results = Runner(
			module_name = 'shell',
			module_args = iperf_cmd,
			pattern = client
			).run()		

		iperf_stdout = results['contacted'][client]['stdout']
		iperf_stderr = results['contacted'][client]['stderr']

		throughput = iperf_stdout
		print ('throughput from ' + client + ' to ' + server + ': ' + throughput)
		print (ping_stderr)
