# push_snmp.py - push SNMPv2c monitoring config to ALL network devices.

# Import sys for CLI processing and helper functions from common module
import sys
from common import (
    connect,
    connection_params,
    load_inventory,
    missing_lines,
    setup_logger,
)

# Generates the list of SNMP IOS configuration commands from inventory SNMP settings
def snmp_lines(snmp: dict) -> list:
    return [
        f"snmp-server community {snmp['community']} RO",
        f"snmp-server host {snmp['trap_host']} version 2c {snmp['community']}",
        f"snmp-server location {snmp['location']}",
        f"snmp-server contact {snmp['contact']}",
        f"snmp-server enable traps {snmp['traps']}",
    ]

# Connects to device, checks running SNMP configuration, pushes missing lines, and saves state
def push(name: str, entry: dict, inv: dict, logger) -> str:
    conn = connect(name, connection_params(entry, inv["defaults"]), logger)
    if conn is None:
        return "failed"
        
    try:
        desired = snmp_lines(inv["snmp"])
        running = conn.send_command("show running-config | include snmp-server")
        to_push = missing_lines(running, desired)
        
        if not to_push:
            logger.info("[%s] SNMP already compliant - nothing to push", name)
            return "compliant"
            
        logger.info("[%s] pushing %d snmp-server line(s)", name, len(to_push))
        output = conn.send_config_set(to_push)
        logger.debug("[%s] device output:\n%s", name, output)
        conn.save_config()
        logger.info("[%s] configuration saved", name)
        return "ok"
    except Exception as exc:
        logger.error("[%s] SNMP push failed: %s", name, exc)
        return "failed"
    finally:
        conn.disconnect()

# Main entry point: targets all routers and switches from inventory, pushes SNMP, and logs summary
def main() -> int:
    logger = setup_logger("push_snmp")
    inv = load_inventory()
    all_devices = {**inv["routers"], **inv["switches"]}
    targets = sys.argv[1:] or list(all_devices.keys())
    results = {}
    
    for name in targets:
        if name not in all_devices:
            logger.error("[%s] not in inventory - skipped", name)
            results[name] = "unknown device"
            continue
        results[name] = push(name, all_devices[name], inv, logger)
        
    logger.info("==== SUMMARY (%d devices) ====", len(results))
    for name, result in results.items():
        logger.info(" %-10s: %s", name, result)
        
    failed = [n for n, r in results.items() if r not in ("ok", "compliant")]
    if failed:
        logger.error("FAILED devices: %s", ", ".join(failed))
        return 1 if failed else 0

# Script execution context guard
if __name__ == "__main__":
    sys.exit(main())
