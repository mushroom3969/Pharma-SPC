select *
from {{ source('raw', 'raw_eg12014_buffer_preparation_buffer') }}
