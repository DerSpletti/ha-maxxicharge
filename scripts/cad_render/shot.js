const {chromium}=require(process.argv[2]+'/node_modules/playwright-core');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1600,height:1600}});p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto(process.argv[3]);await p.waitForFunction('window.__done',null,{timeout:60000});
console.log(await p.evaluate('window.__done'));await p.screenshot({path:process.argv[4],omitBackground:true});await b.close();})();
