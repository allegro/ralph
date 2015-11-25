# Domain Contracts

## Introduction

TLDR; this is a domain ownership module, not DNS management tool. For DNS-records integration look at [this module](https://github.com/allegro/django-powerdns-dnssec) and PowerDNS server

When you are a big company, it's likely that, you have dozens of domains to manage. You have to keep track of its payments, to keep it alive, but the ownership is a issue too. Who is reponsible for managing particular domain? Who has rights to modify given DNS domain? Even more challenging is the scenario when the given subdomain is not used anymore. Trying to guess what person to contact to, and what was original purpose for it can be challenging.

That's why we created Domain Contracts module, which handles owhership, purpose and payments information related to the domains. It can be usable for domain trading companies as well. This modules plays nice with the django-powerdns-dnssec mentioned earlier.

## Quickstart - adding the domain

1. Click Domain -> Domains -> Add domain
2. Type "allegrogroup.com" for a domain name.
3. Leave parent unset, because it`s top level domain.
4. Service/env pair describes for what particular reason this domain was created for. Create new service called "Auction service", as an example, with the Environment called "production". For an internal domains we could use "testing" environment.
5. Choose required domain Status from list - for example "Active" if the domain is actively used.
5. Business segment is helpfull when you want to group domains together, create as an example "Marketplaces".
6. Choose Business Owner person which is responsible for domain and subdomain management.
7. Choose Technical Owner which is responsible for technical maintenance of a domain.
8. Domain Holder is a company which recieves the billing for a domain - for example "Allegro Group".
9. Now you have to fill domain price for given period. Type domain expiration date, registrant name (for example: "CNC", "Aftermarket"), and finally - domain price.
10. You can repeat this process to add appropriate subdomains, for example add new domain with name "test.allegrogroup.com" and parent set to "allegrogroup.com".
