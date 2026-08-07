select
    product,
    site,
    scale,
    sub_scale,
    version,
    batch_no,
    columns(* exclude (sno, batch_no, source_file, product, site, scale, sub_scale, version))::varchar
from {{ source('raw', 'raw_spd8_intermediate_adjustment_and_poros_benzyl_chromatography_process_version1') }}
