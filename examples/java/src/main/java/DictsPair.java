import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.*;
import java.util.zip.*;

public class DictsPair {
    static final String BASE="https://github.com/danilfg/dicts/releases/";
    static final String REG="ghcr.io/danilfg/dicts-data";
    static final HttpClient HTTP=HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER)
        .connectTimeout(Duration.ofSeconds(30)).build();
    static final ObjectMapper JSON=new ObjectMapper();
    static byte[] get(String url,String bearer) throws Exception {
        for(int i=0;i<8;i++){
            URI uri=URI.create(url);
            if(!"https".equals(uri.getScheme()))throw new IllegalArgumentException("HTTPS required");
            HttpRequest.Builder b=HttpRequest.newBuilder(uri).timeout(Duration.ofMinutes(3)).GET();
            if(bearer!=null&&"ghcr.io".equals(uri.getHost()))b.header("Authorization","Bearer "+bearer);
            HttpResponse<byte[]> r=HTTP.send(b.build(),HttpResponse.BodyHandlers.ofByteArray());
            if(r.statusCode()>=300&&r.statusCode()<400){
                URI next=uri.resolve(r.headers().firstValue("Location").orElseThrow());
                if(!Objects.equals(next.getHost(),uri.getHost()))bearer=null;
                url=next.toString();continue;
            }
            if(r.statusCode()!=200)throw new IllegalStateException("HTTP "+r.statusCode());
            return r.body();
        }
        throw new IllegalStateException("Redirect limit");
    }
    static String sha(byte[] b)throws Exception{
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));
    }
    static byte[] verify(byte[] b,JsonNode m)throws Exception{
        if(b.length!=m.path("bytes").asLong()||!sha(b).equals(m.path("sha256").asText()))
            throw new IllegalStateException("SHA-256 or size mismatch");return b;
    }
    static String token()throws Exception{
        return JSON.readTree(get("https://ghcr.io/token?service=ghcr.io&scope="+
            URLEncoder.encode("repository:danilfg/dicts-data:pull",StandardCharsets.UTF_8),null)).get("token").asText();
    }
    static void install(JsonNode blocks,Path cache)throws Exception{
        String auth=null;
        for(JsonNode b:blocks){
            String digest=b.get("sha256").asText();
            if(!digest.matches("[a-f0-9]{64}")||b.path("bytes").asLong()<1||b.path("bytes").asLong()>32L*1024*1024)
                throw new IllegalArgumentException("Bad block");
            Path f=cache.resolve(digest+".zip");
            if(Files.exists(f)){
                try{verify(Files.readAllBytes(f),b);continue;}catch(IllegalStateException ignored){}
            }
            if(auth==null)auth=token();
            byte[] raw=verify(get("https://ghcr.io/v2/danilfg/dicts-data/blobs/sha256:"+digest,auth),b);
            Path tmp=cache.resolve(digest+".partial");Files.write(tmp,raw);
            Files.move(tmp,f,StandardCopyOption.REPLACE_EXISTING);
        }
    }
    public static void main(String[] args)throws Exception{
        String pair=args.length>0?args[0]:"en-ru";
        String version=args.length>1?args[1]:null;
        if(version!=null&&!version.matches("v\\d{4}\\.\\d{2}\\.\\d{2}\\.\\d+\\.\\d+"))throw new IllegalArgumentException("Bad version");
        JsonNode m=JSON.readTree(get(BASE+(version==null?"latest/download/":"download/"+version+"/")+"LEXICAL-INDEX.json",null));
        String tag=m.path("version").asText(),base=BASE+"download/"+tag+"/";
        if(!tag.matches("v\\d{4}\\.\\d{2}\\.\\d{2}\\.\\d+\\.\\d+")||(version!=null&&!version.equals(tag))||
            m.path("schema").asInt()!=1||!"oci-pair-v1".equals(m.path("format").asText())||
            !REG.equals(m.path("registry").asText())||!base.equals(m.path("download_base").asText()))
            throw new IllegalStateException("No compatible OCI release");
        JsonNode c=JSON.readTree(verify(get(base+"PAIR-INDEX.json",null),m.get("pair_index")));
        if(c.path("schema").asInt()!=1||!tag.equals(c.path("version").asText())||!REG.equals(c.path("registry").asText())||
            !"oci-pair-v1".equals(c.path("format").asText()))throw new IllegalStateException("Catalog mismatch");
        JsonNode p=c.path("pairs").path(pair);
        if(p.isMissingNode())throw new IllegalArgumentException("Unknown pair");
        Path cache=Path.of(".dicts-cache","blobs");Files.createDirectories(cache);
        var groups=c.path("groups").fields();
        while(groups.hasNext()){
            var group=groups.next();JsonNode g=group.getValue();
            install(g.path("pairs").path(pair),cache);
            for(String lang:new LinkedHashSet<>(List.of(p.get("from").asText(),p.get("to").asText())))
                install(g.path("languages").path(lang),cache);
        }
        System.out.println("Installed "+pair+" from "+tag);
    }
}
