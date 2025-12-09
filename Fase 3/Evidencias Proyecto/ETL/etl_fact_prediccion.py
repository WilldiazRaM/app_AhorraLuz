from config import get_conn

def load_fact_prediccion():
    sql = """
    INSERT INTO ahorraluz_dw.fact_prediccion (
      prediccion_id,
      usuario_sk,
      alerta_sk,
      fecha_prediccion_key,
      periodo_inicio_key,
      periodo_fin_key,
      consumo_predicho_kwh,
      consumo_real_kwh,
      tarifa_clp_por_kwh_est,
      costo_predicho_clp,
      costo_real_clp,
      error_kwh_abs,
      error_kwh_pct
    )
    SELECT
      pc.id AS prediccion_id,
      du.usuario_sk,
      da.alerta_sk,
      pc.fecha_prediccion::date,
      pc.periodo_inicio::date,
      pc.periodo_fin::date,
      pc.consumo_predicho_kwh,
      pc.consumo_real_kwh,
      ult.tarifa_clp_por_kwh AS tarifa_estimada,
      pc.consumo_predicho_kwh * ult.tarifa_clp_por_kwh AS costo_predicho,
      CASE
        WHEN pc.consumo_real_kwh IS NOT NULL
        THEN pc.consumo_real_kwh * ult.tarifa_clp_por_kwh
        ELSE NULL
      END AS costo_real,
      CASE
        WHEN pc.consumo_real_kwh IS NOT NULL
        THEN ABS(pc.consumo_real_kwh - pc.consumo_predicho_kwh)
        ELSE NULL
      END AS error_abs,
      CASE
        WHEN pc.consumo_real_kwh IS NOT NULL
             AND pc.consumo_real_kwh <> 0
        THEN ABS(pc.consumo_real_kwh - pc.consumo_predicho_kwh)
             / pc.consumo_real_kwh * 100
        ELSE NULL
      END AS error_pct
    FROM predicciones_consumo pc
    JOIN ahorraluz_dw.dim_usuario du
         ON du.usuario_id = pc.usuario_id
    LEFT JOIN ahorraluz_dw.dim_alerta da
         ON da.nivel_alerta_id = pc.nivel_alerta_id
    LEFT JOIN ahorraluz_dw.v_ultima_tarifa_usuario ult
         ON ult.usuario_sk = du.usuario_sk
    LEFT JOIN ahorraluz_dw.fact_prediccion fp
         ON fp.prediccion_id = pc.id
    WHERE fp.prediccion_id IS NULL;   -- solo nuevas predicciones
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
    print("fact_prediccion actualizado (solo filas nuevas).")

if __name__ == "__main__":
    load_fact_prediccion()
