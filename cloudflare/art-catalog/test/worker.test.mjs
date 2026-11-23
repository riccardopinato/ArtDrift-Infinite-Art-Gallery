import test from "node:test";
import assert from "node:assert/strict";
import worker,{makeMatch,assetUrl,publicRow,publicMuseumRow} from "../src/worker.mjs";

test("FTS input is bounded and quoted",()=>{
  assert.equal(makeMatch("Van Gogh","artist"),'artist:"Van"* AND artist:"Gogh"*');
  assert.equal(makeMatch("cat OR *"),'"cat"* AND "OR"*');
  assert.equal(makeMatch("!!!"),null);
  assert.throws(()=>makeMatch("sample","invalid"));
});
test("only authorized images have links",()=>{
  const row={id:1,title:"A",artist:"B",rights_license:"CC0",
    rights_evidence_url:"https://museum.example/rights",image_key:null};
  assert.equal(publicRow(row,"https://assets.example").thumbnail_url,null);
  assert.equal(assetUrl({...row,image_key:"../a.webp"},"https://assets.example"),null);
  assert.equal(assetUrl({...row,image_key:"moma/1.webp",rights_license:"unknown"},"https://assets.example"),null);
  assert.equal(assetUrl({...row,image_key:"moma/1.webp"},"https://assets.example"),"https://assets.example/moma/1.webp");
});
test("search binds user terms and returns limited pages",async()=>{
  const record=[];
  const env={CATALOG_SOURCE_SHA:"abc",ASSET_BASE_URL:"",
    CATALOG_DB:{prepare(sql){record.push(sql);return{bind(...p){record.push(p);
      return{async all(){return{results:[
        {id:1,title:"Painting",artist:"Van Gogh",work_url:"https://www.moma.org/collection/works/1"}
      ]}}}}}}}};
  const res=await worker.fetch(new Request("https://test.local/api/v1/search?q=Van%20Gogh&scope=artist"),env);
  assert.equal(res.status,200);
  assert.equal((await res.json()).works.length,1);
  assert.deepEqual(record[1],['artist:"Van"* AND artist:"Gogh"*',25,0]);
});
test("invalid requests are rejected",async()=>{
  const env={CATALOG_DB:{prepare(){throw Error("forbidden")}}};
  assert.equal((await worker.fetch(new Request("https://test.local/api/v1/search?q=A&cursor=-1"),env)).status,400);
});

test("museum results retain rights, artwork identity and source attribution",()=>{
  const work={
    source_key:"commons:10000012",museum_source:"commons",
    museum_name:"Wikimedia Commons",title:"Modern Painting",
    artist:"Artist",date_display:"2022",medium:"Painting",
    source_url:"https://commons.wikimedia.org/wiki/File:Painting.jpg",
    image_url:"https://upload.wikimedia.org/a.webp",
    rights_license:"CC BY-SA 4.0",
    rights_evidence_url:"https://commons.wikimedia.org/wiki/File:Painting.jpg",
    credit_line:"Artist / CC BY-SA 4.0",
  };
  const shown=publicMuseumRow(work);
  assert.equal(shown.source_key,"commons:10000012");
  assert.equal(shown.thumbnail_url,work.image_url);
  assert.equal(shown.rights_license,"CC BY-SA 4.0");
  assert.equal(publicMuseumRow({...work,image_url:"https://upload.wikimedia.org.bad.test/a.webp"}).thumbnail_url,null);
  assert.equal(publicMuseumRow({...work,rights_license:"CC BY-NC 4.0"}).thumbnail_url,null);
  assert.equal(publicMuseumRow({...work,rights_evidence_url:""}).thumbnail_url,null);
});
test("museum D1 query uses bounded FTS and parameterized arguments",async()=>{
  const observed=[];
  const env={CATALOG_DB:{prepare(sql){observed.push(sql);return{bind(...values){
    observed.push(values);
    return{async all(){return{results:[{
      source_key:"met:123",museum_source:"met",
      museum_name:"The Metropolitan Museum of Art",title:"Painting",
      rights_license:"CC0",image_url:null
    }]}}};
  }}}}};
  const res=await worker.fetch(new Request("https://test.local/api/v1/museum-search?q=Van%20Gogh&scope=artist"),env);
  assert.equal(res.status,200);
  const data=await res.json();
  assert.equal(data.source,"ArtDrift-Museums");
  assert.equal(data.works[0].source_key,"met:123");
  assert.deepEqual(observed[1],['artist:"Van"* AND artist:"Gogh"*',25,0]);
  assert.equal((await worker.fetch(new Request("https://test.local/api/v1/museum-search?q=foo&cursor=-1"),env)).status,400);
});
