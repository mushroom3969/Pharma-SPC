select *
from {{ source('raw', 'raw_eg12014_final_bulk_filling_and_fast_freezing_sec10') }}
