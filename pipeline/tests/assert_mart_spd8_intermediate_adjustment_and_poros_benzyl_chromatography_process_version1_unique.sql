select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_spd8_intermediate_adjustment_and_poros_benzyl_chromatography_process_version1') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
