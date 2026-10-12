"""Generate transport-batch arrival/departure feeds and controlled data defects."""

import copy
import datetime as dt
import random


def generate(base, groups=12):
    rng = random.Random(404)
    snapshots = {s: [] for s in ["arrivals", "departures", "capacity", "staffing"]}
    late = []
    for i, f in enumerate(base):
        date = dt.datetime.strptime(str(f["DateKey"]), "%Y%m%d").replace(tzinfo=dt.timezone.utc)

        def stamp(value):
            return value.isoformat().replace("+00:00", "Z")

        key = f"{f['DateKey']}:{f['TerminalKey']}"
        common = dict(
            version=1,
            updated_at=stamp(date + dt.timedelta(days=2)),
            DateKey=f["DateKey"],
            TerminalKey=f["TerminalKey"],
        )
        cap = dict(
            key=key,
            **common,
            **{
                k: f[k]
                for k in [
                    "AvailableSlots",
                    "OccupiedSlots",
                    "HandlingCapacity",
                    "PlannedVehicles",
                    "IncidentFlag",
                    "Incident",
                    "CO2Kg",
                ]
            },
            CostRatio=f["HandlingCost"] / f["Revenue"],
        )
        snapshots["capacity"].append(cap)
        staff = round(
            18 + f["PlannedVehicles"] / 35 + rng.uniform(-2, 2) - (3 if f["IncidentFlag"] else 0), 1
        )
        snapshots["staffing"].append(
            dict(
                key=key,
                **common,
                StaffHours=staff,
                PlannedStaffHours=round(18 + f["PlannedVehicles"] / 35, 1),
            )
        )
        units_left = f["Vehicles"]
        ontime_left = f["OnTimeVehicles"]
        for group in range(groups):
            units = units_left // (groups - group)
            ontime = min(units, ontime_left // (groups - group))
            units_left -= units
            ontime_left -= ontime
            booking = key + ":" + str(group)
            planned = date + dt.timedelta(hours=6, minutes=group * 25)
            actual = planned + dt.timedelta(minutes=f["DelayMinutes"])
            arrival = dict(
                key=booking,
                **common,
                Units=units,
                OnTimeUnits=ontime,
                planned=stamp(planned),
                actual=stamp(actual),
            )
            snapshots["arrivals"].append(arrival)
            if (i * groups + group) % 61 == 0:
                snapshots["arrivals"].append(copy.deepcopy(arrival))
            if (i * groups + group) % 199 != 0:
                snapshots["departures"].append(
                    dict(
                        key=booking,
                        **common,
                        departure=stamp(actual + dt.timedelta(hours=f["DwellHours"])),
                    )
                )
            if group == 0 and i % 31 == 0:
                corrected = copy.deepcopy(arrival)
                corrected.update(
                    version=2,
                    Units=units + 2,
                    OnTimeUnits=ontime + 1,
                    updated_at=stamp(date + dt.timedelta(days=8)),
                )
                late.append(corrected)
    invalid = copy.deepcopy(snapshots["arrivals"][1])
    invalid.update(key="bad-units", Units=-3)
    invalid_time = copy.deepcopy(snapshots["arrivals"][2])
    invalid_time.update(key="bad-time", actual="not-a-timestamp")
    unknown = copy.deepcopy(snapshots["arrivals"][3])
    unknown.update(key="bad-terminal", TerminalKey=99)
    conflict = copy.deepcopy(snapshots["arrivals"][4])
    conflict["Units"] += 1
    snapshots["arrivals"] += [invalid, invalid_time, unknown, conflict]
    corrected = copy.deepcopy(snapshots)
    corrected["arrivals"] += late
    return (
        snapshots,
        corrected,
        dict(
            late_corrections=len(late),
            invalid_records=3,
            same_version_conflicts=1,
            synthetic=True,
            grain="transport batch; Units is the vehicle count, not sample weight",
        ),
    )
