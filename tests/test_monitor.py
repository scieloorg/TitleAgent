# coding: utf-8
import unittest

from monitor import monitor

class MonitorCISISTests(unittest.TestCase):

    def setUp(self):

        self.cisis = monitor.CISIS('tests/cisis')

    def test_cisis_instanciation_invalid_isis_directory(self):

        with self.assertRaises(ValueError):
            monitor.CISIS('invalid directory')

    def test_cisis_instanciation(self):

        self.assertTrue(isinstance(self.cisis, monitor.CISIS))

    def test_cisis_version(self):

        version = """CISIS Interface v5.5.pre02/GC/512G/W/L4/M/32767/16/60/I - Utility MX\nCISIS Interface v5.5.pre02/.iy0/Z/GIZ/DEC/ISI/UTL/INVX/B7/FAT/CIP/CGI/MX/W\nCopyright (c)BIREME/PAHO 2009. [http://www.bireme.br/products/cisis]\nCopyright (c)BIREME/PAHO 2009. [http://bvsmodelo.bvsalud.org/php/level.php?lang=pt&component=28&item=1]\n\n"""

        self.assertEqual(self.cisis.version, version)

    def test_iso(self):

        self.assertTrue(
            isinstance(self.cisis.iso('tests/title/title'), file)
        )

    def test_isis2json_len(self):

        data = self.cisis.isis2json('tests/title/title')
        self.assertEqual(len(data), 52)

    def test_isis2json_title(self):

        data = self.cisis.isis2json('tests/title/title')
        self.assertEqual(data[0]['v100'][0]['_'], 'Acta Theologica')