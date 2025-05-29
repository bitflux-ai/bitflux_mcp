import threading
import sys
import os
import pytest
from http.server import BaseHTTPRequestHandler, HTTPServer

# Ensure downloadstats src is on sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../src')
))

from downloadstats.tool import machine_lookup
import downloadstats.downloadstats_pb2 as pb2

class MLHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/machinelookup':
            # Read and ignore request body
            length = int(self.headers.get('Content-Length', 0))
            self.rfile.read(length)
            # Construct a sample MachineLookupList proto
            msg = pb2.MachineLookupList()
            m1 = msg.machines.add()
            m1.machine_key = 'mk1'
            m1.deviceid = 'dev1'
            m1.organization_id = 'org1'
            m1.instance_id = 'inst1'
            m1.account_id = 'acct1'
            m1.ami_id = 'ami1'
            m2 = msg.machines.add()
            m2.machine_key = 'mk2'
            m2.deviceid = 'dev2'
            m2.organization_id = 'org2'
            m2.instance_id = 'inst2'
            m2.account_id = 'acct2'
            m2.ami_id = 'ami2'
            data = msg.SerializeToString()
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-protobuf')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress console logging during tests
        pass

@pytest.fixture(scope='module')
def http_server():
    # Start HTTP server on localhost with an ephemeral port
    server = HTTPServer(('127.0.0.1', 0), MLHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f'http://{host}:{port}'
    server.shutdown()
    thread.join()

def test_machine_lookup_success(http_server):
    # Call the client against our fake server
    result = machine_lookup(instance_id='ih', account_id='ah', url=http_server)
    assert isinstance(result, dict)
    assert 'machines' in result
    machines = result['machines']
    assert isinstance(machines, list)
    assert len(machines) == 2
    first = machines[0]
    assert first['machineKey'] == 'mk1'
    assert first['deviceid'] == 'dev1'
    assert first['organizationId'] == 'org1'
    assert first['instanceId'] == 'inst1'
    assert first['accountId'] == 'acct1'
    assert first['amiId'] == 'ami1'

def test_machine_lookup_no_server():
    # Point to an unused port, expect empty dict on error
    result = machine_lookup(instance_id='x', account_id='y', url='http://127.0.0.1:0')
    assert result == {}