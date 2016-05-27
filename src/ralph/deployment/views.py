from django.http import HttpResponse


def ipxe(request, deployment_id):
    return HttpResponse('''#!ipxe
echo mac...............: ${mac}
echo ip................: ${ip}
echo netmask...........: ${netmask}
echo gateway...........: ${gateway}
echo dns...............: ${dns}
echo domain............: ${domain}
echo dhcp-server.......: ${dhcp-server}
echo filename..........: ${filename}
echo next-server.......: ${next-server}
echo hostname..........: ${hostname}
echo uuid..............: ${uuid}
echo serial............: ${serial}
echo .

set base-url http://192.168.200.1:8000

kernel ${base-url}/deployment/kernel

''', content_type='text/plain')


def kickstart(request, deployment_id):
    return HttpResponse('lang en_US', content_type='text/plain')
