import asyncio
import binascii
import os
from pathlib import Path
import shlex
import shutil
import time
from typing import BinaryIO, List
from celery import Celery
import subprocess

from Bio.Align.Applications import ClustalwCommandline, MuscleCommandline
from Bio import SeqIO

celery = Celery(__name__)

# Config file
default_config = 'celeryconfig'
celery.config_from_object(default_config)

API_ENDPOINT = os.getenv('API_ENDPOINT')

def build_command(base_command: str, params: dict) -> List[str]:
    command = [base_command]
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                command.append(f"--{key}")
        else:
            # all switches require a value
            if "unnamed" not in key:
                command.append(f"-{key}" if len(key) == 1 else f"--{key}")
            command.append(str(value))
    return command

@celery.task(name="assembly")
def run_spades(params: dict, id: str):
    os.makedirs(f"/workspace/{id}/assembly", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):
        args = build_command("spades.py", params)
        subprocess.run(args, check=True)
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    
@celery.task(name="fastp")
def run_fastp(params, id):
    os.makedirs(f"/workspace/{id}/qc", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):
        args = build_command("fastp", params)
        subprocess.run(args, check=True)
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    
@celery.task(name="fastqc")
def run_fastqc(params, id):
    os.makedirs(f"/workspace/{id}/qc", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):
        args = build_command("fastqc", params)
        subprocess.run(args, check=True)
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    
@celery.task(name="multiqc")
def run_multiqc(params, id):
    os.makedirs(f"/workspace/{id}/qc", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):
        args = build_command("multiqc", params)
        subprocess.run(args)
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    
@celery.task(name="bwa_mem")
def run_bwa_mem(filenames: List[str], id, out):
    os.makedirs(f"/workspace/{id}/mapping", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):
        #args = build_command("bwa", params)
        subprocess.run(['bwa', 'mem', *filenames, '-o', f"/workspace/{id}/mapping/{out}"], check=True)
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    
@celery.task(name="bwa_index")
def run_bwa_index(filenames: List[str], id: str):
    try:
        for filename in filenames:
            if os.path.exists(filename):
                #args = build_command(f"bwa index {filename}", {})
                subprocess.run(['bwa', 'index', filename], check=True, capture_output=True, text=True)
            else:
                raise FileNotFoundError(f"Workspace for ID {id} does not exist.")
    except Exception as e:
        print(e)

@celery.task(name="convert_to_bam")
def run_convert_to_bam(sam_file: str, bam_file: str, id: str):
    os.makedirs(f"/workspace/{id}/mapping", exist_ok=True)
    if os.path.exists(f"/workspace/{id}"):

        subprocess.run([f"samtools sort -n -O sam /workspace/{id}/mapping/{sam_file}.sam | samtools fixmate -m -O bam - /workspace/{id}/mapping/{bam_file}.fixmate.bam"], check=True, shell=True)
        #rm mappings/evol2.sam
        subprocess.run([f"samtools sort -O bam -o /workspace/{id}/mapping/{bam_file}.sorted.bam /workspace/{id}/mapping/{bam_file}.fixmate.bam"], check=True, shell=True)
        #rm mappings/evol2.fixmate.bam
        subprocess.run([f"samtools markdup -r -S /workspace/{id}/mapping/{bam_file}.sorted.bam /workspace/{id}/mapping/{bam_file}.sorted.dedup.bam"], check=True, shell=True)
        #rm mappings/evol2.sorted.bam
        subprocess.run([f"samtools view -h -b -q 20 /workspace/{id}/mapping/{bam_file}.sorted.dedup.bam > /workspace/{id}/mapping/{bam_file}.sorted.dedup.q20.bam"], check=True, shell=True)
        #rm mappings/evol2.sorted.dedup.bam

        subprocess.run([f"samtools faidx /workspace/{id}/assembly/scaffolds.fasta"], check=True, shell=True)
        # index mappings
        subprocess.run([f"bamtools index -in /workspace/{id}/mapping/{bam_file}.sorted.dedup.q20.bam"], check=True, shell=True)
    
    else:
        raise FileNotFoundError(f"Workspace for ID {id} does not exist.")