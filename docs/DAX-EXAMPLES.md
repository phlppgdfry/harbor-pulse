# Selected DAX with interpretation

These expressions are extracted from the published model source. Review their denominators and filter context, not just their syntax.

## Voertuigen

Vehicle units, not number of source batch rows.

```dax
Voertuigen = SUM(FactOps[Vehicles])
```

## Op tijd %

Vehicle-weighted numerator and denominator; inspect terminal/date filters.

```dax
Op tijd % = DIVIDE(SUM(FactOps[OnTimeVehicles]),[Voertuigen])
```

## Verblijftijd uur

Dwell is weighted by valid matched departure units, excluding missing departure outcomes.

```dax
Verblijftijd uur = DIVIDE(SUMX(FactOps,FactOps[DwellHours]*FactOps[CompleteDepartureUnits]),SUM(FactOps[CompleteDepartureUnits]))
```

## Vertrekdekking %

Coverage has all valid arrivals as denominator; a low value remains visible.

```dax
Vertrekdekking % = DIVIDE(SUM(FactOps[CompleteDepartureUnits]),[Voertuigen])
```

## Indicatieve besparing

Indicative value uses the selected usable fraction; this is not realized savings.

```dax
Indicatieve besparing = [Bespaarde wachturen]*[Tarief wachtuur]*[Benutbare fractie]
```

## Bron fact verschil

Reconciliation is loaded from independent pipeline quality evidence; do not subtract the same measure from itself.

```dax
Bron fact verschil = SUMX(FILTER(DQRule,DQRule[Regel]="Bron versus fact verschil"),DQRule[Aantal])
```

## Interview check

Select one terminal and one month. Explain which measures respond to that context and which disconnected annual evidence tables remain full-year snapshots. The report must label the latter clearly.
