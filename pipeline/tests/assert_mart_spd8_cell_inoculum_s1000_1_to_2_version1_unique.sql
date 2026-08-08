select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_spd8_cell_inoculum_s1000_1_to_2_version1') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
