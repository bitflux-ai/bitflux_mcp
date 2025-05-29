import sys
import os
import threading
import io
import pytest
import polars as pl
from http.server import BaseHTTPRequestHandler, HTTPServer

# Ensure downloadstats src is on sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../src')
))

from downloadstats.tool import download_stats
import downloadstats.downloadstats_pb2 as pb2

class DSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/downloadstats':
            length = int(self.headers.get('Content-Length', 0))
            self.rfile.read(length)
            # Build a Stats proto with embedded Parquet data
            msg = pb2.Stats()
            msg.timestamp = 'ts'
            msg.sample_rate = 100
            msg.unitsize = 1
            msg.head = 2
            msg.tail = 0
            msg.length = 3
            msg.system.mem_total = 1000
            msg.system.swap_total = 2000
            msg.system.num_cpus = 4
            # Create a simple DataFrame and serialize to Parquet
            df = pl.DataFrame({
                'col1': [1, 2, 3],
                'idle_cpu': [0, 0, 0],
                'reclaimable': [1, 1, 1],
            })
            buf = io.BytesIO()
            df.write_parquet(buf)
            msg.bitflux = buf.getvalue()
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
        pass

class NBHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/downloadstats':
            length = int(self.headers.get('Content-Length', 0))
            self.rfile.read(length)
            # Build a Stats proto without bitflux
            msg = pb2.Stats()
            msg.timestamp = 'ts'
            msg.sample_rate = 100
            msg.unitsize = 2
            msg.head = 1
            msg.tail = 1
            msg.length = 1
            msg.system.mem_total = 10
            msg.system.swap_total = 20
            msg.system.num_cpus = 2
            # Default bitflux is empty
            data = msg.SerializeToString()
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-protobuf')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class BadHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/downloadstats':
            length = int(self.headers.get('Content-Length', 0))
            self.rfile.read(length)
            # Build a Stats proto with corrupted bitflux data
            msg = pb2.Stats()
            msg.timestamp = 'x'
            msg.sample_rate = 0
            msg.unitsize = 1
            msg.head = 0
            msg.tail = 0
            msg.length = 0
            msg.system.mem_total = 0
            msg.system.swap_total = 0
            msg.system.num_cpus = 0
            msg.bitflux = b'invalid'
            data = msg.SerializeToString()
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-protobuf')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

@pytest.fixture(scope='function')
def http_server_success():
    server = HTTPServer(('127.0.0.1', 0), DSHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f'http://{host}:{port}'
    server.shutdown()
    thread.join()

@pytest.fixture(scope='function')
def http_server_no_bitflux():
    server = HTTPServer(('127.0.0.1', 0), NBHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f'http://{host}:{port}'
    server.shutdown()
    thread.join()

@pytest.fixture(scope='function')
def http_server_bad():
    server = HTTPServer(('127.0.0.1', 0), BadHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f'http://{host}:{port}'
    server.shutdown()
    thread.join()

def test_download_stats_success(http_server_success):
    result = download_stats(machine_key='mk', url=http_server_success)
    assert isinstance(result, dict)
    assert result['timestamp'] == 'ts'
    # Values come from JSON dict from protobuf -> strings for int64 fields
    assert result['sample_rate'] == '100'
    assert result['mem_total'] == '1000'
    assert result['swap_total'] == '2000'
    assert result['num_cpus'] == '4'
    # Check data rows
    data = result['data']
    assert isinstance(data, list)
    expected = [
        {'col1': 1, 'idle_cpu': 0, 'reclaimable': 1},
        {'col1': 2, 'idle_cpu': 0, 'reclaimable': 1},
        {'col1': 3, 'idle_cpu': 0, 'reclaimable': 1},
    ]
    assert data == expected
    # Check summary contains correct sum
    summary = result['summary']
    assert 'col1' in summary
    assert summary['col1']['sum'] == float(6)

def test_download_stats_no_server():
    result = download_stats(machine_key='x', url='http://127.0.0.1:0')
    assert result == {}

def test_download_stats_no_bitflux(http_server_no_bitflux):
    result = download_stats(machine_key='mk', url=http_server_no_bitflux)
    # Should return stats dict, not enhanced output
    assert isinstance(result, dict)
    assert result.get('timestamp') == 'ts'
    assert 'data' not in result
    assert 'summary' not in result
    # sampleRate and unitsize keys as from JSON
    assert result.get('sampleRate') == '100'
    assert result.get('unitsize') == 2

def test_download_stats_bad_parquet(http_server_bad):
    result = download_stats(machine_key='y', url=http_server_bad)
    assert result == {}