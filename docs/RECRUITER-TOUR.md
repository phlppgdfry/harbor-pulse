# Harbor Pulse in five minutes

A synthetic terminal analytics case by Philippe Godfroy, developed with AI assistance.

## 0:00 - The business problem

Three fictional terminals need to reduce waiting without moving queues or treating every waiting hour as cash savings. The case separates operational indicators, data reliability, investment assumptions and experimental evidence.

## 0:45 - Can we trust the numbers?

The generator intentionally adds 216 duplicates, 36 late corrections, invalid records and missing departures. The ingestion pipeline versions business keys, quarantines conflicts and reconciles 366,910 corrected vehicle units to daily facts. Missing departure coverage is shown rather than replaced with zero dwell time.

Read [the SQL examples](../sql/reviewer_queries.sql), [pipeline tests](../tests/test_pipeline.py) and [source contracts](../contracts/source-contracts.json).

## 1:45 - What would management do?

Pilot dispatch/appointment slots first under the invented cost and benefit ranges. Count only the realizable fraction of time saved. Subtract annual operating costs and show implementation cost separately. A favorable assumption distribution does not prove realized savings.

See [the decision note](DECISION.md) and [the sensitivity evidence](../evidence/sensitivity.json).

## 2:45 - How would we test it?

The simulated pilot assigns two lanes within day blocks. The observed difference-in-differences is -7.06 minutes; the generator injected -6 minutes. Uncertainty is estimated by resampling paired days. Planning checks expose null rejection, smaller effects, missing days and control-lane spillover.

Read [the pre-registration protocol](PILOT-PREREGISTRATION.md).

## 3:45 - What can a technical reviewer inspect?

Inspect [selected DAX](DAX-EXAMPLES.md), [regression diagnostics](ROBUSTNESS.md), [the executable recovery drill](../scripts/cloud_operations.py), and [control status](CONTROL-STATUS.md). Run the case without a Microsoft account.

## 4:30 - Personal contribution and interview discussion

This is Philippe's portfolio project, developed with substantial AI implementation assistance. It is evidence of inspectable project work, not proof of unaided authorship, professional experience or achieved business impact. Personal competency should be assessed through explanation and live changes.

Useful questions: Why is punctuality weighted? Why is the realizable fraction necessary? Why do watermarks not filter ingestion? What breaks a causal interpretation? What would change with persistent lane assignment? How would you handle a failed deployment?

[Interview preparation and ownership](OWNERSHIP.md) gives an honest discussion guide.
