from etl_dimensiones import (
    load_dim_fecha,
    load_dim_usuario,
    load_dim_dispositivo,
    load_dim_alerta,
)
from etl_fact_consumo import load_fact_consumo
from etl_fact_prediccion import load_fact_prediccion

if __name__ == "__main__":
    print("=== ETL AhorraLuz ===")
    load_dim_fecha()
    load_dim_usuario()
    load_dim_dispositivo()
    load_dim_alerta()
    load_fact_consumo()
    load_fact_prediccion()
    print("ETL completado.")
