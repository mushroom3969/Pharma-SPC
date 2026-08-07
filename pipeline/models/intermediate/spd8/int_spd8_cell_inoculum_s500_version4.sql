with unpivoted as (

    unpivot {{ ref('stg_spd8_cell_inoculum_s500_version4') }}
    on columns(* exclude (batch_no, product, site, scale, sub_scale, version))
    into name canonical_feature value value

)

select
    product,
    site,
    scale,
    split_part(batch_no, '_', 1) as batch_no,
    case when strpos(batch_no, '_') = 0 then '' else substr(batch_no, strpos(batch_no, '_') + 1) end as replicate_label,
    canonical_feature,
    try_cast(value as double) as value
from unpivoted
