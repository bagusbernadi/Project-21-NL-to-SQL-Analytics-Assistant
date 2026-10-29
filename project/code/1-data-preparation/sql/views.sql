-- View KPI: satu sumber rumus untuk asisten, dashboard, dan cek silang (definisi di docs/schema.md).
CREATE VIEW v_production AS
SELECT date, shift, station, model, input_qty, ok_first_pass, ng_qty,
       ok_first_pass * 1.0 / input_qty AS fpy, ng_qty * 1.0 / input_qty AS ng_rate
FROM production_daily
WHERE input_qty > 0 AND ng_qty >= 0 AND ok_first_pass >= 0 AND ng_qty <= input_qty AND ok_first_pass + ng_qty = input_qty;

CREATE VIEW v_kpi_station AS
SELECT s.seq, p.station, SUM(p.input_qty) AS input_qty, SUM(p.ok_first_pass) AS ok_first_pass, SUM(p.ng_qty) AS ng_qty,
       SUM(p.ok_first_pass) * 1.0 / SUM(p.input_qty) AS fpy, SUM(p.ng_qty) * 1.0 / SUM(p.input_qty) AS ng_rate
FROM v_production p JOIN dim_station s ON s.station = p.station
GROUP BY s.seq, p.station;

CREATE VIEW v_kpi_station_shift AS
SELECT station, shift, SUM(input_qty) AS input_qty, SUM(ng_qty) AS ng_qty,
       SUM(ok_first_pass) * 1.0 / SUM(input_qty) AS fpy, SUM(ng_qty) * 1.0 / SUM(input_qty) AS ng_rate
FROM v_production GROUP BY station, shift;

CREATE VIEW v_pareto_defect AS
SELECT d.defect_code, dd.defect_name, dd.station, dd.category, SUM(d.qty) AS qty,
       SUM(d.qty) * 1.0 / SUM(SUM(d.qty)) OVER () AS share,
       SUM(SUM(d.qty)) OVER (ORDER BY SUM(d.qty) DESC, d.defect_code) * 1.0 / SUM(SUM(d.qty)) OVER () AS cum_share
FROM defect_log d JOIN dim_defect dd ON dd.defect_code = d.defect_code
GROUP BY d.defect_code, dd.defect_name, dd.station, dd.category;

CREATE VIEW v_trend_week AS
SELECT date_trunc('week', date)::DATE AS week_start, SUM(input_qty) AS input_qty, SUM(ng_qty) AS ng_qty,
       SUM(ng_qty) * 1.0 / SUM(input_qty) AS ng_rate
FROM v_production GROUP BY 1;

CREATE VIEW v_rty_model AS
WITH f AS (SELECT model, station, SUM(ok_first_pass) * 1.0 / SUM(input_qty) AS fpy FROM v_production GROUP BY model, station)
SELECT model, EXP(SUM(LN(fpy))) AS rty FROM f GROUP BY model;
