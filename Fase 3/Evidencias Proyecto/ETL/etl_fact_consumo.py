from config import get_conn

def load_fact_consumo():
    sql = """
    INSERT INTO ahorraluz_dw.fact_consumo_mensual (
      registro_consumo_id,
      usuario_sk,
      dispositivo_sk,
      fecha_key,
      anio,
      mes,
      consumo_kwh,
      costo_clp,
      tarifa_clp_por_kwh,
      fuente
    )
    SELECT
      rc.id AS registro_consumo_id,
      du.usuario_sk,
      dd.dispositivo_sk,
      rc.fecha::date AS fecha_key,
      EXTRACT(YEAR  FROM rc.fecha)::int AS anio,
      EXTRACT(MONTH FROM rc.fecha)::int AS mes,
      rc.consumo_kwh,
      rc.costo_clp,
      CASE 
        WHEN rc.consumo_kwh > 0 AND rc.costo_clp IS NOT NULL
        THEN rc.costo_clp / rc.consumo_kwh
        ELSE NULL
      END AS tarifa,
      rc.fuente::text
    FROM registros_consumo rc
    JOIN ahorraluz_dw.dim_usuario du 
         ON du.usuario_id = rc.usuario_id
    LEFT JOIN ahorraluz_dw.dim_dispositivo dd
         ON dd.dispositivo_id = rc.dispositivo_id
    JOIN ahorraluz_dw.dim_fecha df 
         ON df.fecha_key = rc.fecha
    LEFT JOIN ahorraluz_dw.fact_consumo_mensual f
         ON f.registro_consumo_id = rc.id
    WHERE f.registro_consumo_id IS NULL;   -- solo nuevos
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
    print("fact_consumo_mensual actualizado (solo filas nuevas).")

if __name__ == "__main__":
    load_fact_consumo()
