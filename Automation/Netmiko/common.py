# common.py - shared helpers for all EE8203 Netmiko scripts.

# Standard library and third-party dependency imports
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

# Global file paths for inventory definitions and log storage
INVENTORY_FILE = Path(__file__).parent / "inventory.yaml"
LOG_DIR = Path(__file__).parent / "logs"

# Reads and parses the YAML inventory configuration file
def load_inventory(path: Path = INVENTORY_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

# Configures dual logging to both console output and timestamped log files
def setup_logger(script_name: str) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = LOG_DIR / f"{script_name}_{stamp}.log"
    
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    
    fmt = logging.Formatter("%(asctime)s - %(levelname)-7s - %(message)s")
    
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setFormatter(fmt)
    
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    
    logger.addHandler(fh)
    logger.addHandler(sh)
    
    logger.info("Log file: %s", logfile)
    return logger

# Merges device specific entry with global defaults and environment variable overrides
def connection_params(entry: dict, defaults: dict) -> dict:
    return {
        "device_type": defaults["device_type"],
        "host": entry["host"],
        "username": os.environ.get("NET_USERNAME", defaults["username"]),
        "password": os.environ.get("NET_PASSWORD", defaults["password"]),
        "secret": os.environ.get("NET_SECRET", defaults["secret"]),
        "conn_timeout": defaults.get("conn_timeout", 30),
    }

# Establishes an SSH connection via Netmiko and enters enable privileged execution mode
def connect(name: str, params: dict, logger: logging.Logger):
    try:
        logger.info("[%s] connecting to %s...", name, params["host"])
        conn = ConnectHandler(**params)
        conn.enable()
        logger.info("[%s] connected", name)
        return conn
    except NetmikoAuthenticationException:
        logger.error("[%s] authentication failed - check credentials", name)
    except NetmikoTimeoutException:
        logger.error("[%s] SSH timeout - device unreachable on mgmt plane", name)
    except Exception as exc:
        logger.error("[%s] unexpected error: %s", name, exc)
    return None

# Compares running configuration against desired lines to ensure idempotent pushes
def missing_lines(running_config: str, desired_lines: list) -> list:
    present = {line.strip() for line in running_config.splitlines()}
    return [line for line in desired_lines if line.strip() not in present]

# Fetches full active running configuration from target network device
def get_running_config(conn) -> str:
    return conn.send_command("show running-config", read_timeout=90)
