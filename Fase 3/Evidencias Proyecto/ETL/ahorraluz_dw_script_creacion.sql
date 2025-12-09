CREATE SCHEMA IF NOT EXISTS ahorraluz_dw;

CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_usuario (
  usuario_sk       SERIAL PRIMARY KEY,
  usuario_id       UUID NOT NULL UNIQUE,
  email            TEXT,
  nombres          TEXT,
  apellidos        TEXT,
  tipo_vivienda    TEXT,
  comuna           TEXT,
  creado_en        TIMESTAMPTZ,
  activo           BOOLEAN
);

CREATE TABLE IF NOT EXISTS ahorraluz_dw.fact_consumo_mensual (
  fact_consumo_id       BIGSERIAL PRIMARY KEY,
  registro_consumo_id   BIGINT UNIQUE,
  usuario_sk            INT REFERENCES ahorraluz_dw.dim_usuario(usuario_sk),
  fecha_key             DATE,
  anio                  INT,
  mes                   INT,
  consumo_kwh           NUMERIC(12,4),
  costo_clp             NUMERIC(14,2),
  tarifa_clp_por_kwh    NUMERIC(14,6),
  fuente                TEXT
);

CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_fecha (
  fecha_key   DATE PRIMARY KEY,
  anio        INT,
  mes         INT,
  dia         INT,
  nombre_mes  TEXT,
  trimestre   INT
);

CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_dispositivo (
  dispositivo_sk       SERIAL PRIMARY KEY,
  dispositivo_id       BIGINT NOT NULL UNIQUE,
  usuario_id           UUID,
  nombre_dispositivo   TEXT,
  tipo_dispositivo     TEXT,
  potencia_promedio_w  NUMERIC(10,2),
  horas_uso_diario     NUMERIC(5,2),
  activo               BOOLEAN,
  fecha_registro       TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_alerta (
  alerta_sk        SERIAL PRIMARY KEY,
  nivel_alerta_id  SMALLINT UNIQUE,
  codigo           TEXT,
  descripcion      TEXT
);

CREATE TABLE IF NOT EXISTS ahorraluz_dw.fact_prediccion (
  fact_prediccion_id        BIGSERIAL PRIMARY KEY,
  prediccion_id             BIGINT UNIQUE,   -- id de predicciones_consumo
  usuario_sk                INT REFERENCES ahorraluz_dw.dim_usuario(usuario_sk),
  alerta_sk                 INT REFERENCES ahorraluz_dw.dim_alerta(alerta_sk),
  fecha_prediccion_key      DATE REFERENCES ahorraluz_dw.dim_fecha(fecha_key),
  periodo_inicio_key        DATE REFERENCES ahorraluz_dw.dim_fecha(fecha_key),
  periodo_fin_key           DATE REFERENCES ahorraluz_dw.dim_fecha(fecha_key),
  consumo_predicho_kwh      NUMERIC(12,4),
  consumo_real_kwh          NUMERIC(12,4),
  tarifa_clp_por_kwh_est    NUMERIC(14,6),
  costo_predicho_clp        NUMERIC(14,2),
  costo_real_clp            NUMERIC(14,2),
  error_kwh_abs             NUMERIC(12,4),
  error_kwh_pct             NUMERIC(6,2)
);

CREATE OR REPLACE VIEW ahorraluz_dw.v_ultima_tarifa_usuario AS
SELECT DISTINCT ON (usuario_sk)
  usuario_sk,
  tarifa_clp_por_kwh,
  fecha_key
FROM ahorraluz_dw.fact_consumo_mensual
WHERE tarifa_clp_por_kwh IS NOT NULL
ORDER BY usuario_sk, fecha_key DESC;




ALTER TABLE ahorraluz_dw.fact_consumo_mensual
ADD COLUMN IF NOT EXISTS dispositivo_sk INT NULL;

ALTER TABLE ahorraluz_dw.fact_consumo_mensual
  ADD CONSTRAINT fact_consumo_dispositivo_fk
  FOREIGN KEY (dispositivo_sk)
  REFERENCES ahorraluz_dw.dim_dispositivo(dispositivo_sk);