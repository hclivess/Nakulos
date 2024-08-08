from pysnmp.hlapi import *
import json


def collect():
    with open('client_config.json', 'r') as config_file:
        config = json.load(config_file)

    snmp_targets = config.get('snmp_targets', [])
    results = {}

    for target in snmp_targets:
        hostname = target['hostname']
        community = target['community']
        oids = target['oids']

        target_results = {}
        for oid_name, oid in oids.items():
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData(community),
                       UdpTransportTarget((hostname, 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )

            if errorIndication:
                print(f"Error: {errorIndication}")
            elif errorStatus:
                print(f"Error: {errorStatus}")
            else:
                for varBind in varBinds:
                    target_results[oid_name] = str(varBind[1])

        results[hostname] = target_results

    return results


if __name__ == "__main__":
    print(collect())