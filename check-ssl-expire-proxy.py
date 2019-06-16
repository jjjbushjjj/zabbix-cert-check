#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import socket
from datetime import datetime
from http_proxy_connect import http_proxy_connect
from configobj import ConfigObj
import subprocess
from OpenSSL import SSL
import pprint

global to_zabbix
to_zabbix = {}


def metric_send(item, val, host, zbx_serv, zbx_serv_port):
    ''' Sends metric to zabbix '''

    print "This is sent to zabbix: item - %s value - %s" % (item, val)
    subprocess.call(["/usr/sbin/zabbix-sender",
                         "-z",
                         zbx_serv,
                         "-p",
                         zbx_serv_port,
                         "-s",
                         host,
                         "-k",
                         item,
                         "-o",
                         val
        ])


def exit_error(errcode, errtext):
    print errtext
    exit(errcode)


def pyopenssl_check_callback(connection, x509, errnum, errdepth, ok):
    ''' callback for pyopenssl ssl check'''

    good_cert = 0
    dns_alt_names = ''

    ex_count = x509.get_extension_count()
    for ext in range(0,ex_count):
        # print "EXTENSION %s" % ext
        extent = x509.get_extension(ext)
        if extent.__str__().find('CA:TRUE') >= 0:
           # print "don't check CA part just exit"
           return ok
        if extent.__str__().find('DNS') >= 0:
           # print "Yay!! find alt dns names!"
           # print extent.__str__()
           dns_alt_names = extent.__str__()
           break
    # Check if certificate consist host in it fields
    if x509.get_subject().commonName == HOST:
        good_cert = 1
        # print "1st check %s" % x509.get_subject().commonName
    if x509.get_subject().commonName.split('.')[1:] == HOST.split('.')[1:]:
        good_cert = 1
        # print "2nd check %s" % x509.get_subject().commonName.split('.')[1:]
    if dns_alt_names.find(HOST) >= 0: 
        good_cert = 1
        # print "3rd check %s" % dns_alt_names.find(HOST)

    if good_cert == 1:
        to_zabbix['commonName'] = x509.get_subject().commonName
        to_zabbix['serialNumber'] = x509.get_serial_number()
        pyopenssl_check_expiration(x509.get_notAfter())
        to_zabbix['altNames'] = dns_alt_names.replace('DNS:', '')

    return ok


def pyopenssl_check_expiration(asn1):
    ''' Return the numbers of day before expiration. False if expired.'''
    try:
        expire_date = datetime.strptime(asn1, "%Y%m%d%H%M%SZ")
        # print "Expire Date: %s" % expire_date
    except:
        exit_error(1, 'Certificate date format unknow.')

    expire_in = expire_date - datetime.now()
    if expire_in.days > 0:
        to_zabbix['expireInDays'] = expire_in.days
        return expire_in.days
    else:
        return False


def main():

    # Parse commandline
    parser = argparse.ArgumentParser()
    parser.add_argument('--hosts', help='specify an host to connect to. Could be list host1:port1 host2:port2 host3',
            nargs="+", type=str, default="")
    parser.add_argument('-c', '--conf', help='specify config file to use default /etc/zabbix/zabbix-cert-check.conf',
                        default='/etc/zabbix/zabbix-cert-check.conf')
    parser.add_argument('-d', '--debug', help='turn on debug if this option is set we do not send anything to zabbix',
                action="store_true")

    args = parser.parse_args()

    config = ConfigObj(args.conf)

    global HOST
    global PORT

    for HOST in args.hosts:

        hostport=HOST.split(':')
        HOST=hostport[0]
        try:
            PORT=int(hostport[1])
        except IndexError:
            PORT = 443

        print "HOST: %s PORT %s" % (HOST,PORT)

        # Check the DNS name
        try:
            socket.getaddrinfo(HOST, PORT)[0][4][0]
        except socket.gaierror as e:
            exit_error(1, e)

        # Connect using proxy or not
        if config['proxy'].as_bool('proxy_use'):
            (sock, status, response_headers) = http_proxy_connect((HOST, PORT),
                                    (config['proxy']['proxy_host'], config['proxy'].as_int('proxy_port')),
                                    (config['proxy']['proxy_user'], config['proxy']['proxy_pass']),
                                    {'Host': HOST })
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))

        try:
            ctx = SSL.Context(config['certcheck'].as_int('ssl_method'))
            ctx.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
                    pyopenssl_check_callback)
            ctx.load_verify_locations(config['certcheck']['ca_certs'])

            ssl_sock = SSL.Connection(ctx, sock)
            ssl_sock.set_connect_state()
            ssl_sock.set_tlsext_host_name(HOST)
            ssl_sock.do_handshake()

            ssl_sock.shutdown()

        except SSL.Error as e:
            exit_error(1, e)

        sock.close()

        if args.debug:
            # Don't send to zabbix, just print
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(to_zabbix)

        else:
            # Create items in zabbix
            dis_val = '{"data":[{"{#MACRO}":"'+HOST+'"}]}'
            metric_send('srv.discovery', dis_val,
                    config['zabbix']['zabbix_hostname'],
                    config['zabbix']['zabbix_server_url'],
                    config['zabbix']['zabbix_server_port'])
            # Send items to zabbix
            for (key, val) in to_zabbix.items():
                dis_key = 'srv.ex['+HOST+','+key+']'
                metric_send(dis_key, str(val),
                            config['zabbix']['zabbix_hostname'],
                        config['zabbix']['zabbix_server_url'],
                        config['zabbix']['zabbix_server_port'])


if __name__ == "__main__":
    main()
