select
    product,
    site,
    scale,
    sub_scale,
    version,
    batch_no,
    columns(* exclude (sno, batch_no, source_file, product, site, scale, sub_scale, version))::varchar
from {{ source('raw', 'raw_eg12014_c_2nd_cell_inoculation_sec02_25l') }}
