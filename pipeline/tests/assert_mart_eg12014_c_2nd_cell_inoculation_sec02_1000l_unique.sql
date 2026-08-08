select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_eg12014_c_2nd_cell_inoculation_sec02_1000l') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
