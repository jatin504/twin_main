import pandas as pd
import threading
import time
from datetime import datetime

from state.tags import Tags


def read_forecast():
    df = pd.read_csv("./data/forecast.csv")

    # Parse timestamp
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # Keep only HH:MM
    df["Time"] = df["Timestamp"].dt.strftime("%H:%M")

    return df


def load_forecast(sim, df):
    now = datetime.now()

    # Round current time DOWN to nearest 15-minute slot
    forecast_minute = (now.minute // 15) * 15

    current_time_str = f"{now.hour:02d}:{forecast_minute:02d}"

    row = df[df["Time"] == current_time_str]

    if row.empty:
        print(f"[Forecast] No forecast found for {current_time_str}")
        return

    load_power = row.iloc[0]["Forecast_Load"]

    print(
        f"[Forecast] {now.strftime('%H:%M:%S')} "
        f"-> slot {current_time_str} -> {load_power}"
    )

    sim.plant_database.device(
        sim.plant_device_id
    ).set(
        Tags.Network.LOAD_POWER,
        load_power
    )


def forecast_worker(sim):
    # df = read_forecast()

    print("[Forecast] Worker started")

    # Prevent updating multiple times during the same minute
    last_minute = None

    while True:
        now = datetime.now()

        current_minute = now.strftime("%Y-%m-%d %H:%M")

        # Update once every minute
        if current_minute != last_minute:
            last_minute = current_minute

            try:
                df = read_forecast()
                load_forecast(sim, df)
            except Exception as e:
                print(f"[Forecast] Error: {e}")

        # Check every second
        time.sleep(1)


def start_forecast_thread(sim):
    thread = threading.Thread(
        target=forecast_worker,
        args=(sim,),
        daemon=True,
        name="forecast-worker"
    )

    thread.start()

    return thread
