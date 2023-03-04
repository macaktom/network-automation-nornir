# network_automation_nornir

Network automation + monitoring of Cisco, Juniper and Linux devices using Python framework Nornir.
Following configurations and features were automated:
1. Network interfaces
2. Routing protocols (RIP, OSPF, EIGRP) with route redistribution
3. Switching
3. Packet filtering (ACL)
4. NAT 
5. Creating Excel and HTML reports
6. Deleting parts of configurations or whole configuration
7. Configuration export to .txt and .conf formats
8. Restoring configurations (rollback)
9. Backup of configurations
10. Gathering metrics and showing them on CLI or Grafana

Used Python (Nornir framework) to automate this. For monitoring I also used InfluxDB for storing data and Grafana for visualization
Tested on Cisco and Juniper routers. Most of the features were also implemented for Juniper routers (OLIVE).

11. VSFTPD (FTP server) + TIG stack (Telegraf + InfluxDB + Grafana) configured using Nornir
