from ansible.runner import Runner

servers = ['robotch', 'raspi', 'mint' ]

clients = servers

tests = 0

# for every server
for server in servers:

	# start iperf server
	iperf_cmd = 'iperf -s -D'

	results = Runner(
		module_name = 'command',
		module_args = iperf_cmd,
		pattern = server
		).run()

	# for every client
	for client in clients:
		tests += 1
		print ('\n***** testing between client:' + client + ' and server:' + server + ' *****') 
		# ping from client to server
		ping_cmd = 'ping -c 1 ' + server + ' | tail -1 | awk -F \'/\' \'{print $5}\''
		#print('start ansible')
		results = Runner(
			module_name = 'shell',
			module_args = ping_cmd,
			pattern = client
			).run()
		#print('ansible done')
		ping_stdout = results['contacted'][client]['stdout']
		ping_stderr = results['contacted'][client]['stderr']

		latency = ping_stdout
		
		if ping_stderr:
			print (ping_stderr)
		else:
			print ('latency: ' + latency + ' ms')

		# iperf from client to server
		iperf_cmd = 'iperf -t 1 -c ' + server + ' | tail -1 | sed \'s/.*\(...............\)/\\1/\' | sed \'s/^[ \\t]*//\''
		#print('start ansible')
		results = Runner(
			module_name = 'shell',
			module_args = iperf_cmd,
			pattern = client
			).run()		
		#print('ansible done')
		iperf_stdout = results['contacted'][client]['stdout']
		iperf_stderr = results['contacted'][client]['stderr']

		throughput = iperf_stdout
		
		if iperf_stderr:
			print (iperf_stderr)
		else:
			print ('throughput: ' + throughput)

	#kill iperf server
	results = Runner(
		module_name = 'shell',
		module_args = 'kill -9 $(pgrep iperf)',
		pattern = server
		).run()

	iperf_s_killer_stdout = results['contacted'][server]['stdout']
	iperf_s_killer_stdout = results['contacted'][server]['stderr']



