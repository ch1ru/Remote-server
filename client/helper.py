import json
import os
import functools
import threading
import socket
import subprocess
import time
from http.server import SimpleHTTPRequestHandler
import client as client_module
from models.params import spadesParams, fastpParams, fastqcParams
import urllib.parse
import jwt
import time

from dotenv import load_dotenv

load_dotenv()

api_client = client_module.api_client
celery_client = client_module.celery_client

def get_workspaces():
    response = api_client.get(endpoint=f'/api/workspace')
    return response

def poll_for_result(task_id: str) -> str:
    response = celery_client.get(endpoint=f'api/tasks', params={})
    status = response[task_id]['state']
    return str(status).lower()
def wait_for_task(
    task_id: str, 
    poll_fn= None, 
    success_state: str = "success", 
    failure_state: str = "failure", 
    interval: float = 1.0, 
    callback=None,
    args=(),
    timeout: float | None = None, 
    verbose: bool = True):
    """Block until a task reaches the success_state.

    Args:
        task_id: the task identifier passed to the poll function.
        poll_fn: callable(task_id) -> status string. If None, uses poll_for_result.
        success_state: the lower-case status string considered success (default: "success").
        interval: seconds between polls.
        timeout: optional timeout in seconds. If exceeded, raises TimeoutError.
        verbose: if True, print status messages while waiting.

    Returns:
        The final status string (usually success_state).

    Raises:
        TimeoutError: if timeout is set and exceeded.
    """
    if poll_fn is None:
        poll_fn = poll_for_result

    start = time.time()
    while True:
        status = poll_fn(task_id)
        if status == success_state:
            return status
        if status == failure_state:
            raise RuntimeError(f"Task {task_id} failed.")
        if timeout is not None and (time.time() - start) > timeout:
            raise TimeoutError(f"Timeout waiting for task {task_id}; last status={status}")
        if verbose:
            print(f"Waiting for task {task_id} to complete... (status={status})")
        if callback is not None:
            callback(*args)
        time.sleep(interval) # set this to 0 because we have our own loader

def gen_igv_url(id: str) -> str:

    # URLs
    genome_url = f"http://localhost:5000/api/workspace/{id}/assembly/scaffolds.fasta"
    fai_url = f"http://localhost:5000/api/workspace/{id}/assembly/scaffolds.fasta.fai"
    bam_url = f"http://localhost:5000/api/workspace/{id}/mapping/anc.sorted.dedup.q20.bam"
    bai_url = f"http://localhost:5000/api/workspace/{id}/mapping/anc.sorted.dedup.q20.bam.bai"

    # Track JSON
    track_json = f'[{{"name":"Ancestor","url":"{bam_url}",indexURL:"{bai_url}","type":"alignment"}}]'
    encoded_tracks = urllib.parse.quote(track_json)

    # Full IGV URL

    token = gen_jwt_token()
    encoded_token = urllib.parse.quote(token)

    igv_url = (
        f"{os.getenv('DEV_IGV')}/index.html?"
        #f"genome={genome_url}&"
        #f"genomeIndex={fai_url}&"
        f"token={encoded_token}"
    )

    print(igv_url)
    return igv_url

def upload(filenames: list[str], id):
    # Open the file in binary mode
    files = []
    for filename in filenames:
        with open(filename, "rb") as f:
            pass  # Just to ensure the file can be opened
        files.append(('files', (os.path.basename(filename), open(filename, 'rb'), 'application/octet-stream')))

    response = api_client.post(endpoint='api/upload', files=files, data={'id': id})

    # Close file handles after upload
    for _, (name, fobj, _) in files:
        fobj.close()

    print(response)
    return response

def fastp(filenames: list[str], id):

    params = fastpParams(
        o=f"/workspace/{id}/trimmed/trimmed_{os.path.basename(filenames[0])}",
        O=f"/workspace/{id}/trimmed/trimmed_{os.path.basename(filenames[1])}",
        i=f"/workspace/{id}/uploads/{os.path.basename(filenames[0])}",
        I=f"/workspace/{id}/uploads/{os.path.basename(filenames[1])}",
        html=f"/workspace/{id}/qc/fastp/fastp_report.html",
        json=f"/workspace/{id}/qc/fastp/fastp_report.json",
        thread=4,
        cut_right=True,
        detect_adapter_for_pe=True,
        overrepresentation_analysis=True,
        correction=True,
    )

    data = {
        "id": id,
        "params": json.dumps(params.model_dump())  # JSON string
    }

    response = api_client.post(endpoint='api/qc/fastp', data=data)

    return response['job_id']

def fastqc(filenames: list[str], id):
    
    params = fastqcParams(
        o=f"/workspace/{id}/qc/fastqc",
        unnamed1=f"/workspace/{id}/trimmed/trimmed_{os.path.basename(filenames[0])}",
        unnamed2=f"/workspace/{id}/trimmed/trimmed_{os.path.basename(filenames[1])}",
    )

    data = {
        "id": id,
        "params": json.dumps(params.model_dump())  # JSON string
    }

    response = api_client.post(endpoint='api/qc/fastqc', data=data)

    return response['job_id']


def fastqc_report(id, filename):
    
    response = api_client.get(endpoint=f'api/qc/fastqc', params={'id': id, 'filename': filename}, raw=True)

    # response is a requests.Response object when raw=True
    try:
        body = response.text
    except Exception:
        body = str(response)

    # Create the directory if it doesn't exist
    current_dir = os.getcwd()
    qc_dir = os.path.join(current_dir, 'reports')
    os.makedirs(qc_dir, exist_ok=True)
    
    out_path = os.path.join(qc_dir, f'fastqc_report_{id}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(body)

    print(f'Wrote report to {out_path}')

    url, shutdown_callable = start_temp_server(qc_dir, os.path.basename(out_path), timeout=300)
    print(f"Temporary report URL: {url} (will auto-stop in 5 minutes)")

    return url

def fastp_report(id):
    
    response = api_client.get(endpoint=f'api/qc/fastp', params={'id': id, 'ext_type': 'html'}, raw=True)

    # response is a requests.Response object when raw=True
    try:
        body = response.text
    except Exception:
        body = str(response)

    # Create the directory if it doesn't exist
    current_dir = os.getcwd()
    qc_dir = os.path.join(current_dir, 'reports')
    os.makedirs(qc_dir, exist_ok=True)
    
    out_path = os.path.join(qc_dir, f'fastp_report_{id}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(body)

    print(f'Wrote report to {out_path}')

    url, shutdown_callable = start_temp_server(qc_dir, os.path.basename(out_path), timeout=300)
    print(f"Temporary report URL: {url} (will auto-stop in 5 minutes)")

    return url


def assemble(filenames: list[str], id):

    params = spadesParams(
        o=f"/workspace/{id}/assembly",
        file1=f"/workspace/{id}/trimmed/trimmed_{filenames[0]}",
        file2=f"/workspace/{id}/trimmed/trimmed_{filenames[1]}"
    )

    data = {
        "id": id,
        "params": json.dumps(params.model_dump(by_alias=True))  # JSON string
    }

    response = api_client.post(endpoint='api/assemble', data=data)

    return response['job_id']

def bwa_index(filenames: list[str], id):
    
    data = {
        "filenames": filenames,
        "id": id,
        "params": json.dumps({})  # Placeholder if needed in future
    }

    print(data)

    response = api_client.post(endpoint='api/mapping/bwa/index', data=data)

    return response['job_id']

def bwa_mem(filenames: list[str], id, out: str):
    
    data = {
        "filenames": filenames,
        "id": id,
        "out": out,
        "params": json.dumps({})  # Placeholder if needed in future
    }

    response = api_client.post(endpoint='api/mapping/bwa/mem', data=data)

    return response['job_id']

def samtools_convert(sam_file: str, bam_file: str, id: str):
    
    data = {
        "sam_file": sam_file,
        "bam_file": bam_file,
        "id": id,
    }

    response = api_client.post(endpoint='api/mapping/samtools', data=data)

    return response['job_id']

def get_bam(id: str, filename: str):

    # Create the directory if it doesn't exist
    current_dir = os.getcwd()
    local_path = os.path.join(current_dir, 'bam_files')
    os.makedirs(local_path, exist_ok=True)

    with api_client.get(endpoint=f'api/mapping/bam', params={'id': id, 'file': filename}, raw=True) as r:
        r.raise_for_status()  # raise exception if status != 200
        with open(os.path.join(local_path, f'{filename}_bam_{id}.bam'), "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):  # 1 MB chunks
                f.write(chunk)

    print(f'Wrote BAM to {local_path}')

    url, shutdown_callable = start_temp_server(local_path, f'{filename}_bam_{id}.bam', timeout=300)
    print(f"Temporary report URL: {url} (will auto-stop in 5 minutes)")

    return url

def gen_jwt_token():

    # Load RSA private key (TODO: add path to env)
    SECRET = b'6bb818ae58acf0e281802cd2ad104ae14691500357bdb41f86e6baf861a881a7'

    payload = {"sub": "device123", "aud": "igv-access", "exp": int(time.time()) + 300}

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    return token


# Start a temporary HTTP server to serve the qc directory
def start_temp_server(directory: str, filename: str, timeout: int = 300, bind_addr: str | None = None):
    """Start a background HTTP server serving `directory` on an ephemeral port using a subprocess.

    Returns (url, shutdown_callable). The server subprocess will be terminated after `timeout` seconds
    by a timer. The function returns immediately and the server runs independently.
    """
    # Find a free port on the desired interface
    bind_ip = bind_addr
    if not bind_ip:
        # Try to detect a non-loopback IPv4 address
        bind_ip = '127.0.0.1'
        try:
            # Connect to an external address to determine outbound interface IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                bind_ip = s.getsockname()[0]
        except Exception:
            # fallback stays localhost
            #bind_ip = '127.0.0.1'
            raise RuntimeError("Could not determine local IP address for binding temporary server.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((bind_ip, 0))
        port = s.getsockname()[1]

    # Build the command to run a simple HTTP server serving `directory`
    # Use python -m http.server for portability
    cmd = [
        'python3', '-m', 'http.server', str(port), '--bind', bind_ip, '--directory', directory
    ]

    # Start subprocess in background
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    def _shutdown():
        try:
            proc.terminate()
            # wait briefly
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        except Exception:
            pass

    # Schedule automatic shutdown
    timer = threading.Timer(timeout, _shutdown)
    timer.daemon = True
    timer.start()

    url = f'http://{bind_ip}:{port}/{filename}'
    return url, _shutdown