select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_spd8_poros_50_hq_chromatography_and_depth_filtration_process_version4') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
