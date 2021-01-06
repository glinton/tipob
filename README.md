# TIPOB
A connected "twist" on a familiar game. Track your performance in influxDB.

## Use

Report to influx by setting the following variables then passing the `--influx` flag to the game:
```sh
export INFLUX_TOKEN="abc123"
export INFLUX_ORG="abc123"
export INFLUX_ORGID="abc123"
export INFLUX_HOST="http://localhost:8086"
```
**note:** `--bucket` may need to also be specified on the first run to create the proper bucket.

Run on a raspberry pi implanted into a bopit (check code for which GPIO pins buttons should be connected to) by passing the `--pi` flag to the game.

Follow the audio prompts to play the game. Bop is mapped to `b`, Twist to `t`, and Pull to `p`.

View your results in your dashboard where you can run a flux query like this:
```
from(bucket: "tipob")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "tipob")
  |> filter(fn: (r) => r["_field"] == "reaction_time")
  |> sort(columns: ["_time"])
```

## Python Requirements
 - `pyaudio`         - core requirement
 - `RPi.GPIO`        - if running on the PI
 - `influxdb_client` - if reporting to InfluxDB (why wouldn't you :wink:)
