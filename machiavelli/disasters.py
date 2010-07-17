from machiavelli import dice

PLAGUE_TABLE = [
[''     , 'SWI'  , ''     , ''     , 'CAR'  , ''     , ''     , ''     , ''     , 'MON'  , 'CAP'  ],
['RAG'  , 'BOS'  , 'SLA'  , ''     , ''     , ''     , 'CRO'  , ''     , ''     , 'BARI' , 'TYR'  ],
['SAV'  , ''     , ''     , 'FRI'  , ''     , 'ROME' , ''     , 'MAR'  , 'PAV'  , ''     , ''     ],
[''     , 'SAL'  , 'VER'  , ''     , 'DAL'  , 'LUC'  , 'BOL'  , 'CARIN', 'PRO'  , ''     , ''     ],
[''     , ''     , 'TUR'  , 'SIE'  , 'MES'  , 'PAD'  , 'AUS'  , 'FER'  , ''     , ''     , ''     ],
['PAL'  , ''     , 'GEN'  , 'ALB'  , 'PISA' , 'TUN'  , 'AVI'  , 'MIL'  , ''     , ''     , 'SAR'  ],
['DUR'  , ''     , 'NAP'  , 'MOD'  , 'PER'  , 'CRE'  , 'VEN'  , 'FLO'  , ''     , ''     , ''     ],
[''     , 'BER'  , 'ANC'  , 'PAR'  , ''     , ''     , ''     , ''     , 'MAN'  , 'IST'  , ''     ],
['PIO'  , 'HUN'  , ''     , 'URB'  , ''     , ''     , ''     , ''     , 'TRE'  , ''     , 'COMO' ],
['ARE'  , 'FOR'  , ''     , ''     , ''     , ''     , ''     , 'OTR'  , ''     , 'AQU'  , 'SPO'  ],
['TRENT', 'HER'  , ''     , 'PIS'  , ''     , ''     , ''     , 'COR'  , ''     , 'PAT'  , 'SALZ' ]
]

FAMINE_TABLE = [
[''     , ''     , 'PRO'  , 'PAT'  , 'MOD'  , ''     , 'COR'  , 'ANC'  , ''     , ''     , ''     ],
[''     , 'PIO'  , ''     , ''     , ''     , ''     , ''     , 'TUN'  , ''     , ''     , 'PAL'  ],
['PER'  , ''     , 'OTR'  , 'PAD'  , 'SWI'  , 'CRE'  , ''     , ''     , 'HER'  , ''     , ''     ],
['FRI'  , ''     , 'BOL'  , 'SAL'  , 'VER'  , 'AUS'  , 'MIL'  , 'SIE'  , ''     , ''     , 'DUR'  ],
['MAR'  , 'RAG'  , ''     , 'CARIN', 'BER'  , 'PIS'  , 'SPO'  , ''     , ''     , 'HUN'  , ''     ],
[''     , 'BARI' , 'SLA'  , 'MON'  , 'URB'  , 'FOR'  , ''     , 'COMO' , 'TRENT', ''     , ''     ],
['FER'  , ''     , 'ROME' , 'PAV'  , ''     , ''     , 'ARE'  , ''     , 'SALZ' , 'ALB'  , 'GEN'  ],
[''     , ''     , 'CRO'  , ''     , 'FLO'  , 'TUR'  , 'MAN'  , 'CAP'  , 'TRE'  , ''     , ''     ],
['SAV'  , ''     , 'SAR'  , ''     , 'PAR'  , 'BOS'  , 'TYR'  , ''     , 'NAP'  , ''     , 'DAL'  ],
[''     , ''     , 'VEN'  , ''     , ''     , ''     , ''     , 'CAR'  , ''     , 'MES'  , 'PER'  ],
[''     , ''     , ''     , 'PISA' , 'AQU'  , 'AVI'  , 'LUC'  , ''     , 'IST'  , ''     , ''     ]
]

def get_year():
	return dice.roll_1d6()

def get_row(year):
	if year in [2, 3, 6]:
		return dice.roll_2d6() - 2
	else:
		return False

def get_column(year):
	if year in [4, 5, 6]:
		return dice.roll_2d6() - 2
	else:
		return False

def get_provinces(table):
	year = get_year()
	row = get_row(year)
	column = get_column(year)
	provinces = []
	if row:	
		for p in table[row]:
			provinces.append(p)
	if column:
		for r in table:
			provinces.append(r[column])
	return provinces

def get_plague():
	return get_provinces(PLAGUE_TABLE)

def get_famine():
	return get_provinces(FAMINE_TABLE)

