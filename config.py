"""Project-local credentials only; environment values take precedence."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
from runtime_paths import add_local_tools
add_local_tools()

def load_env():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):continue
            key,sep,value=line.partition('=')
            if sep:os.environ.setdefault(key.strip(),value.strip().strip('\"').strip("'"))

def setting(name,default=''):
    load_env()
    value=os.getenv(name,default)
    return value

def credential(name):
    value=setting(name)
    if not value:raise ValueError(f'Set {name} in this project’s .env file.')
    return value

def save_setting(name, value):
    """Update only a named project setting; never return its value to the UI."""
    if name not in {'LEC_API_KEY', 'OXEN_API_KEY', 'GENERATION_PROVIDER', 'REPLICATE_API_TOKEN', 'OXEN_STORAGE_REPO'}:
        raise ValueError('Unsupported setting.')
    if any(char in value for char in '\r\n'):
        raise ValueError('Use a single-line value.')
    path = ROOT / '.env'
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [line for line in lines if line.partition('=')[0].strip() != name]
    lines.append(name + '=' + value)
    temporary = ROOT / '.env.pending'
    temporary.write_text('\n'.join(lines) + '\n')
    temporary.replace(path)
    os.environ[name] = value
