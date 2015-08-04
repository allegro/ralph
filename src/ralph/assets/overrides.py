from dj.choices import Country as ChoiceCountry

ISO_3166 = (
    ('AF', 'AFG'), ('AX', 'ALA'), ('AL', 'ALB'), ('DZ', 'DZA'), ('AS', 'ASM'),
    ('AD', 'AND'), ('AO', 'AGO'), ('AI', 'AIA'), ('AQ', 'ATA'), ('AG', 'ATG'),
    ('AR', 'ARG'), ('AM', 'ARM'), ('AW', 'ABW'), ('AU', 'AUS'), ('AT', 'AUT'),
    ('AZ', 'AZE'), ('BS', 'BHS'), ('BH', 'BHR'), ('BD', 'BGD'), ('BB', 'BRB'),
    ('BY', 'BLR'), ('BE', 'BEL'), ('BZ', 'BLZ'), ('BJ', 'BEN'), ('BM', 'BMU'),
    ('BT', 'BTN'), ('BO', 'BOL'), ('BQ', 'BES'), ('BA', 'BIH'), ('BW', 'BWA'),
    ('BV', 'BVT'), ('BR', 'BRA'), ('IO', 'IOT'), ('BN', 'BRN'), ('BG', 'BGR'),
    ('BF', 'BFA'), ('BI', 'BDI'), ('KH', 'KHM'), ('CM', 'CMR'), ('CA', 'CAN'),
    ('CV', 'CPV'), ('KY', 'CYM'), ('CF', 'CAF'), ('TD', 'TCD'), ('CL', 'CHL'),
    ('CN', 'CHN'), ('CX', 'CXR'), ('CC', 'CCK'), ('CO', 'COL'), ('KM', 'COM'),
    ('CG', 'COG'), ('CD', 'COD'), ('CK', 'COK'), ('CR', 'CRI'), ('CI', 'CIV'),
    ('HR', 'HRV'), ('CU', 'CUB'), ('CW', 'CUW'), ('CY', 'CYP'), ('CZ', 'CZE'),
    ('DK', 'DNK'), ('DJ', 'DJI'), ('DM', 'DMA'), ('DO', 'DOM'), ('EC', 'ECU'),
    ('EG', 'EGY'), ('SV', 'SLV'), ('GQ', 'GNQ'), ('ER', 'ERI'), ('EE', 'EST'),
    ('ET', 'ETH'), ('FK', 'FLK'), ('FO', 'FRO'), ('FJ', 'FJI'), ('FI', 'FIN'),
    ('FR', 'FRA'), ('GF', 'GUF'), ('PF', 'PYF'), ('TF', 'ATF'), ('GA', 'GAB'),
    ('GM', 'GMB'), ('GE', 'GEO'), ('DE', 'DEU'), ('GH', 'GHA'), ('GI', 'GIB'),
    ('GR', 'GRC'), ('GL', 'GRL'), ('GD', 'GRD'), ('GP', 'GLP'), ('GU', 'GUM'),
    ('GT', 'GTM'), ('GG', 'GGY'), ('GN', 'GIN'), ('GW', 'GNB'), ('GY', 'GUY'),
    ('HT', 'HTI'), ('HM', 'HMD'), ('VA', 'VAT'), ('HN', 'HND'), ('HK', 'HKG'),
    ('HU', 'HUN'), ('IS', 'ISL'), ('IN', 'IND'), ('ID', 'IDN'), ('IR', 'IRN'),
    ('IQ', 'IRQ'), ('IE', 'IRL'), ('IM', 'IMN'), ('IL', 'ISR'), ('IT', 'ITA'),
    ('JM', 'JAM'), ('JP', 'JPN'), ('JE', 'JEY'), ('JO', 'JOR'), ('KZ', 'KAZ'),
    ('KE', 'KEN'), ('KI', 'KIR'), ('KP', 'PRK'), ('KR', 'KOR'), ('KW', 'KWT'),
    ('KG', 'KGZ'), ('LA', 'LAO'), ('LV', 'LVA'), ('LB', 'LBN'), ('LS', 'LSO'),
    ('LR', 'LBR'), ('LY', 'LBY'), ('LI', 'LIE'), ('LT', 'LTU'), ('LU', 'LUX'),
    ('MO', 'MAC'), ('MK', 'MKD'), ('MG', 'MDG'), ('MW', 'MWI'), ('MY', 'MYS'),
    ('MV', 'MDV'), ('ML', 'MLI'), ('MT', 'MLT'), ('MH', 'MHL'), ('MQ', 'MTQ'),
    ('MR', 'MRT'), ('MU', 'MUS'), ('YT', 'MYT'), ('MX', 'MEX'), ('FM', 'FSM'),
    ('MD', 'MDA'), ('MC', 'MCO'), ('MN', 'MNG'), ('ME', 'MNE'), ('MS', 'MSR'),
    ('MA', 'MAR'), ('MZ', 'MOZ'), ('MM', 'MMR'), ('NA', 'NAM'), ('NR', 'NRU'),
    ('NP', 'NPL'), ('NL', 'NLD'), ('NC', 'NCL'), ('NZ', 'NZL'), ('NI', 'NIC'),
    ('NE', 'NER'), ('NG', 'NGA'), ('NU', 'NIU'), ('NF', 'NFK'), ('MP', 'MNP'),
    ('NO', 'NOR'), ('OM', 'OMN'), ('PK', 'PAK'), ('PW', 'PLW'), ('PS', 'PSE'),
    ('PA', 'PAN'), ('PG', 'PNG'), ('PY', 'PRY'), ('PE', 'PER'), ('PH', 'PHL'),
    ('PN', 'PCN'), ('PL', 'POL'), ('PT', 'PRT'), ('PR', 'PRI'), ('QA', 'QAT'),
    ('RE', 'REU'), ('RO', 'ROU'), ('RU', 'RUS'), ('RW', 'RWA'), ('BL', 'BLM'),
    ('SH', 'SHN'), ('KN', 'KNA'), ('LC', 'LCA'), ('MF', 'MAF'), ('PM', 'SPM'),
    ('VC', 'VCT'), ('WS', 'WSM'), ('SM', 'SMR'), ('ST', 'STP'), ('SA', 'SAU'),
    ('SN', 'SEN'), ('RS', 'SRB'), ('SC', 'SYC'), ('SL', 'SLE'), ('SG', 'SGP'),
    ('SX', 'SXM'), ('SK', 'SVK'), ('SI', 'SVN'), ('SB', 'SLB'), ('SO', 'SOM'),
    ('ZA', 'ZAF'), ('GS', 'SGS'), ('SS', 'SSD'), ('ES', 'ESP'), ('LK', 'LKA'),
    ('SD', 'SDN'), ('SR', 'SUR'), ('SJ', 'SJM'), ('SZ', 'SWZ'), ('SE', 'SWE'),
    ('CH', 'CHE'), ('SY', 'SYR'), ('TW', 'TWN'), ('TJ', 'TJK'), ('TZ', 'TZA'),
    ('TH', 'THA'), ('TL', 'TLS'), ('TG', 'TGO'), ('TK', 'TKL'), ('TO', 'TON'),
    ('TT', 'TTO'), ('TN', 'TUN'), ('TR', 'TUR'), ('TM', 'TKM'), ('TC', 'TCA'),
    ('TV', 'TUV'), ('UG', 'UGA'), ('UA', 'UKR'), ('AE', 'ARE'), ('GB', 'GBR'),
    ('US', 'USA'), ('UM', 'UMI'), ('UY', 'URY'), ('UZ', 'UZB'), ('VU', 'VUT'),
    ('VE', 'VEN'), ('VN', 'VNM'), ('VG', 'VGB'), ('VI', 'VIR'), ('WF', 'WLF'),
    ('EH', 'ESH'), ('YE', 'YEM'), ('ZM', 'ZMB'), ('ZW', 'ZWE')
)


class Country(ChoiceCountry):
    @classmethod
    def iso2_to_iso3(cls, iso2_country):
        iso2_country = iso2_country.upper()
        return {k: v for k, v in ISO_3166}[iso2_country]

    @classmethod
    def iso3_to_iso2(cls, iso3_country):
        iso3_country = iso3_country.upper()
        return {v: k for k, v in ISO_3166}[iso3_country]
