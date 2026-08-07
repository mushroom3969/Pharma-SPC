select
    product,
    site,
    scale,
    sub_scale,
    version,
    batch_no,
    columns(* exclude (sno, batch_no, source_file, product, site, scale, sub_scale, version))::varchar
from {{ source('raw', 'raw_spd8_final_bulk_filling_and_fast_freezing_process_version4') }}
