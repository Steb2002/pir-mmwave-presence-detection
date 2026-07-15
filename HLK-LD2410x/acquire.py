import argparse
import csv
import time
import serial

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Porta seriale, es. COM5 o /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--trial", required=True)
    parser.add_argument("--group", default="G1")
    parser.add_argument("--ground_truth_presence", type=int, required=True)
    parser.add_argument("--ground_truth_state", default="unknown")

    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=2)
    time.sleep(2)

    start = time.time()

    with open(args.output, "w", newline="") as f:
        writer = None

        while time.time() - start < args.duration:
            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            if line.startswith("ERROR"):
                print(line)
                continue

            parts = line.split(",")

            if parts[0] == "timestamp_ms":
                header = parts + [
                    "pc_time_s",
                    "group_id",
                    "trial_id",
                    "scenario",
                    "ground_truth_presence",
                    "ground_truth_state"
                ]
                writer = csv.writer(f)
                writer.writerow(header)
                print(",".join(header))
                continue

            if writer is None:
                continue

            row = parts + [
                time.time(),
                args.group,
                args.trial,
                args.scenario,
                args.ground_truth_presence,
                args.ground_truth_state
            ]

            writer.writerow(row)
            print(",".join(map(str, row)))

    ser.close()

if __name__ == "__main__":
    main()