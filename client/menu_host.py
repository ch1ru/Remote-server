import argparse
import time

import qrcode
from helper import *
parser = argparse.ArgumentParser(
    prog='ProgramName',
    description='What the program does',
    epilog='Text at the bottom of help')

parser.add_argument('-c', '--command') 
parser.add_argument('-i', '--id')

args = parser.parse_args()

id = args.id  # Example job ID

if args.command == 'upload':
    upload(['data/anc_R1.fastq.gz', 'data/anc_R2.fastq.gz'], id)
elif args.command == 'fastp':
    task_id = fastp(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

    # wait for fastp to finish, then generate QR once
    wait_for_task(task_id, interval=1, verbose=True)
    report_url = fastp_report(id)
    img = qrcode.make(report_url)
    img.save(f'/qr/fastp_report_{id}_qrcode.png')
    
elif args.command == 'fastqc':
    task_id = fastqc(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

    # wait for fastqc to finish, then generate QR once
    wait_for_task(task_id, interval=1, verbose=True)
    # show just R1 report as example
    report_url = fastqc_report(id, filename='trimmed_anc_R1')
    img = qrcode.make(report_url)
    img.save(f'/qr/fastqc_report_{id}_qrcode.png')

elif args.command == 'assemble':
    task_id = assemble(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

    # wait for assembly/fastqc to finish
    wait_for_task(task_id, interval=1, verbose=True)
    # display complete message

elif args.command == 'map':
    task_id = bwa_index([f'/workspace/{id}/assembly/scaffolds.fasta'], id)

    wait_for_task(task_id, interval=1, verbose=True)

    task_id = bwa_mem([f'/workspace/{id}/assembly/scaffolds.fasta', f'/workspace/{id}/trimmed/trimmed_anc_R1.fastq.gz', f'/workspace/{id}/trimmed/trimmed_anc_R2.fastq.gz'], id, out='anc.sam')
    
    wait_for_task(task_id, interval=1, verbose=True)
    
    task_id = samtools_convert('anc', 'anc', id)

    wait_for_task(task_id, interval=1, verbose=True)

    igv_url = gen_igv_url(id)
    img = qrcode.make(igv_url)
    img.save(f'/qr/igv_{id}_qrcode.png')

elif args.command == "workspaces":
    workspaces = get_workspaces()
    print(workspaces)


else:
    print("Unknown command")