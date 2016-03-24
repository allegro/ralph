# DNS

## Introduction

Ralph integrated with DNSAAS [PowerDNS](https://github.com/allegro/django-powerdns-dnssec)


## Configuration

- ``ENABLE_DNSAAS_INTEGRATION`` - set to True if you want to enable DNSaaS integration
- ``DNSAAS_URL`` - Url to DNSAAS
- ``DNSAAS_TOKEN`` - API Token to DNSAAS
- ``DNSAAS_AUTO_PTR_ALWAYS`` - DNSAAS auto_ptr value, default is 2
- ``DNSAAS_AUTO_PTR_NEVER`` - DNSAAS auto_ptr value, default is 1

On the edit page of DataCenterAsset will appear a new tab DNS Edit.
DNS records are matched using DataCenterAssets IP
