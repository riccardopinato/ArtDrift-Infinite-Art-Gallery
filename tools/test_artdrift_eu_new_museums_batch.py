"""Safety and functional unit tests of ArtDrift non-US museum collectors."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sp=importlib.util.spec_from_file_location("eu",ROOT/"tools/artdrift_eu_new_museums_batch.py")
eu=importlib.util.module_from_spec(sp)
sp.loader.exec_module(eu)
class EuropeanMuseumSourceTests(unittest.TestCase):
    def test_research_hosts_exclude_us_museums(self):
        for domain in ("api.artic.edu","openaccess-api.clevelandart.org",
                       "collectionapi.metmuseum.org","api.nga.gov",
                       "iip.smk.dk","evil.example"):
            self.assertFalse(eu.allow("https://"+domain+"/api/objects"))
        self.assertTrue(eu.allow("https://data.rijksmuseum.nl/search/collection"))
        self.assertTrue(eu.allow("https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a/img.jpg"))
        self.assertFalse(eu.allow("http://data.rijksmuseum.nl/a"))
        self.assertFalse(eu.allow("https://data.rijksmuseum.nl.evil.example/a"))

    def test_scenic_multilingual_titles(self):
        for title in ("Landschap aan de kust","Sommarlandskap","Garden at Giverny",
                      "Blumen im Garten","Bomen langs de rivier",
                      "Sommardag vid havet","Zomerlandschap"):
            self.assertTrue(eu.scene_title(title),title)
        for title in ("Portrait of Woman in Garden","A Nocturne Beach","Portrait",
                      "Woman at the Sea","Landscape in Black Night","Sketch of a Meadow"):
            self.assertFalse(eu.scene_title(title),title)

    def test_painting_year_never_from_artist_lifespan(self):
        self.assertEqual(eu.date_year("1899-01-01T00:00:00Z"),1899)
        self.assertIsNone(eu.date_year("1765"))
        self.assertIsNone(eu.date_year("1922–1970"))
        self.assertIsNone(eu.date_year("mid-20th century"))
        self.assertEqual(eu.author_year_from_doc("1903, Nationalmuseum"),1903)
        self.assertIsNone(eu.author_year_from_doc("unknown"))

    def test_linked_art_parse(self):
        obj={"identified_by":[{"type":"Identifier",
             "classified_as":[{"id":"https://id.rijksmuseum.nl/22015218"}],
             "content":"SK-A-11"},
             {"type":"Name","content":"Landschap bij de rivier",
             "language":[{"id":"http://vocab.getty.edu/aat/300388277"}]}],
             "produced_by":{"part":[{"timespan":{"begin_of_the_begin":"1907-01-01T00:00:00Z"},
              "carried_out_by":[{"notation":[{"@language":"en","@value":"Artist Example"}]}]}]}}
        self.assertEqual(eu.rijks_year(obj),1907)
        self.assertEqual(eu.rijks_ident(obj),"SK-A-11")
        self.assertEqual(eu.rijks_artist(obj),"Artist Example")
        self.assertTrue(eu.scene_title(eu.display_name(obj["identified_by"])))

    def test_high_chroma_near_miss_preserved_for_visual_qa(self):
        # Actual Rijksmuseum SK-A-2288, Landscape on the Oise.
        vivid={"luminance":.4935,"dark_fraction":.1906,
               "saturation":.5389,"vivid_fraction":.5614}
        self.assertTrue(eu.visual_review_exception(vivid))
        from artdrift_dark_threshold_ab import color_tier
        self.assertTrue(color_tier(vivid).startswith("HOLD"))
        # A predominantly dark low-chroma image is still rejected.
        self.assertFalse(eu.visual_review_exception(
            {"luminance":.29,"dark_fraction":.65,"saturation":.52,"vivid_fraction":.55}))
        self.assertFalse(eu.visual_review_exception(
            {"luminance":.59,"dark_fraction":.08,"saturation":.13,"vivid_fraction":.12}))

    def test_sweden_requires_public_domain_and_actual_creation_date(self):
        obj={"pageid":52109999,"title":"File:Summer Landscape (Test Artist) - Nationalmuseum - 9999.tif",
             "imageinfo":[{"mime":"image/tiff","thumburl":
                "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/test.tif/330px-test.tif.jpg",
                "extmetadata":{"LicenseShortName":{"value":"Public domain"},
                               "Copyrighted":{"value":"False"},
                               "Artist":{"value":"Test Artist"},
                               "DateTimeOriginal":{"value":"1891"}},
                "sha1":"abc"}]}
        self.assertIsNotNone(eu.sweden_object(obj))
        obj["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"]="CC BY-NC"
        self.assertIsNone(eu.sweden_object(obj))
        obj["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"]="Public domain"
        obj["imageinfo"][0]["extmetadata"]["DateTimeOriginal"]["value"]="Unknown"
        self.assertIsNone(eu.sweden_object(obj))

    def test_staedel_major_set_discards_deleted_records(self):
        from unittest.mock import patch
        from urllib.parse import parse_qs,urlsplit
        ns='http://www.openarchives.org/OAI/2.0/'
        lido='http://www.lido-schema.org'
        raw=(f'<OAI-PMH xmlns="{ns}" xmlns:lido="{lido}"><ListRecords>'
             '<record><header status="deleted"><identifier>oai:DE-MUS-048017:1</identifier></header></record>'
             '<record><header><identifier>oai:DE-MUS-048017:2</identifier></header>'
             '<metadata><lido:lido><lido:lidoRecID>DE-MUS-048017:2</lido:lidoRecID>'
             '</lido:lido></metadata></record></ListRecords></OAI-PMH>').encode()
        def fake(url,**kwargs):
            q=parse_qs(urlsplit(url).query)
            self.assertEqual(q.get('set'),['scope:major'])
            self.assertEqual(q.get('verb'),['ListRecords'])
            return raw
        with patch.object(eu,'fetch',side_effect=fake):
            rows=eu.staedel_records()
        self.assertEqual(len(rows),1)

    def test_staedel_identifiers_getrecord_fallback(self):
        from unittest.mock import patch
        from urllib.parse import parse_qs,urlsplit
        ns='http://www.openarchives.org/OAI/2.0/'
        lido='http://www.lido-schema.org'
        wrap=lambda v,s:(f'<OAI-PMH xmlns="{ns}" xmlns:lido="{lido}">'
                         f'<{v}>{s}</{v}></OAI-PMH>').encode()
        calls=[]
        def fake(url,**kwargs):
            q=parse_qs(urlsplit(url).query);v=q['verb'][0];calls.append(v)
            if v=='ListRecords':
                return wrap(v,'<record><header status="deleted">'
                    '<identifier>oai:DE-MUS-048017:1</identifier></header></record>')
            if v=='ListIdentifiers':
                return wrap(v,'<header status="deleted">'
                    '<identifier>oai:DE-MUS-048017:1</identifier></header>'
                    '<header><identifier>oai:DE-MUS-048017:2442</identifier></header>')
            if v=='GetRecord':
                self.assertEqual(q['identifier'],['oai:DE-MUS-048017:2442'])
                return wrap(v,'<record><header><identifier>oai:DE-MUS-048017:2442</identifier>'
                    '</header><metadata><lido:lido><lido:lidoRecID>DE-MUS-048017:2442'
                    '</lido:lidoRecID></lido:lido></metadata></record>')
            raise AssertionError(v)
        with patch.object(eu,'fetch',side_effect=fake):
            self.assertEqual(len(eu.staedel_records()),1)
        self.assertIn('ListIdentifiers',calls)
        self.assertIn('GetRecord',calls)

    def test_staedel_uses_subject_creation_date_and_cdn(self):
        from xml.etree import ElementTree as ET
        ns='http://www.openarchives.org/OAI/2.0/'
        lido='http://www.lido-schema.org'
        xml=f"""<record xmlns="{ns}" xmlns:lido="{lido}">
        <header><identifier>oai:DE-MUS-048017:2442</identifier></header>
        <metadata><lido:lido><lido:lidoRecID>DE-MUS-048017:2442</lido:lidoRecID>
        <lido:titleSet><lido:appellationValue xml:lang="en">A quiet view</lido:appellationValue></lido:titleSet>
        <lido:objectRelationWrap><lido:subjectConcept><lido:term>river</lido:term></lido:subjectConcept></lido:objectRelationWrap>
        <lido:eventSet><lido:event><lido:eventType><lido:term>Acquisition</lido:term></lido:eventType>
        <lido:earliestDate>1900</lido:earliestDate></lido:event></lido:eventSet>
        <lido:eventSet><lido:event><lido:eventType><lido:term>Work conception</lido:term></lido:eventType>
        <lido:eventDate><lido:date><lido:earliestDate>1872</lido:earliestDate></lido:date></lido:eventDate></lido:event></lido:eventSet>
        <lido:resourceWrap><lido:linkResource>https://cdn.staedelmuseum.de/images/2442/thumb-xl.jpg</lido:linkResource></lido:resourceWrap>
        </lido:lido></metadata></record>"""
        rec=eu.staedel_parse(ET.fromstring(xml))
        self.assertIsNotNone(rec)
        self.assertEqual(rec['year'],1872)
        self.assertEqual(rec['matched_title_or_subject'],'subject')
        self.assertFalse(rec['commercially_approved'])
        self.assertTrue(eu.allow('https://cdn.staedelmuseum.de/images/a.jpg'))
        self.assertFalse(eu.allow('https://cdn.staedelmuseum.de.evil.test/a.jpg'))

    def test_staedel_no_acquisition_date_as_creation(self):
        from xml.etree import ElementTree as ET
        ns='http://www.openarchives.org/OAI/2.0/'
        lido='http://www.lido-schema.org'
        xml=f"""<record xmlns="{ns}" xmlns:lido="{lido}">
        <header><identifier>oai:DE-MUS-048017:10</identifier></header>
        <metadata><lido:lido><lido:lidoRecID>DE-MUS-048017:10</lido:lidoRecID>
        <lido:titleSet><lido:appellationValue>River landscape</lido:appellationValue></lido:titleSet>
        <lido:eventSet><lido:event><lido:eventType><lido:term>Acquisition</lido:term></lido:eventType>
        <lido:earliestDate>1900</lido:earliestDate></lido:event></lido:eventSet>
        <lido:resourceWrap><lido:linkResource>https://cdn.staedelmuseum.de/images/10.jpg</lido:linkResource></lido:resourceWrap>
        </lido:lido></metadata></record>"""
        self.assertIsNone(eu.staedel_parse(ET.fromstring(xml)))


    def test_staedel_only_creation_event_date_and_no_doll_subject(self):
        from xml.etree import ElementTree as ET
        ns='http://www.openarchives.org/OAI/2.0/'
        lido='http://www.lido-schema.org'
        def make(title):
            xml=f"""<record xmlns="{ns}" xmlns:lido="{lido}">
            <header><identifier>oai:DE-MUS-048017:sg377</identifier></header>
            <metadata><lido:lido><lido:lidoRecID>DE-MUS-048017/lido/sg377</lido:lidoRecID>
            <lido:titleSet><lido:appellationValue>{title}</lido:appellationValue></lido:titleSet>
            <lido:objectRelationWrap><lido:subjectConcept><lido:term>fruit</lido:term></lido:subjectConcept></lido:objectRelationWrap>
            <lido:eventSet><lido:event><lido:eventType><lido:term>Work conception</lido:term></lido:eventType>
            <lido:eventActor><lido:actorDate><lido:earliestDate>1858</lido:earliestDate></lido:actorDate></lido:eventActor>
            <lido:eventDate><lido:date><lido:earliestDate>1915</lido:earliestDate></lido:date></lido:eventDate>
            </lido:event></lido:eventSet>
            <lido:resourceWrap><lido:linkResource>https://cdn.staedelmuseum.de/images/6a/b6/sg377/thumb-lg.jpg</lido:linkResource></lido:resourceWrap>
            </lido:lido></metadata></record>"""
            return ET.fromstring(xml)
        self.assertIsNone(eu.staedel_parse(make('Japanese Dolls with Apples')))
        valid=eu.staedel_parse(make('Still Life with Fruits'))
        self.assertIsNotNone(valid)
        self.assertEqual(valid['year'],1915)
if __name__=="__main__":unittest.main()
