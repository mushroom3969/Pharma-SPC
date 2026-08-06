select *
from {{ source('raw', 'raw_eg12014_cell_clarification_sec04') }}
