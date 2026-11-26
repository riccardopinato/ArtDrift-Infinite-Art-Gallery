"""OAI ListIdentifiers offline tests: no artwork images and no lost IDs."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import artdrift_staedel_identifiers as m


def oai(ids,token="",deleted=()):
    base='http://www.openarchives.org/OAI/2.0/'
    h=''.join(f'<header><identifier>{x}</identifier></header>' for x in ids)
    h+=''.join(f'<header status="deleted"><identifier>{x}</identifier></header>'
               for x in deleted)
    return (f'<OAI-PMH xmlns="{base}"><ListIdentifiers>{h}'
            f'<resumptionToken>{token}</resumptionToken>'
            '</ListIdentifiers></OAI-PMH>').encode()


class IdentifierTests(unittest.TestCase):
    def test_follow_and_dedupe_headers_without_images(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            if len(calls)==1:
                return oai(['oai:DE-MUS-048017:1',
                            'oai:DE-MUS-048017:2'],token='page-2',
                           deleted=['oai:DE-MUS-048017:dead'])
            self.assertIn('resumptionToken=page-2',url)
            return oai(['oai:DE-MUS-048017:2',
                        'oai:DE-MUS-048017:3'])
        with patch.object(m.time,"sleep"):
            obj=m.harvest(max_pages=3,request=fetch)
        self.assertEqual(obj['distinct_active_identifier_count'],3)
        self.assertEqual(obj['deleted_headers_seen'],1)
        self.assertTrue(obj['catalog_iteration_completed'])
        self.assertEqual(obj['commercially_approved'],0)
    def test_partial_run_keeps_cursor_and_prior_identifiers(self):
        with patch.object(m.time,"sleep"):
            first=m.harvest(max_pages=1,request=lambda u:
                oai(['oai:DE-MUS-048017:1'],token='NEXT'))
        self.assertFalse(first['catalog_iteration_completed'])
        self.assertEqual(first['next_resumption_token'],'NEXT')
        def next_page(url):
            self.assertIn('resumptionToken=NEXT',url)
            return oai(['oai:DE-MUS-048017:2'])
        second=m.harvest(max_pages=1,previous=first,request=next_page)
        self.assertEqual(second['distinct_active_identifier_count'],2)
        self.assertTrue(second['catalog_iteration_completed'])
    def test_throttle_never_becomes_museum_zero(self):
        def blocked(_):
            raise ValueError('HTTP Error 429: Too Many Requests')
        r=m.harvest(previous={'provider':'staedel',
                  'active_identifiers':['oai:DE-MUS-048017:12'],
                  'next_resumption_token':'CURSOR'},request=blocked)
        self.assertEqual(r['distinct_active_identifier_count'],1)
        self.assertFalse(r['catalog_iteration_completed'])
        self.assertTrue(r['errors'])


if __name__=="__main__":
    unittest.main()
