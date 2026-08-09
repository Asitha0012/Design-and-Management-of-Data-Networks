# verify.py - post-run state checks.

# Import sys for system exit codes and common helper utilities
import sys
from common import connect, connection_params, load_inventory, setup_logger

# Performs verification tests per device (SSH reachability, SNMP community, OSPF neighbor status, NAT statistics)
def check(name: str, entry: dict, inv: dict, is_router: bool, logger) -> list:
    conn = connect(name, connection_params(entry, inv["defaults"]), logger)
    if conn is None:
        return [("ssh-reachable", False)]
        
    results = [("ssh-reachable", True)]
    try:
        community = inv["snmp"]["community"]
        snmp_out = conn.send_command("show running-config | include snmp-server community")
        results.append(("snmp-community", community in snmp_out))
        
        if is_router:
            ospf = conn.send_command("show ip ospf neighbor")
            results.append(("ospf-neighbor-full", "FULL" in ospf))
            
        if "nat" in entry:
            nat = conn.send_command("show ip nat statistics")
            results.append(("nat-configured", "Dynamic mappings" in nat))
            
    except Exception as exc:
        logger.error("[%s] verification error: %s", name, exc)
        results.append(("verification-run", False))
    finally:
        if conn:
            conn.disconnect()
            
    return results

# Main entry point: iterates across all routers and switches, performs checks, and outputs PASS/FAIL summary
def main() -> int:
    logger = setup_logger("verify")
    inv = load_inventory()
    all_ok = True
    
    logger.info("%-10s %-20s %s", "DEVICE", "CHECK", "RESULT")
    
    for group, is_router in (("routers", True), ("switches", False)):
        for name, entry in inv[group].items():
            for check_name, passed in check(name, entry, inv, is_router, logger):
                logger.info("%-10s %-20s %s", name, check_name, "PASS" if passed else "FAIL")
                all_ok = all_ok and passed
                
    logger.info("==== OVERALL: %s ====", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1

# Script execution context guard
if __name__ == "__main__":
    sys.exit(main())
