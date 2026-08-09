# configure_routers.py - configure R-CORE and R-EDGE from inventory.yaml.

# Import sys for CLI arguments and helper functions from common module
import sys
from common import (
    connect,
    connection_params,
    get_running_config,
    load_inventory,
    missing_lines,
    setup_logger,
)

# Generates interface configuration blocks (IP address, NAT inside/outside, description)
def interface_blocks(interfaces: list) -> list:
    blocks = []
    for iface in interfaces:
        lines = []
        if iface.get("description"):
            lines.append(f"description {iface['description']}")
        if iface.get("ip") == "dhcp":
            lines.append("ip address dhcp")
        else:
            lines.append(f"ip address {iface['ip']} {iface['mask']}")
        if iface.get("nat"):
            lines.append(f"ip nat {iface['nat']}")
        blocks.append((f"interface {iface['name']}", lines))
    return blocks

# Generates OSPF routing configuration commands including router-id and networks
def ospf_block(ospf: dict) -> tuple:
    lines = [f"router-id {ospf['router_id']}"]
    lines += [f"passive-interface {i}" for i in ospf.get("passive_interfaces", [])]
    lines += [f"network {n['net']} {n['wildcard']} area {n['area']}" for n in ospf.get("networks", [])]
    if ospf.get("default_information_originate"):
        lines.append("default-information originate always")
    return (f"router ospf {ospf['process']}", lines)

# Generates Standard Access List configuration block
def acl_block(name: str, permits: list) -> tuple:
    return (f"ip access-list standard {name}", list(permits))

# Combines all interface, OSPF, NAT, and VTY ACL blocks required for target router
def desired_blocks(router: dict, vty: dict) -> list:
    blocks = interface_blocks(router.get("interfaces", []))
    if "ospf" in router:
        blocks.append(ospf_block(router["ospf"]))
    
    if "nat" in router:
        nat = router["nat"]
        blocks.append(acl_block(nat["acl_name"], nat["acl_permits"]))
        blocks.append((f"ip nat inside source list {nat['acl_name']} interface {nat['overload_interface']} overload", []))
        
    if vty:
        blocks.append(acl_block(vty["vty_acl_name"], vty["vty_acl_permits"]))
        blocks.append(("line vty 0 4", [f"access-class {vty['vty_acl_name']} in"]))
    
    return blocks

# Filters out configuration lines already present in running config to make pushes idempotent
def push_lines(blocks: list, running: str) -> list:
    push = []
    for context, children in blocks:
        if not missing_lines(running, children or [context]):
            continue
        push.append(context)
        push += children
        if context.startswith("interface "):
            push.append("no shutdown")
    return push

# Connects to specified router, checks diff against running config, applies and saves changes
def configure(name: str, router: dict, inv: dict, logger) -> str:
    conn = connect(name, connection_params(router, inv["defaults"]), logger)
    if conn is None:
        return "failed"
        
    try:
        blocks = desired_blocks(router, inv.get("router_acls", {}))
        push = push_lines(blocks, get_running_config(conn))
        
        if not push:
            logger.info("[%s] already compliant - nothing to push (idempotent)", name)
            return "compliant"
            
        logger.info("[%s] pushing %d line(s):", name, len(push))
        for line in push:
            logger.debug("[%s] %s", name, line)
            
        logger.debug("[%s] device output:\n%s", name, conn.send_config_set(push))
        conn.save_config()
        logger.info("[%s] configuration saved (write memory)", name)
        return "ok"
    except Exception as exc:
        logger.error("[%s] configuration failed: %s", name, exc)
        return "failed"
    finally:
        conn.disconnect()

# Main entry point: iterates through target routers, pushes configuration, and logs summary
def main() -> int:
    logger = setup_logger("configure_routers")
    inv = load_inventory()
    targets = sys.argv[1:] or list(inv["routers"].keys())
    results = {}
    
    for name in targets:
        if name not in inv["routers"]:
            logger.error("[%s] not in inventory - skipped", name)
            results[name] = "unknown device"
            continue
        results[name] = configure(name, inv["routers"][name], inv, logger)
        
    logger.info("==== SUMMARY ====")
    for name, result in results.items():
        logger.info("%-8s: %s", name, result)
        
    return 0 if all(r in ("ok", "compliant") for r in results.values()) else 1

# Script execution context guard
if __name__ == "__main__":
    sys.exit(main())
