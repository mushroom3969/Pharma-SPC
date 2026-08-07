select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_eg12014_capto_mmc_purification_sec07') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
