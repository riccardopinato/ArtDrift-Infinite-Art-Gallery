/* Read-only Art Drift MoMA metadata. No upstream image proxying. */
const PAGE = 24;
const MAX_OFFSET = 4800;
const HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "X-Content-Type-Options": "nosniff",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
  "Access-Control-Allow-Headers": "Accept",
  "Cache-Control": "public, max-age=60, s-maxage=600, stale-while-revalidate=600",
};
function response(data, status=200, cache=true) {
  return new Response(JSON.stringify(data),{
    status, headers:{...HEADERS, ...(cache ? {}:{"Cache-Control":"no-store"})}
  });
}
export function makeMatch(q, scope="all") {
  if (!["all","artist","title"].includes(scope)) throw Error("bad_scope");
  const tokens=[...q.normalize("NFC").matchAll(/[\p{L}\p{N}]{2,}/gu)]
    .slice(0,6).map(x=>x[0].slice(0,32));
  if (tokens.length===0) return null;
  const prefix = scope==="all" ? "" : scope+":";
  return tokens.map(t=>prefix+'"'+t+'"*').join(" AND ");
}
export function assetUrl(row,base) {
  if (!row || !row.image_key || !row.rights_evidence_url ||
      !/^(cc0|public domain)$/i.test((row.rights_license||"").trim()))return null;
  if(!/^[a-z0-9][a-z0-9/_-]{0,130}\.webp$/.test(row.image_key))return null;
  try {
    const root=new URL(base),proof=new URL(row.rights_evidence_url);
    if(root.protocol!=="https:" || proof.protocol!=="https:" ||
       root.username || root.password || proof.username || proof.password ||
       root.search || root.hash || (root.port && root.port!=="443"))return null;
    return root.toString().replace(/\/$/,"")+"/"+row.image_key;
  } catch {return null;}
}
export function publicRow(row,base) {
  const image=assetUrl(row,base);
  return {
    id:row.id,title:row.title,artist:row.artist,date:row.date_display,
    medium:row.medium,dimensions:row.dimensions,
    classification:row.classification,department:row.department,
    source_url:row.work_url,thumbnail_url:image,
    image_rights:image?row.rights_license:null,
  };
}

const MUSEUM_IMAGE_HOSTS=new Set([
  "www.artic.edu","images.metmuseum.org","openaccess-cdn.clevelandart.org",
  "clevelandart.org","www.clevelandart.org","iiif.micr.io",
  "api.nga.gov","media.nga.gov","media.getty.edu",
  "ids.si.edu","www.si.edu","si.edu","iip.smk.dk","iip-thumb.smk.dk",
  "api.artsmia.org","images.thewalters.org","art.thewalters.org",
  "upload.wikimedia.org"
]);
const CC_MEDIA=new Set(["CC0","Public Domain","CC BY 3.0","CC BY 4.0",
  "CC BY-SA 3.0","CC BY-SA 4.0"]);
export function publicMuseumRow(row) {
  const rights=String(row?.rights_license||"");
  let thumbnail=null;
  if((CC_MEDIA.has(rights) || rights==="Public Domain Mark" ||
       rights.startsWith("Public Domain / ")) && row?.rights_evidence_url) {
    try {
      const image=new URL(row.image_url), proof=new URL(row.rights_evidence_url);
      if(image.protocol==="https:" && MUSEUM_IMAGE_HOSTS.has(image.hostname) &&
          !image.username && !image.password && (!image.port || image.port==="443") &&
          proof.protocol==="https:" && !proof.username && !proof.password) {
        thumbnail=image.toString();
      }
    } catch { /* Missing rights/image metadata means no image, never a guess. */ }
  }
  let official=null;
  try {
    const uri=new URL(row.source_url);
    if(uri.protocol==="https:" && !uri.username && !uri.password &&
       (!uri.port || uri.port==="443"))official=uri.toString();
  } catch {}
  return {
    source_key:String(row.source_key||""),
    museum_source:String(row.museum_source||""),
    museum_name:String(row.museum_name||""),
    title:String(row.title||""),
    artist:String(row.artist||""),
    date:String(row.date_display||""),
    medium:String(row.medium||""),
    source_url:official,
    thumbnail_url:thumbnail,
    rights_license:rights,
    rights_evidence_url:String(row.rights_evidence_url||""),
    credit_line:String(row.credit_line||""),
  };
}

export default {
  async fetch(request,env) {
    if(request.method==="OPTIONS")return new Response(null,{status:204,headers:HEADERS});
    if(!["GET","HEAD"].includes(request.method))return response({error:"method_not_allowed"},405,false);
    const url=new URL(request.url);
    if(url.pathname==="/health"){
      return response({status:"configured",datasets:["ArtDrift-Museums","MoMA-selective-metadata"],source_sha:env.CATALOG_SOURCE_SHA});
    }
    if(url.pathname==="/api/v1/museums"){
      try {
        const rs=await env.CATALOG_DB.prepare(
          "SELECT museum_name,COUNT(*) AS works FROM museum_works GROUP BY museum_name ORDER BY museum_name LIMIT 100"
        ).all();
        return response({source:"ArtDrift-Museums",institutions:rs.results||[]});
      }catch{return response({error:"catalog_not_ready"},503,false);}
    }
    if(url.pathname==="/api/v1/museum-search"){
      const q=(url.searchParams.get("q")||"").trim();
      const scope=url.searchParams.get("scope")||"all";
      const raw=url.searchParams.get("cursor")||"0";
      if(q.length<2 || q.length>90 || !/^(0|[1-9]\d{0,4})$/.test(raw))
        return response({error:"bad_query"},400,false);
      const offset=Number(raw);
      if(offset>MAX_OFFSET)return response({error:"page_limit"},400,false);
      let match;
      try {match=makeMatch(q,scope);}
      catch{return response({error:"bad_scope"},400,false);}
      if(!match)return response({error:"empty_search_terms"},400,false);
      const sql=[
        "SELECT m.source_key,m.museum_source,m.museum_name,m.title,m.artist,",
        "m.date_display,m.medium,m.source_url,m.image_url,m.rights_license,",
        "m.rights_evidence_url,m.credit_line FROM museum_works_fts",
        "JOIN museum_works m ON m.rowid=museum_works_fts.rowid",
        "WHERE museum_works_fts MATCH ?",
        "ORDER BY bm25(museum_works_fts),m.source_key LIMIT ? OFFSET ?"
      ].join(" ");
      try{
        const rs=await env.CATALOG_DB.prepare(sql).bind(match,PAGE+1,offset).all();
        const rows=rs.results||[];
        return response({
          source:"ArtDrift-Museums",license:"per-record museum source",
          count:Math.min(rows.length,PAGE),
          next_cursor:rows.length>PAGE && offset+PAGE<=MAX_OFFSET?
             String(offset+PAGE):null,
          works:rows.slice(0,PAGE).map(publicMuseumRow)
        });
      }catch{return response({error:"catalog_not_ready"},503,false);}
    }
    if(url.pathname==="/api/v1/search"){
      const q=(url.searchParams.get("q")||"").trim();
      const scope=url.searchParams.get("scope")||"all";
      const offsetRaw=url.searchParams.get("cursor")||"0";
      if(q.length<2 || q.length>90 || !/^(0|[1-9]\d{0,4})$/.test(offsetRaw))
        return response({error:"bad_query"},400,false);
      const offset=Number(offsetRaw);
      if(offset>MAX_OFFSET)return response({error:"page_limit"},400,false);
      let match;
      try {match=makeMatch(q,scope);}
      catch {return response({error:"bad_scope"},400,false);}
      if(!match)return response({error:"empty_search_terms"},400,false);
      const sql=[
        "SELECT w.id,w.title,w.artist,w.date_display,w.medium,w.dimensions,",
        "w.classification,w.department,w.work_url,w.image_key,w.rights_license,",
        "w.rights_evidence_url FROM works_fts",
        "JOIN works w ON w.id=works_fts.rowid WHERE works_fts MATCH ?",
        "ORDER BY bm25(works_fts),w.id LIMIT ? OFFSET ?"
      ].join(" ");
      try{
        const rs=await env.CATALOG_DB.prepare(sql).bind(match,PAGE+1,offset).all();
        const rows=rs.results||[];
        return response({
          source:"MoMA",license:"metadata:CC0",
          count:Math.min(rows.length,PAGE),
          next_cursor:rows.length>PAGE && offset+PAGE<=MAX_OFFSET?String(offset+PAGE):null,
          works:rows.slice(0,PAGE).map(x=>publicRow(x,env.ASSET_BASE_URL||""))
        });
      }catch{return response({error:"catalog_not_ready"},503,false);}
    }
    const m=url.pathname.match(/^\/api\/v1\/works\/(\d+)$/);
    if(m){
      const id=Number(m[1]);
      if(!Number.isSafeInteger(id)||id<=0)return response({error:"bad_id"},400,false);
      try{
        const row=await env.CATALOG_DB.prepare("SELECT * FROM works WHERE id=? LIMIT 1").bind(id).first();
        return row?response({source:"MoMA",work:publicRow(row,env.ASSET_BASE_URL||"")}):
          response({error:"not_found"},404,false);
      }catch{return response({error:"catalog_not_ready"},503,false);}
    }
    return response({error:"not_found"},404,false);
  }
};
