# Automated Campus Network Design & Automation

This repository contains the network topologies, automation scripts, and deployment documentation for a secure, monitored, and programmatically managed hierarchical campus network.

## 🚀 Project Objectives & Core Features

* **Hierarchical Network Architecture:** A fully designed three-layer campus network topology utilizing VLANs, trunking, and robust inter-VLAN routing.
* **Traffic & Security Control:** Custom-formulated Access Control Lists (ACLs) engineered to enforce strict inter-departmental security policies.
* **Python Automation:** Programmatic device configuration and management powered by Python and the `Netmiko` library.
* **Infrastructure as Code (IaC):** Idempotent, repeatable switch configurations managed via customized `Ansible` playbooks.
* **Centralized Monitoring:** Real-time network health tracking and alerting platform deployed through `Zabbix`.
* **Industry-Standard Documentation:** Comprehensive operational guidelines, including a professional Method of Procedure (MOP) document.

## 🛠️ Tech Stack & Protocols

* **Automation & Scripting:** Python, Netmiko, Ansible
* **Network Monitoring:** Zabbix
* **Core Networking:** 3-Layer Hierarchical Design, VLANs, 802.1Q Trunking, Inter-VLAN Routing, ACLs
* **Documentation:** Method of Procedure (MOP)

---

> **Engineering Rationale:** All hardware selections, topology hierarchies, and automation tool sets within this repository are backed by dedicated engineering justifications to balance scalability, cost, and operational efficiency.

## 📋 Repository Structure & Deliverables

* `/automation` — Python scripts and Ansible playbooks for automated deployments.
* `/topology` — Network design diagrams and baseline configuration files.
* `/monitoring` — Zabbix templates and alerting configuration parameters.
* `/docs` — Professional Method of Procedure (MOP) manual and engineering rationale reports.
* `/testing` — Validation scripts and logs utilized during live testing and code walkthrough sessions.
