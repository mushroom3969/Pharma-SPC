select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_eg12014_cell_inoculation_sec01_s2800') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
