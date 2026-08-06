select *
from {{ source('raw', 'raw_eg12014_nanofiltration_sec08') }}
