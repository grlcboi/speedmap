#!/usr/bin/env python

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

class DumpResultCallback(CallbackBase):
  def v2_runner_on_ok(self, result, **kwargs):
    print(json.dumps({host.name: result._result}, indent=4))

class SilentCallback(CallbackBase):
  def v2_runner_on_ok(self, result, **kwargs):
    return

class IperfClientCallback(CallbackBase):
  def v2_runner_on_ok(self, result, **kwargs):
      host = result._host
      result = result._result
      stdout = result['stdout']
      stderr = result['stderr']
      
      if not stderr:
        print('        ' + stdout + '\n')
      elif stdout and stderr:
        print('        stdout: ' + stdout)
        print('        stderr: ' + stderr)
      else:
        print('        stderr: ' + stderr)
      print(json.dumps({host.name: result}, indent=4))

# instantiate callbacks
dump_results_callback = DumpResultCallback()
iperf_results_callback = IperfClientCallback()
silent_callback = SilentCallback()

Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])
# initialize needed objects
loader = DataLoader()
options = Options(connection='local', module_path='/path/to/mymodules', forks=100, become=None, become_method=None, become_user=None, check=False,
                  diff=False)
passwords = dict(vault_pass='secret')

# create inventory and pass to var manager
inventory = InventoryManager(loader=loader, sources=['test_hosts']) #replace with env var
variable_manager = VariableManager(loader=loader, inventory=inventory)

# run engine
def run_play(play, callback):
  tqm = None
  try:
      tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=options,
                passwords=passwords,
                stdout_callback=callback,  # Use our custom callback instead of the ``default`` callback plugin
            )
      result = tqm.run(play)
  finally:
      if tqm is not None:
          tqm.cleanup()

servers = clients = hosts = ['robotch', 'raspi', 'mint' ]

for server in servers:
  print('testing with server ' + server)
  # start iperf server
  iperf_cmd = 'iperf -s -D'
  play_source =  dict(
          name = "start iperf server",
          hosts = server,
          gather_facts = 'no',
          tasks = [
              dict(action=dict(module='command', args=iperf_cmd), register='shell_out')
           ]
      )
  play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
  
  result = run_play(play, silent_callback)

  for client in clients:
    print('    testing with client ' + client) 
    # ping from client to server
    iperf_cmd = 'iperf -t 1 -c ' + server + ' | tail -1 | sed \'s/.*\(...............\)/\\1/\' | sed \'s/^[ \\t]*//\''
    play_source =  dict(
            name = "start iperf client",
            hosts = client,
            gather_facts = 'no',
            tasks = [
                dict(action=dict(module='shell', args=iperf_cmd), register='shell_out')
             ]
        )
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
    result = run_play(play, iperf_results_callback)
  # kill iperf server
  kill_iperf_cmd = 'kill -9 $(pgrep iperf)'
  play_source =  dict(
          name = "kill iperf server",
          hosts = server,
          gather_facts = 'no',
          tasks = [
              dict(action=dict(module='shell', args=kill_iperf_cmd), register='shell_out')
           ]
      )
  play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
  result = run_play(play,silent_callback)

