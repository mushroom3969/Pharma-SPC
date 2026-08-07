select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_eg12014_final_bulk_filling_and_fast_freezing_sec10') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
