"""Audited incremental upserts over replayable synthetic source snapshots."""
import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path

SOURCES = ('arrivals', 'departures', 'capacity', 'staffing')

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(',', ':'))

def timestamp(value):
    if not isinstance(value,str):
        raise ValueError('invalid_timestamp_type')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone_required')
    return result

def connect(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS events(source TEXT, event_key TEXT, version INTEGER, digest TEXT,
        updated_at TEXT, payload TEXT, PRIMARY KEY(source,event_key));
    CREATE TABLE IF NOT EXISTS revisions(source TEXT,event_key TEXT,version INTEGER,digest TEXT,
        PRIMARY KEY(source,event_key,version));
    CREATE TABLE IF NOT EXISTS audit(run INTEGER,source TEXT,event_key TEXT,old_version INTEGER,
        new_version INTEGER,old_digest TEXT,new_digest TEXT);
    CREATE TABLE IF NOT EXISTS quarantine(run INTEGER,source TEXT,event_key TEXT,reason TEXT,payload TEXT);
    CREATE TABLE IF NOT EXISTS watermarks(source TEXT PRIMARY KEY,updated_at TEXT);
    CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY,status TEXT,inserted INTEGER DEFAULT 0,
        updated INTEGER DEFAULT 0,duplicates INTEGER DEFAULT 0,stale INTEGER DEFAULT 0,rejected INTEGER DEFAULT 0,
        input_rows INTEGER DEFAULT 0,message TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS facts(date_key INTEGER,terminal_key INTEGER,vehicles INTEGER,payload TEXT,
        PRIMARY KEY(date_key,terminal_key));
    ''')
    return db

def validate(source, row):
    if not isinstance(row.get('key'), str) or not row['key']:
        raise ValueError('missing_key')
    if type(row.get('version')) is not int or row['version'] < 1:
        raise ValueError('invalid_version')
    timestamp(row['updated_at'])
    if row.get('TerminalKey') not in (1,2,3):
        raise ValueError('unknown_terminal')
    dt.datetime.strptime(str(row['DateKey']), '%Y%m%d')
    if source == 'arrivals':
        if type(row.get('Units')) is not int or row['Units'] <= 0:
            raise ValueError('invalid_units')
        if type(row.get('OnTimeUnits')) is not int or not 0 <= row['OnTimeUnits'] <= row['Units']:
            raise ValueError('invalid_ontime_units')
        planned,actual=timestamp(row['planned']),timestamp(row['actual'])
        if int(planned.strftime('%Y%m%d')) != row['DateKey']:
            raise ValueError('planned_date_key_mismatch')
    elif source == 'departures':
        timestamp(row['departure'])
    elif source == 'capacity':
        if row['AvailableSlots'] <= 0 or not 0 <= row['OccupiedSlots'] <= row['AvailableSlots']:
            raise ValueError('invalid_capacity')
    elif source == 'staffing':
        if row['StaffHours'] <= 0 or row['PlannedStaffHours'] <= 0:
            raise ValueError('invalid_staffing')

def rebuild(db):
    records={source:{} for source in SOURCES}
    for row in db.execute('SELECT source,event_key,payload FROM events'):
        records[row['source']][row['event_key']]=json.loads(row['payload'])
    grouped={}
    rates={1:30,2:32,3:28}
    missing=0;invalid_departures=0
    for key,a in records['arrivals'].items():
        k=(a['DateKey'],a['TerminalKey'])
        group=grouped.setdefault(k,dict(Vehicles=0,OnTimeVehicles=0,DelayWeighted=0,DwellWeighted=0,
                                      CompleteDepartureUnits=0,MissingDepartureUnits=0))
        group['Vehicles']+=a['Units'];group['OnTimeVehicles']+=a['OnTimeUnits']
        delay=max(0,(timestamp(a['actual'])-timestamp(a['planned'])).total_seconds()/60)
        group['DelayWeighted']+=delay*a['Units']
        dep=records['departures'].get(key)
        if dep and dep['TerminalKey']==a['TerminalKey'] and dep['DateKey']==a['DateKey'] and timestamp(dep['departure'])>=timestamp(a['actual']):
            group['DwellWeighted']+=(timestamp(dep['departure'])-timestamp(a['actual'])).total_seconds()/3600*a['Units']
            group['CompleteDepartureUnits']+=a['Units']
        else:
            group['MissingDepartureUnits']+=a['Units'];missing+=1
            if dep:invalid_departures+=1
    db.execute('DELETE FROM facts')
    for (date,terminal),values in sorted(grouped.items()):
        key=f'{date}:{terminal}'
        cap=records['capacity'].get(key);staff=records['staffing'].get(key)
        if cap is None or staff is None:
            raise ValueError('daily_capacity_or_staffing_missing:'+key)
        complete=values['CompleteDepartureUnits']
        revenue=values['Vehicles']*rates[terminal]
        fact=dict(DateKey=date,TerminalKey=terminal,Vehicles=values['Vehicles'],PlannedVehicles=cap['PlannedVehicles'],
                  OnTimeVehicles=values['OnTimeVehicles'],Revenue=revenue,BudgetRevenue=cap['PlannedVehicles']*rates[terminal],
                  HandlingCost=round(revenue*cap['CostRatio']),DelayMinutes=values['DelayWeighted']/values['Vehicles'],
                  DwellHours=values['DwellWeighted']/complete if complete else 0,
                  CompleteDepartureUnits=complete,MissingDepartureUnits=values['MissingDepartureUnits'],
                  AvailableSlots=cap['AvailableSlots'],OccupiedSlots=cap['OccupiedSlots'],HandlingCapacity=cap['HandlingCapacity'],
                  IncidentFlag=cap['IncidentFlag'],Incident=cap['Incident'],CO2Kg=cap['CO2Kg'],
                  StaffHours=staff['StaffHours'],PlannedStaffHours=staff['PlannedStaffHours'])
        db.execute('INSERT INTO facts VALUES(?,?,?,?)',(date,terminal,fact['Vehicles'],canonical(fact)))
    source_units=sum(a['Units'] for a in records['arrivals'].values())
    fact_units=db.execute('SELECT COALESCE(SUM(vehicles),0) FROM facts').fetchone()[0]
    if source_units != fact_units:
        raise ValueError('source_fact_reconciliation_failed')
    return dict(source_vehicles=source_units,fact_vehicles=fact_units,difference=0,
                missing_departures=missing,invalid_departures=invalid_departures,fact_rows=len(grouped))

def ingest(db, snapshots, fail_after=None):
    """Scan snapshots, apply only unseen revisions; atomically update facts and watermarks.

    Watermarks are operational evidence, not a lossy timestamp-only filter. The
    current file adapter scans all rows so backdated corrections are not missed.
    """
    run=db.execute("INSERT INTO runs(status) VALUES('running')").lastrowid;db.commit()
    counts=dict(inserted=0,updated=0,duplicates=0,stale=0,rejected=0,input_rows=0)
    db.execute('BEGIN')
    try:
        for source in SOURCES:
            for record in snapshots.get(source,[]):
                counts['input_rows']+=1;key=str(record.get('key',''))
                try:validate(source,record)
                except (ValueError,KeyError,TypeError) as error:
                    counts['rejected']+=1
                    db.execute('INSERT INTO quarantine VALUES(?,?,?,?,?)',(run,source,key,str(error),canonical(record)));continue
                digest=hashlib.sha256(canonical(record).encode()).hexdigest();version=record['version']
                seen=db.execute('SELECT digest FROM revisions WHERE source=? AND event_key=? AND version=?',(source,key,version)).fetchone()
                if seen:
                    if seen['digest']==digest:counts['duplicates']+=1
                    else:
                        counts['rejected']+=1
                        db.execute('INSERT INTO quarantine VALUES(?,?,?,?,?)',(run,source,key,'conflicting_same_version',canonical(record)))
                    continue
                old=db.execute('SELECT * FROM events WHERE source=? AND event_key=?',(source,key)).fetchone()
                db.execute('INSERT INTO revisions VALUES(?,?,?,?)',(source,key,version,digest))
                if old and version < old['version']:
                    counts['stale']+=1;continue
                counts['updated' if old else 'inserted']+=1
                db.execute('INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?)',(source,key,version,digest,record['updated_at'],canonical(record)))
                db.execute('INSERT INTO audit VALUES(?,?,?,?,?,?,?)',(run,source,key,old['version'] if old else None,version,old['digest'] if old else None,digest))
                previous=db.execute('SELECT updated_at FROM watermarks WHERE source=?',(source,)).fetchone()
                if previous is None or timestamp(record['updated_at'])>timestamp(previous['updated_at']):
                    db.execute('INSERT OR REPLACE INTO watermarks VALUES(?,?)',(source,record['updated_at']))
                if fail_after and counts['inserted']+counts['updated']>=fail_after:
                    raise RuntimeError('injected_failure')
        reconciled=rebuild(db)
        db.execute('UPDATE runs SET status=?,inserted=?,updated=?,duplicates=?,stale=?,rejected=?,input_rows=? WHERE id=?',
                   ('succeeded',*[counts[k] for k in ['inserted','updated','duplicates','stale','rejected','input_rows']],run))
        db.commit()
        return dict(run=run,status='succeeded',**counts,**reconciled)
    except Exception as error:
        db.rollback();db.execute('UPDATE runs SET status=?,message=? WHERE id=?',('failed',str(error),run));db.commit();raise

def facts(db):
    return [json.loads(row['payload']) for row in db.execute('SELECT payload FROM facts ORDER BY date_key,terminal_key')]

def publication_gate(clean, run, minimum_coverage=.99, maximum_reject_rate=.001):
    units=sum(f['Vehicles'] for f in clean)
    coverage=sum(f['CompleteDepartureUnits'] for f in clean)/units if units else 0
    reject_rate=run['rejected']/run['input_rows'] if run['input_rows'] else 1
    checks=dict(reconciled=run['difference']==0,departure_coverage=coverage>=minimum_coverage,reject_rate=reject_rate<=maximum_reject_rate)
    if not all(checks.values()):raise ValueError('publication_gate_failed:'+canonical(checks))
    return dict(status='pass_with_warnings' if run['rejected'] or run['missing_departures'] else 'pass',checks=checks,
                departure_coverage=coverage,reject_rate=reject_rate,minimum_coverage=minimum_coverage,maximum_reject_rate=maximum_reject_rate)
