select quarter_end
from {{ ref('fct_vacancies') }}
where month(quarter_end) not in (3, 6, 9, 12)
   or quarter_end <> last_day(quarter_end)
