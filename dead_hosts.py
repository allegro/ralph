DEAD_HOSTS = [
    "s43807.dc4.local",
    "s43808.dc4.local",
    "s43809.dc4.local",
    "s43810.dc4.local",
    "s43830.dc4.local",
    "s53107.dc5.alledc.net",
    "s53127.dc5.alledc.net",
    "t40734.te4.local",
    "t40736.te4.local",
    "t40737.te4.local",
    "t40738.te4.local",
    "t50205.te5.alledc.net",
    "t50221.te5.alledc.net",
    "t50222.te5.alledc.net",
    "t50223.te5.alledc.net",
    "t50224.te5.alledc.net",
]

for host in DEAD_HOSTS:
    print(f"ralph-ng.allegrogroup.com/api/dc-hosts/?hostname={host}")
