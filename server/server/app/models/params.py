from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class fastpParams(BaseModel):
    i: str
    I: str
    o: str
    O: str
    html: str
    json: str
    thread: int = 4
    detect_adapter_for_pe: Optional[bool]
    overrepresentation_analysis: Optional[bool]
    correction: Optional[bool]
    cut_right: Optional[bool]

class fastqcParams(BaseModel):
    o: str
    unnamed1: str
    unnamed2: str

class spadesParams(BaseModel):
    o: str
    file1: str = Field(..., alias='1')
    file2: str = Field(..., alias='2')
    model_config = ConfigDict(populate_by_name=True)

class multiqcParams(BaseModel):
    input_dir: str
    output_file: str
    flags: Optional[str] = None

class bwaMemParams(BaseModel):
    unamed1: str # reference genome
    unamed2: str # paired-end reads
    o: str

class bwaIndexParams(BaseModel):
    reference: str
    reads1: str = Field(..., alias='1')
    reads2: str = Field(..., alias='2')
    output: str
    threads: int = 4
    flags: Optional[str] = None