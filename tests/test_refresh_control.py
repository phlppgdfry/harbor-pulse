import datetime as dt,unittest
from harbor_pulse.refresh_control import evaluate
class RefreshControlTests(unittest.TestCase):
 def setUp(self):
  self.now=dt.datetime(2026,10,12,tzinfo=dt.timezone.utc)
  self.m=dict(ingested_at='2026-10-11T12:00:00Z',source_fact_difference=0,departure_coverage=.995,release_status='verified',source_kind='synthetic')
 def test_current_ingestion_passes(self):self.assertTrue(evaluate(self.m,self.now)['healthy'])
 def test_old_ingestion_fails_even_with_future_events(self):
  self.m['ingested_at']='2026-10-01T00:00:00Z';self.m['newest_source_event']='2026-12-31T00:00:00Z'
  self.assertIn('ingest_sla_exceeded',evaluate(self.m,self.now)['errors'])
 def test_future_or_naive_clock_is_rejected(self):
  self.m['ingested_at']='2026-10-13T00:00:00Z';self.assertIn('ingest_clock_in_future',evaluate(self.m,self.now)['errors'])
  self.m['ingested_at']='2026-10-11T00:00:00';self.assertIn('invalid_ingest_clock',evaluate(self.m,self.now)['errors'])
 def test_failed_quality_cannot_be_marked_fresh(self):
  self.m['departure_coverage']=.8;self.m['source_fact_difference']=2
  result=evaluate(self.m,self.now);self.assertFalse(result['healthy']);self.assertIn('coverage_failed',result['errors']);self.assertIn('reconciliation_failed',result['errors'])
