with split_batch as (

    select
        product,
        site,
        scale,
        split_part(batch_no, '_', 1) as base_batch_id,
        split_part(batch_no, '_', 2) as replicate_label,
        five_days_duration,
        five_days_temp_max,
        five_days_temp_min,
        harvest_temp_max,
        harvest_temp_min
    from {{ ref('stg_eg12014_cell_culture_production_sec03') }}

)

select product, site, scale, base_batch_id, replicate_label, 'five_days_duration' as canonical_feature, five_days_duration as value
from split_batch
union all
select product, site, scale, base_batch_id, replicate_label, 'five_days_temp_max' as canonical_feature, five_days_temp_max as value
from split_batch
union all
select product, site, scale, base_batch_id, replicate_label, 'five_days_temp_min' as canonical_feature, five_days_temp_min as value
from split_batch
union all
select product, site, scale, base_batch_id, replicate_label, 'harvest_temp_max' as canonical_feature, harvest_temp_max as value
from split_batch
union all
select product, site, scale, base_batch_id, replicate_label, 'harvest_temp_min' as canonical_feature, harvest_temp_min as value
from split_batch


