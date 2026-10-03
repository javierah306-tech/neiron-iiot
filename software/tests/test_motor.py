from datetime import datetime,timedelta,timezone
import math
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json
from neiron.contract import PacketError,validate,utcnow,stamp
from neiron.motor_model import MotorModel,Settings
from neiron.motor_engine import MotorEngine
from neiron.motor_transport import LocalSender
from neiron.motor_server import MotorHandler
from neiron.profiles import PROFILES
from neiron.server import Server
from neiron.service import Service

class ModelTests(unittest.TestCase):
    def test_thermal_equilibrium_and_power_balance(self):
        m=MotorModel()
        for _ in range(60):m.step(120)
        c=m.context
        self.assertTrue(2900<c["rpm"]<2940)
        self.assertTrue(17<c["flow_m3h"]<19)
        self.assertTrue(43<c["head_m"]<47)
        self.assertTrue(48<m.surface_c<65)
        self.assertLess(abs(m.surface_c-c["equilibrium_model_c"]),.2)
        self.assertAlmostEqual(c["electrical_power_w"],c["shaft_power_w"]+c["losses_w"])
        self.assertAlmostEqual(c["hydraulic_power_w"],1000*9.80665*c["flow_m3h"]/3600*c["head_m"])
    def test_no_temperature_jump_and_time_scaling(self):
        a,b=MotorModel(),MotorModel();b.settings.time_scale=60
        a.step(60);b.step(1)
        self.assertAlmostEqual(a.surface_c,b.surface_c,places=10)
        b.settings.ambient_c=35
        old=b.surface_c
        self.assertEqual(b.surface_c,old)
        b.settings.time_scale=1;b.step(1)
        self.assertLess(abs(b.surface_c-old),.1)
    def test_stop_motor_cools_and_keeps_generation(self):
        m=MotorModel()
        for _ in range(10):m.step(120)
        hot=m.surface_c;m.motor_on=False;m.step(120)
        self.assertLess(m.surface_c,hot);self.assertLess(m.rpm,1)
        p=m.packet(utcnow())
        self.assertLess(p["vibration_rms"],.05)
        self.assertGreater(p["temperature_c"],m.settings.ambient_c)
    def test_valve_and_faults_are_related_to_context(self):
        m=MotorModel();m.step(30)
        nominal=m.context.copy();p=m.packet(utcnow());normal_rms=p["vibration_rms"]
        m.settings.valve_opening=.5;m.step(30)
        self.assertLess(m.context["flow_m3h"],nominal["flow_m3h"])
        self.assertLess(m.context["shaft_power_w"],nominal["shaft_power_w"])
        m.settings.valve_opening=1;m.scenario="misalignment";m.step(30)
        self.assertGreater(m.packet(utcnow())["vibration_rms"],3)
        m.scenario="cavitation";m.step(30)
        self.assertGreater(m.packet(utcnow())["vibration_rms"],3)
        self.assertLess(m.context["head_m"],nominal["head_m"])
        m.scenario="normal";m.step(30)
        self.assertLess(m.packet(utcnow())["vibration_rms"],1)
        m.scenario="blocked_cooling"
        for _ in range(20):m.step(120)
        self.assertGreater(m.surface_c,75)
    def test_rms_removes_dc_and_matches_vector_harmonics(self):
        m=MotorModel();m.rpm=3000;m.context={"load_fraction":1}
        with patch("random.Random.gauss",return_value=0):m.packet(utcnow())
        r=3000/2910;a=.78*r*r;b=.15*r*r;c=.2*r*r;e=.22*r
        expected=math.sqrt(.5*(a*a*1.7625+b*b*1.6125+c*c*.4525+e*e)+b*.35*e*math.cos(.2))
        self.assertAlmostEqual(m.rms,expected,places=8)
        self.assertEqual(m.context["sample_count"],1000)
        self.assertEqual(m.context["sample_rate_hz"],1000)
        self.assertEqual(len(m.waveform),120)
        previous=m.rms
        with patch("random.Random.gauss",return_value=1):m.packet(utcnow())
        self.assertAlmostEqual(m.rms,previous,places=8)
    def test_motor_contract_and_parameter_validation(self):
        m=MotorModel();m.step(1);p=m.packet(utcnow());profile=PROFILES["motor-pump"]
        accepted=validate(p,utcnow(),asset_id=profile["asset_id"],device_id=profile["device_id"],method=profile["method"])
        self.assertEqual(accepted["source"],"simulated")
        self.assertEqual(p["temperature_c"]*16,round(p["temperature_c"]*16))
        with self.assertRaises(PacketError):validate(p,utcnow())
        for changes in [{"time_scale":2},{"ambient_c":float("nan")},{"valve_opening":0}]:
            with self.assertRaises(ValueError):Settings.validated(dict(ambient_c=22,valve_opening=1,time_scale=1,**{})|changes)

class MotorIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="neiron-motor-test-")
        self.root=Path(self.temp.name)
        self.clock_now=utcnow()
        self.service=Service(self.root/"receiver.sqlite3",clock=lambda:self.clock_now,profile="motor-pump",input_mode="external")
        self.engine=MotorEngine(self.root/"simulator")
        self.server=Server(("127.0.0.1",0),self.service)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        self.sender=LocalSender(self.engine,self.server.server_address[1])
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.worker.join();self.service.close();self.temp.cleanup()
    def tick(self):
        self.clock_now+=timedelta(seconds=1);self.engine.tick(1,self.clock_now);self.sender.send_latest();self.service.tick()
    def test_independent_services_receive_persist_and_detect_loss(self):
        self.service.tick();self.assertIsNone(self.service.store.latest())
        self.tick();self.assertEqual(self.engine.link["state"],"connected")
        self.assertEqual(self.service.last["temperature_c"],self.engine.latest_packet["temperature_c"])
        self.assertEqual(self.service.last["vibration_rms"],self.engine.latest_packet["vibration_rms"])
        self.assertEqual(self.service.store.latest()["device_id"],"esp32-motor-simulado")
        self.assertEqual(self.service.status()["asset"]["id"],"motor-bomba-5hp")
        self.engine.command({"action":"signal_loss"})
        for _ in range(6):self.tick()
        self.assertIsNone(self.service.status()["current"])
        self.assertIsNotNone(self.service.alarms.active("no_data"))
        self.engine.command({"action":"recovery"});self.tick()
        self.assertIsNone(self.service.alarms.active("no_data"))
        self.assertEqual(self.engine.link["accepted"],2)
    def test_restart_state_sequence_and_receiver_persistence(self):
        self.tick();seq=self.engine.model.sequence
        self.engine.configure({"ambient_c":24,"valve_opening":.5,"time_scale":10})
        restored=MotorEngine(self.root/"simulator")
        self.assertEqual(restored.model.sequence,seq)
        self.assertEqual(restored.model.settings.time_scale,10)
        self.assertEqual(restored.model.surface_c,self.engine.model.surface_c)
        self.service.close();self.service=Service(self.root/"receiver.sqlite3",clock=lambda:self.clock_now,profile="motor-pump",input_mode="external");self.server.service=self.service
        self.assertIsNone(self.service.status()["current"])
        self.assertEqual(self.service.history({})["total"],1)
    def test_receiver_sequence_sync_and_profile_isolation(self):
        self.engine.model.sequence=99;self.tick()
        fresh=MotorEngine(self.root/"fresh");sender=LocalSender(fresh,self.server.server_address[1]);fresh.tick(1,self.clock_now);sender.send_latest()
        self.assertEqual(fresh.model.sequence,100)
        self.clock_now+=timedelta(seconds=1);fresh.tick(1,self.clock_now);sender.send_latest()
        self.assertEqual(self.service.store.latest()["sequence"],101)
        washer=Service(self.root/"washer.sqlite3")
        try:
            self.server.service=washer
            self.tick()
            self.assertEqual(self.engine.link["state"],"wrong_profile")
            self.assertIsNone(washer.store.latest())
            with self.assertRaises(ValueError):Service(self.root/"washer.sqlite3",profile="motor-pump",input_mode="external")
        finally:self.server.service=self.service;washer.close()
    def test_receiver_suspend_pause_and_motor_off_are_distinct(self):
        self.service.control({"action":"stop"});self.tick()
        self.assertEqual(self.engine.link["state"],"suspended")
        self.service.control({"action":"start"});self.tick()
        self.engine.command({"action":"motor_stop"});self.tick()
        self.assertIsNotNone(self.service.status()["current"])
        self.assertFalse(self.engine.model.motor_on)
        self.engine.command({"action":"pause"});self.tick()
        self.assertEqual(self.engine.link["state"],"paused")
    def test_receiver_disconnect_does_not_stop_model(self):
        self.tick();elapsed=self.engine.model.elapsed_s
        self.engine.command({"action":"disconnect"});self.tick()
        self.assertGreater(self.engine.model.elapsed_s,elapsed)
        self.assertEqual(self.engine.link["accepted"],1)
        self.engine.command({"action":"connect"});self.tick()
        self.assertEqual(self.engine.link["accepted"],2)
    def test_motor_http_resources_and_origin_guard(self):
        server=Server(("127.0.0.1",0),self.engine,MotorHandler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        url="http://127.0.0.1:"+str(server.server_address[1])
        try:
            with urlopen(url) as r:self.assertIn("DATOS FICTICIOS",r.read().decode())
            with urlopen(Request(url+"/api/settings",data=json.dumps({"ambient_c":25,"valve_opening":.75,"time_scale":60}).encode(),headers={"Content-Type":"application/json"})) as r:self.assertEqual(json.load(r)["settings"]["time_scale"],60)
            with self.assertRaises(HTTPError) as e:urlopen(Request(url+"/api/status",headers={"Origin":"http://external.example"}))
            self.assertEqual(e.exception.code,403)
        finally:server.shutdown();server.server_close();worker.join()

if __name__=="__main__":unittest.main()
