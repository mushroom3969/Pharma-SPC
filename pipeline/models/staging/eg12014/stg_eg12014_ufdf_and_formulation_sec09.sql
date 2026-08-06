select *
from {{ source('raw', 'raw_eg12014_ufdf_and_formulation_sec09') }}
