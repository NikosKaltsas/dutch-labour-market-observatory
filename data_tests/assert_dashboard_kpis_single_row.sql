select count(*) as row_count
from {{ ref('dashboard_kpis') }}
having count(*) <> 1
