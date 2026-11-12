const fs=require('fs'),path=require('path'),zlib=require('zlib');
const root=path.resolve(__dirname,'..');
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(path.join(dir,e.name)):[path.join(dir,e.name)]).sort();}
function crc(data){let c=0xffffffff;for(const b of data){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
function zip(folder,name){const local=[],central=[];let offset=0;const entries=files(folder);for(const file of entries){const data=fs.readFileSync(file),body=zlib.deflateRawSync(data),n=Buffer.from(path.relative(folder,file).replaceAll('\\','/')),sum=crc(data),h=Buffer.alloc(30),c=Buffer.alloc(46);h.writeUInt32LE(0x04034b50);h.writeUInt16LE(20,4);h.writeUInt16LE(8,8);h.writeUInt16LE(33,12);h.writeUInt32LE(sum,14);h.writeUInt32LE(body.length,18);h.writeUInt32LE(data.length,22);h.writeUInt16LE(n.length,26);c.writeUInt32LE(0x02014b50);c.writeUInt16LE(20,4);c.writeUInt16LE(20,6);c.writeUInt16LE(8,10);c.writeUInt16LE(33,14);c.writeUInt32LE(sum,16);c.writeUInt32LE(body.length,20);c.writeUInt32LE(data.length,24);c.writeUInt16LE(n.length,28);c.writeUInt32LE(offset,42);local.push(h,n,body);central.push(c,n);offset+=h.length+n.length+body.length;}const directory=Buffer.concat(central),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(entries.length,8);end.writeUInt16LE(entries.length,10);end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);const dest=path.join(root,'dist',name);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,Buffer.concat([...local,directory,end]));console.log(`${name}: ${entries.length} files`);}

const content=path.join(root,'content');
const manifest=fs.readFileSync(path.join(content,'horizon-mod.toml'),'utf8');
const field=(text,key)=>{const m=text.match(new RegExp('^'+key+'\\s*=\\s*"([^"]+)"','m'));if(!m)throw Error('Missing field '+key);return m[1];};
for(const file of files(content))if(file.endsWith('.json'))JSON.parse(fs.readFileSync(file,'utf8'));
zip(content,`${field(manifest,'id')}-${field(manifest,'version')}.hmod`);
const crypto=require('crypto');
const hashes=fs.readdirSync(path.join(root,'dist')).filter(n=>n.endsWith('.hmod')||n.endsWith('.hnmod')).sort().map(n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist',n))).digest('hex')+'  '+n);
fs.writeFileSync(path.join(root,'dist/SHA256SUMS.txt'),hashes.join('\n')+'\n');

