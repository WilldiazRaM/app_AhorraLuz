--VISTAS de KPI en el DW
--KPI 1 – Consumo mensual promedio (kWh) por hogar y tipo de vivienda
CREATE OR REPLACE VIEW ahorraluz_dw.kpi1_consumo_promedio_tipo_vivienda AS
SELECT
  f.anio,
  f.mes,
  du.tipo_vivienda,
  AVG(f.consumo_kwh) AS promedio_kwh
FROM ahorraluz_dw.fact_consumo_mensual f
JOIN ahorraluz_dw.dim_usuario du ON du.usuario_sk = f.usuario_sk
GROUP BY f.anio, f.mes, du.tipo_vivienda;



--KPI 2 – Tarifa promedio CLP/kWh por comuna
CREATE OR REPLACE VIEW ahorraluz_dw.kpi2_tarifa_promedio_comuna AS
SELECT
  du.comuna,
  AVG(f.tarifa_clp_por_kwh) AS tarifa_promedio
FROM ahorraluz_dw.fact_consumo_mensual f
JOIN ahorraluz_dw.dim_usuario du ON du.usuario_sk = f.usuario_sk
GROUP BY du.comuna;


--KPI 3 – Costo mensual estimado vs real por hogar
CREATE OR REPLACE VIEW ahorraluz_dw.kpi3_costo_estimado_vs_real AS
SELECT
  du.email,
  df.anio,
  df.mes,
  SUM(fp.costo_predicho_clp) AS costo_predicho,
  SUM(fp.costo_real_clp)     AS costo_real
FROM ahorraluz_dw.fact_prediccion fp
JOIN ahorraluz_dw.dim_usuario du ON du.usuario_sk = fp.usuario_sk
JOIN ahorraluz_dw.dim_fecha df   ON df.fecha_key = fp.periodo_inicio_key
GROUP BY du.email, df.anio, df.mes;


--KPI 4 Error medio de predicción (MAPE) por mes / comuna
CREATE OR REPLACE VIEW ahorraluz_dw.kpi4_mape_por_comuna AS
SELECT
  df.anio,
  df.mes,
  du.comuna,
  AVG(fp.error_kwh_pct) AS mape_pct
FROM ahorraluz_dw.fact_prediccion fp
JOIN ahorraluz_dw.dim_usuario du ON du.usuario_sk = fp.usuario_sk
JOIN ahorraluz_dw.dim_fecha df   ON df.fecha_key = fp.periodo_inicio_key
GROUP BY df.anio, df.mes, du.comuna;

--KPI 5 – Distribución de niveles de alerta
CREATE OR REPLACE VIEW ahorraluz_dw.kpi5_alertas_distribucion AS
SELECT
  da.codigo AS nivel_alerta,
  COUNT(*)  AS total_predicciones
FROM ahorraluz_dw.fact_prediccion fp
JOIN ahorraluz_dw.dim_alerta da ON da.alerta_sk = fp.alerta_sk
GROUP BY da.codigo;




