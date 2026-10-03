import csv
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from neiron.contract import PacketError, stamp, DEVICE, UNIT
from neiron.service import Service
from neiron.server import Server, CSV_HEADERS

class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    def __call__(self): return self.now
    def advance(self, seconds=1): self.now += timedelta(seconds=seconds)

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="neiron-test-")
        self.path=Path(self.temp.name)/"test.sqlite3"
        self.clock=Clock()
        self.s=Service(self.path,self.clock)
    def tearDown(self):
        self.s.close()
        self.temp.cleanup()
    def start(self,scenario="normal"):
        self.s.control({"action":scenario})
        self.s.control({"action":"start"})
    def ticks(self,n):
        for _ in range(n): self.clock.advance(); self.s.tick()
    def active(self,kind): return self.s.alarms.active(kind)
    def test_normal_and_stop_hide_values(self):
        self.assertEqual(self.s.status()["state"],"stopped")
        self.start(); self.ticks(2)
        current=self.s.status()["current"]
        self.assertEqual(current["vibration_unit"],UNIT)
        self.assertEqual(self.s.status()["state"],"normal")
        self.s.control({"action":"stop"})
        self.assertIsNone(self.s.status()["current"])
        self.assertIsNotNone(self.s.status()["last_received_at"])
    def test_temperature_start_ack_recover_and_persist(self):
        self.start("hot"); self.ticks(3)
        self.assertIsNone(self.active("temperature"))
        self.ticks(1); alarm=self.active("temperature")
        self.assertIsNotNone(alarm)
        self.s.acknowledge(alarm["id"],{"author":"Javier"})
        self.s.acknowledge(alarm["id"],{"author":"Javier"})
        self.assertIsNotNone(self.active("temperature"))
        self.assertEqual(len(self.s.store.rows("SELECT * FROM alarm_events WHERE event='acknowledged'")),1)
        self.s.control({"action":"recovery"}); self.ticks(4)
        self.assertIsNone(self.active("temperature"))
        self.s.close(); self.s=Service(self.path,self.clock)
        row=self.s.alarm_history()["rows"][0]
        self.assertIsNotNone(row["recovered_at"])
        self.assertIsNotNone(row["acknowledged_at"])
        self.assertEqual(len(self.s.alarm_history()["events"]),3)
    def test_vibration_recovery(self):
        self.start("vibration"); self.ticks(4)
        self.assertIsNotNone(self.active("vibration"))
        self.s.control({"action":"recovery"}); self.ticks(4)
        self.assertIsNone(self.active("vibration"))
    def test_signal_loss_hides_old_reading_and_recovers(self):
        self.start(); self.ticks(1)
        previous=self.s.status()["last_received_at"]
        self.s.control({"action":"signal_loss"}); self.ticks(5)
        self.assertEqual(self.s.status()["state"],"no_data")
        self.assertIsNone(self.s.status()["current"])
        self.assertEqual(self.s.status()["last_received_at"],previous)
        self.assertIsNotNone(self.active("no_data"))
        self.s.control({"action":"recovery"}); self.ticks(1)
        self.assertIsNone(self.active("no_data"))
        self.assertEqual(self.s.status()["state"],"normal")
    def test_no_signal_from_start_and_stop_supervision(self):
        self.start("signal_loss"); self.ticks(5)
        self.assertIsNotNone(self.active("no_data"))
        self.s.control({"action":"stop"})
        self.assertIsNone(self.active("no_data"))
        self.assertIn("suspendida", self.s.alarm_history()["events"][0]["detail"])
    def test_no_threshold_duration_across_signal_gap(self):
        self.start("hot"); self.ticks(2)
        self.s.control({"action":"signal_loss"}); self.ticks(5)
        self.s.control({"action":"hot"}); self.ticks(1)
        self.assertIsNone(self.active("temperature"))
        self.ticks(3); self.assertIsNotNone(self.active("temperature"))
    def test_hysteresis_prevents_chatter(self):
        self.start("hot"); self.ticks(4)
        p=dict(self.s.last)
        p.pop("received_at")
        for v in [44,45,43,44,43]:
            self.clock.advance();p.update(sequence=p["sequence"]+1,acquired_at=stamp(self.clock()),temperature_c=v)
            self.s.receive(p)
        self.assertIsNotNone(self.active("temperature"))
        for _ in range(4):
            self.clock.advance();p.update(sequence=p["sequence"]+1,acquired_at=stamp(self.clock()),temperature_c=41)
            self.s.receive(p)
        self.assertIsNone(self.active("temperature"))
        self.assertEqual(len(self.s.alarm_history()["rows"]),1)
    def test_invalid_duplicate_and_out_of_order_are_explicit(self):
        self.start(); self.ticks(1); packet=dict(self.s.last)
        # recepción es de propiedad del servidor y no forma parte del paquete de entrada
        packet.pop("received_at")
        before=self.s.store.latest()
        with self.assertRaises(PacketError) as e: self.s.receive(packet)
        self.assertEqual(e.exception.code,"duplicate")
        self.clock.advance(); newer=dict(packet,sequence=3,acquired_at=stamp(self.clock()));self.s.receive(newer)
        with self.assertRaises(PacketError) as e: self.s.receive(dict(newer,sequence=2))
        self.assertEqual(e.exception.code,"out_of_order")
        for bad in [dict(newer,sequence=True),dict(newer,temperature_c=float("nan")),dict(newer,quality="good"),dict(newer,acquired_at="2026-10-01T12:00:00"),dict(newer,extra=1)]:
            with self.assertRaises(PacketError): self.s.receive(bad)
        self.assertEqual(self.s.store.latest()["sequence"],3)
        codes={x["code"] for x in self.s.store.rows("SELECT * FROM reception_events")}
        self.assertTrue({"duplicate","out_of_order","invalid"}.issubset(codes))
    def test_future_stale_and_real_rejected(self):
        self.start();p=self.s.simulator.packet(self.clock())
        for bad,code in [(dict(p,acquired_at=stamp(self.clock()+timedelta(seconds=6))),"future"),(dict(p,acquired_at=stamp(self.clock()-timedelta(seconds=11))),"stale"),(dict(p,source="real"),"real_disabled")]:
            with self.assertRaises(PacketError) as e:self.s.receive(bad)
            self.assertEqual(e.exception.code,code)
        self.assertIsNone(self.s.store.latest())
    def test_packet_rejection_does_not_stop_simulation(self):
        self.start()
        p=self.s.simulator.packet(self.clock())
        p["acquired_at"]=stamp(self.clock()+timedelta(seconds=4))
        self.s.receive(p)
        self.ticks(2)  # posteriores secuencias con reloj anterior se rechazan explícitamente
        self.assertTrue(self.s.status()["running"])
        self.assertIsNone(self.s.status()["error"])
        self.assertEqual(self.s.store.latest()["sequence"],1)
        self.ticks(3)
        self.assertGreater(self.s.store.latest()["sequence"],1)
        self.assertTrue(any(e["code"]=="out_of_order" for e in self.s.status()["reception_events"]))

    def test_interventions_and_measurements_survive_restart(self):
        self.start();self.ticks(2)
        intervention=self.s.add_intervention({"asset_id":"lavadora-prueba","intervention_at":stamp(self.clock()-timedelta(hours=1)),"author":"Javier","work_type":"Inspección","observations":"Prueba simulada"})
        self.assertNotEqual(intervention["intervention_at"],intervention["recorded_at"])
        self.s.close();self.s=Service(self.path,self.clock)
        self.assertEqual(len(self.s.interventions()["rows"]),1)
        self.assertEqual(self.s.history({})["total"],2)
        self.assertIsNone(self.s.status()["current"])
        self.start();self.ticks(1)
        self.assertEqual(self.s.last["sequence"],3)
    def test_rules_persist_and_validate(self):
        rules=self.s.store.rules();rules["temperature_limit"]=48
        self.s.configure(rules)
        self.s.close();self.s=Service(self.path,self.clock)
        self.assertEqual(self.s.store.rules()["temperature_limit"],48)
        with self.assertRaises(ValueError):self.s.configure(dict(rules,vibration_hysteresis=10))
        with self.assertRaises(ValueError):self.s.configure(dict(rules,no_data_s=0))
    def test_history_intervals_and_bad_intervention(self):
        self.start();self.ticks(3)
        query={"from":stamp(self.clock()-timedelta(seconds=1)),"to":stamp(self.clock())}
        self.assertEqual(self.s.history(query)["total"],2)
        with self.assertRaises(ValueError):self.s.history({"from":query["to"],"to":query["from"]})
        with self.assertRaises(ValueError):self.s.add_intervention({})

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="neiron-http-")
        self.s=Service(Path(self.temp.name)/"test.sqlite3")
        self.server=Server(("127.0.0.1",0),self.s)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url="http://127.0.0.1:"+str(self.server.server_address[1])
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.s.close();self.temp.cleanup()
    def request(self,path,data=None,headers=None):
        return urlopen(Request(self.url+path,data=None if data is None else json.dumps(data).encode(),headers=headers or ({"Content-Type":"application/json"} if data is not None else {})),timeout=5)
    def test_local_server_assets_and_controls(self):
        with self.request("/") as r:
            self.assertIn("DATOS SIMULADOS",r.read().decode())
            self.assertIn("default-src 'self'",r.headers["Content-Security-Policy"])
        with self.request("/api/simulation",{"action":"start"}) as r:self.assertTrue(json.load(r)["running"])
        self.s.tick()
        with self.request("/api/status") as r:
            status=json.load(r)
            self.assertEqual(status["ai"],"disabled");self.assertIsNotNone(status["current"])
        with self.request("/api/simulation",{"action":"stop"}) as r:self.assertIsNone(json.load(r)["current"])
    def test_csv_units_source_and_dates(self):
        self.s.control({"action":"start"});self.s.tick()
        with self.request("/api/export.csv") as r:
            self.assertIn("attachment",r.headers["Content-Disposition"])
            rows=list(csv.reader(io.StringIO(r.read().decode("utf-8-sig")),delimiter=";"))
        self.assertEqual(rows[0],CSV_HEADERS);self.assertEqual(len(rows),2)
        self.assertEqual(rows[1][6],"simulated");self.assertIn("+00:00",rows[1][4]);self.assertEqual(rows[1][10],UNIT)
    def test_host_origin_and_input_validation(self):
        for headers in [{"Host":"external.example"},{"Origin":"https://external.example"},{"Sec-Fetch-Site":"cross-site"}]:
            with self.assertRaises(HTTPError) as e:self.request("/api/status",headers=headers)
            self.assertEqual(e.exception.code,403)
        with self.assertRaises(HTTPError) as e:self.request("/api/interventions",{})
        self.assertEqual(e.exception.code,400)
        with self.assertRaises(HTTPError) as e:self.request("/api/history?from=invalid")
        self.assertEqual(e.exception.code,400)
    def test_packet_endpoint_rejects_duplicates_and_invalid(self):
        self.s.control({"action":"start"})
        p=self.s.simulator.packet(self.s.clock())
        with self.request("/api/packets",p) as r:self.assertEqual(r.status,201)
        with self.assertRaises(HTTPError) as e:self.request("/api/packets",p)
        self.assertEqual(e.exception.code,409)
        self.assertEqual(json.load(e.exception)["code"],"duplicate")
        with self.assertRaises(HTTPError) as e:self.request("/api/packets",dict(p,temperature_c="mala"))
        self.assertEqual(e.exception.code,422)

if __name__=="__main__": unittest.main()
