select
    product,
    site,
    scale,
    batch_no,
    replicate_label,
    canonical_feature,
    count(*) as n
from {{ ref('mart_spd8_media_preparation_protocol_for_spd8_version4') }}
group by product, site, scale, batch_no, replicate_label, canonical_feature
having count(*) > 1
