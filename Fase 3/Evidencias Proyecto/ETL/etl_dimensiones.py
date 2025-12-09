from config import get_conn

def load_dim_fecha():
    sql = """
    CREATE SCHEMA IF NOT EXISTS ahorraluz_dw;

    CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_fecha (
      fecha_key   DATE PRIMARY KEY,
      anio        INT,
      mes         INT,
      dia         INT,
      nombre_mes  TEXT,
      trimestre   INT
    );

    INSERT INTO ahorraluz_dw.dim_fecha (fecha_key, anio, mes, dia, nombre_mes, trimestre)
    SELECT
      d::date                             AS fecha_key,
      EXTRACT(YEAR  FROM d)::int          AS anio,
      EXTRACT(MONTH FROM d)::int          AS mes,
      EXTRACT(DAY   FROM d)::int          AS dia,
      TO_CHAR(d, 'TMMonth')               AS nombre_mes,
      EXTRACT(QUARTER FROM d)::int        AS trimestre
    FROM generate_series('2023-01-01'::date, '2030-12-31'::date, interval '1 day') AS d
    ON CONFLICT (fecha_key) DO NOTHING;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)

def load_dim_usuario():
    sql = """
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

    INSERT INTO ahorraluz_dw.dim_usuario (
      usuario_id, email, nombres, apellidos,
      tipo_vivienda, comuna, creado_en, activo
    )
    SELECT
      u.id                        AS usuario_id,
      ai.email                    AS email,
      p.nombres                   AS nombres,
      p.apellidos                 AS apellidos,
      tv.nombre                   AS tipo_vivienda,
      c.nombre                    AS comuna,
      u.creado_en,
      u.activo
    FROM usuarios u
    LEFT JOIN auth_identidades ai ON ai.usuario_id = u.id
    LEFT JOIN perfiles p          ON p.usuario_id  = u.id
    LEFT JOIN cat_tipo_vivienda tv ON p.tipo_vivienda_id = tv.id
    LEFT JOIN direcciones d       ON d.usuario_id = u.id
    LEFT JOIN cat_comuna c        ON d.comuna_id  = c.id
    ON CONFLICT (usuario_id) DO UPDATE SET
      email = EXCLUDED.email,
      nombres = EXCLUDED.nombres,
      apellidos = EXCLUDED.apellidos,
      tipo_vivienda = EXCLUDED.tipo_vivienda,
      comuna = EXCLUDED.comuna,
      creado_en = EXCLUDED.creado_en,
      activo = EXCLUDED.activo;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)

def load_dim_dispositivo():
    sql = """
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

    INSERT INTO ahorraluz_dw.dim_dispositivo (
      dispositivo_id, usuario_id, nombre_dispositivo, tipo_dispositivo,
      potencia_promedio_w, horas_uso_diario, activo, fecha_registro
    )
    SELECT
      d.id,
      d.usuario_id,
      d.nombre,
      td.nombre,
      d.potencia_promedio_w,
      d.horas_uso_diario,
      d.activo,
      d.fecha_registro
    FROM dispositivos d
    LEFT JOIN cat_tipo_dispositivo td ON d.tipo_dispositivo_id = td.id
    ON CONFLICT (dispositivo_id) DO UPDATE SET
      usuario_id = EXCLUDED.usuario_id,
      nombre_dispositivo = EXCLUDED.nombre_dispositivo,
      tipo_dispositivo = EXCLUDED.tipo_dispositivo,
      potencia_promedio_w = EXCLUDED.potencia_promedio_w,
      horas_uso_diario = EXCLUDED.horas_uso_diario,
      activo = EXCLUDED.activo,
      fecha_registro = EXCLUDED.fecha_registro;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)

def load_dim_alerta():
    sql = """
    CREATE TABLE IF NOT EXISTS ahorraluz_dw.dim_alerta (
      alerta_sk        SERIAL PRIMARY KEY,
      nivel_alerta_id  SMALLINT UNIQUE,
      codigo           TEXT,
      descripcion      TEXT
    );

    INSERT INTO ahorraluz_dw.dim_alerta (
      nivel_alerta_id, codigo, descripcion
    )
    SELECT
      na.id,
      na.codigo,
      na.descripcion
    FROM cat_nivel_alerta na
    ON CONFLICT (nivel_alerta_id) DO UPDATE SET
      codigo = EXCLUDED.codigo,
      descripcion = EXCLUDED.descripcion;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)

if __name__ == "__main__":
    load_dim_fecha()
    load_dim_usuario()
    load_dim_dispositivo()
    load_dim_alerta()
    print("Dimensiones cargadas/actualizadas.")
