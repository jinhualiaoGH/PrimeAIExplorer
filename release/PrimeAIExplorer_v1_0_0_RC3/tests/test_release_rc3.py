import tempfile, unittest, json
from pathlib import Path
from primeaiexplorer.dashboards import HtmlDashboardEngine
from primeaiexplorer.observatories import ObservatoryResult
from primeaiexplorer.publication import build_publication
class T(unittest.TestCase):
 def result(self): return {'performance':ObservatoryResult(name='performance',metrics={'accuracy':.5,'brier_score':.1,'ece':.2},tables={},summary={},metadata={})}
 def test_nav(self):
  with tempfile.TemporaryDirectory() as d:
   p=HtmlDashboardEngine().render(self.result(),Path(d)/'x.html'); self.assertIn('position:sticky',p.read_text())
 def test_cards(self):
  with tempfile.TemporaryDirectory() as d:
   p=HtmlDashboardEngine().render(self.result(),Path(d)/'x.html'); self.assertIn('Accuracy',p.read_text())
 def test_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   p=HtmlDashboardEngine().render(self.result(),Path(d)/'x.html',context={'experiment_id':'EXP-X'}); self.assertIn('EXP-X',p.read_text())
 def test_figure_label(self):
  with tempfile.TemporaryDirectory() as d:
   p=HtmlDashboardEngine().render(self.result(),Path(d)/'x.html'); self.assertIn('Figure 1',p.read_text())
 def test_publish_missing(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError): build_publication(d,Path(d)/'o')
 def test_publish(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a'; a.mkdir();
   for n,c in [('summary.json','{"observatory_count":1,"metric_count":1,"table_count":0}'),('observatories.json','{}'),('metrics.csv','a,b\n'),('dashboard.html','<html/>')]: (a/n).write_text(c)
   o=build_publication(a,Path(d)/'pub'); self.assertTrue((o/'publication_manifest.json').is_file())
 def test_publish_report(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a'; a.mkdir();
   for n,c in [('summary.json','{}'),('observatories.json','{}'),('metrics.csv','a,b\n'),('dashboard.html','<html/>')]: (a/n).write_text(c)
   o=build_publication(a,Path(d)/'pub'); self.assertIn('Publication', (o/'report.md').read_text())
 def test_manifest_version(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a'; a.mkdir();
   for n,c in [('summary.json','{}'),('observatories.json','{}'),('metrics.csv','a,b\n'),('dashboard.html','<html/>')]: (a/n).write_text(c)
   o=build_publication(a,Path(d)/'pub'); self.assertEqual(json.loads((o/'publication_manifest.json').read_text())['primeaiexplorer_version'],'1.0.0rc3')
