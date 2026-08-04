select *
from {{ source('raw', 'raw_eg12014_qff_purification_sec06') }}
