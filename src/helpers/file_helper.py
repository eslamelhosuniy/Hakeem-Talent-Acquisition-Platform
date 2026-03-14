import uuid
import os

def generate_prefixed_filename(filename: str):
    """
    Generate unique filename with prefix
    """

    ext = filename.split(".")[-1]

    unique_prefix = uuid.uuid4().hex

    new_filename = f"{unique_prefix}_{filename}"

    return new_filename