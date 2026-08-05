select *
from {{ source('raw', 'raw_eg12014_cell_inoculation_sec01_s2800') }}
