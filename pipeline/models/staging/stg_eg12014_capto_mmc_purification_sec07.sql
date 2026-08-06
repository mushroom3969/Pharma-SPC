select *
from {{ source('raw', 'raw_eg12014_capto_mmc_purification_sec07') }}
