# zabbix-cert-check
zabbix ssl certificates checking
Easy to track certs expire date via zabbix and zabbix-sender

## Requirements

    python >= 2.7
    openssl >= 1
    zabbix-sender (goes with zabbix-proxy or zabbix-server)
    python module http_proxy_connect (included)
    
## Install

    1. Copy check-ssl-expire-proxy.py & http_proxy_connect.py to /usr/local/bin
    2. Copy zabbix-cert-check.conf to /etc/zabbix
    3. Ensure that you have all imported modules
        -   argparse
        -   socket
        -   datetime
        -   http_proxy_connect
        -   configobj
        -   subprocess
        -   OpenSSL
        -   pprint
        Most of them must be already present in default python installation

    Make shure it works:
        ./check-ssl-expire-proxy.py -h (Shows help)
    Modify /etc/zabbix/zabbix-cert-check.conf to suit your needs
    Run with -d flag and check the output.
    Example:
    ./check-ssl-expire-proxy.py --hosts google.com -d

    HOST: google.com PORT 443
{   'altNames': '*.google.com, *.android.com, *.appengine.google.com, *.cloud.google.com, *.google-analytics.com, *.google.ca, *.google.cl, *.google.co.in, *.google.co.jp, *.google.co.uk, *.google.com.ar, *.google.com.au, *.google.com.br, *.google.com.co, *.google.com.mx, *.google.com.tr, *.google.com.vn, *.google.de, *.google.es, *.google.fr, *.google.hu, *.google.it, *.google.nl, *.google.pl, *.google.pt, *.googleadapis.com, *.googleapis.cn, *.googlecommerce.com, *.googlevideo.com, *.gstatic.cn, *.gstatic.com, *.gvt1.com, *.gvt2.com, *.metric.gstatic.com, *.urchin.com, *.url.google.com, *.youtube-nocookie.com, *.youtube.com, *.youtubeeducation.com, *.ytimg.com, android.clients.google.com, android.com, developer.android.google.cn, g.co, goo.gl, google-analytics.com, google.com, googlecommerce.com, policy.mta-sts.google.com, urchin.com, www.goo.gl, youtu.be, youtube.com, youtubeeducation.com',
    'commonName': u'*.google.com',
    'expireInDays': 57,
    'serialNumber': 8319081633418726259 }

    Here 'altNames','commonName', 'expireInDays', 'serialNumber' is your zabbix items.

    4. Import template to zabbix (zbx_ssl_template.xml).
        this template consist 3 items prototypes (see above) 
        and 2 triggers prototypes: 
        cert expire in 20 days 
        serial number for cert has been changed
        The last one is useful if you have local cert stores that must consists working certs. 
    5. Create cronjob for check-ssl-expire-proxy.py
    6. Optionaly adjust triggers in template for your needs.
    7. Apply template to your host. And start collect data. 
  

    There is minor bug when you run this first time. Looks like there is some delay beetwen new items adds to host over discovery
    and be able to actually write data to these items. So just run same command again in 1-2 min will show your data.

 

    



