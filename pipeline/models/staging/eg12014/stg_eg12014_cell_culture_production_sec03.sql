select
    product,
    site,
    scale,
    batch_no,
    main_culture_in_2000_l_sub_duration_of_day_5_temperature_shift_h as five_days_duration,
    main_culture_in_2000_l_sub_temperature_day_0_to_5_max_degree_c as five_days_temp_max,
    main_culture_in_2000_l_sub_temperature_day_0_to_5_min_degree_c as five_days_temp_min,
    main_culture_in_2000_l_sub_temperature_day_5_to_11_max_degree_c as harvest_temp_max,
    main_culture_in_2000_l_sub_temperature_day_5_to_11_min_degree_c as harvest_temp_min
from {{ source('raw', 'raw_eg12014_cell_culture_production_sec03') }}
