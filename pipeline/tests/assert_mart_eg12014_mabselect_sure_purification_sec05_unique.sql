select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_eg12014_mabselect_sure_purification_sec05') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
