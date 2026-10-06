const {chromium}=require('playwright');
const {spawn}=require('node:child_process'),assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'..'),dir=process.env.RH_SCREENSHOTS||require('node:os').tmpdir();
fs.mkdirSync(dir,{recursive:true});
(async()=>{
 const server=spawn(process.env.RH_TEST_PYTHON||'python3',[path.join(__dirname,'serve_gaming_motion_fixture.py')]);let out='',browser;
 server.stdout.on('data',b=>out+=b);server.stderr.on('data',b=>process.stderr.write(b));
 try{
  for(let n=0;n<100&&!out.includes('\n');n++)await new Promise(r=>setTimeout(r,50));
  const base='http://127.0.0.1:'+JSON.parse(out.split('\n')[0]).port;
  browser=await chromium.launch({executablePath:process.env.RH_CHROMIUM||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'],headless:true,timeout:15000});
  const ctx=await browser.newContext({viewport:{width:390,height:844},extraHTTPHeaders:{'DO-Connecting-IP':'198.51.100.88'}}),p=await ctx.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));p.setDefaultTimeout(12000);
  await p.goto(base+'/gaming');assert.equal(await p.locator('.game-cards>a').count(),8);
  await p.locator('#gamingUsername').fill('EightGamePlayer');await p.locator('#gamingNameForm button').click();await p.locator('#gamingIdentity').waitFor();
  async function bet(){const wait=p.waitForResponse(r=>r.url().endsWith('/gaming/api/bet'));await p.locator('#betButton').click();const response=await wait,v=await response.json();assert.equal(response.status(),200,JSON.stringify(v));await p.waitForFunction(()=>document.getElementById('betButton').getAttribute('aria-busy')==='false');return v;}
  async function state(){return (await(await ctx.request.get(base+'/gaming/api/state')).json()).wallet;}
  for(const game of ['dice','keno','plinko','blackjack','limbo','coinflip','baccarat']){
   await p.goto(base+'/gaming/'+game);assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,game+' mobile overflow');
   if(game==='dice'){
    const slider=p.locator('#diceBoardChance');await slider.scrollIntoViewIfNeeded();const box=await slider.boundingBox();
    await p.mouse.move(box.x+box.width*.5,box.y+box.height/2);await p.mouse.down();
    await p.mouse.move(box.x+box.width*.7,box.y+box.height/2,{steps:8});await p.mouse.up();
    const chance=Number(await p.locator('#diceChance').inputValue());assert.ok(chance>60&&chance<80);
    assert.match(await p.locator('#diceChanceLabel').textContent(),new RegExp(String(chance)));
   }
   if(game==='keno')await p.locator('#kenoAuto').click();
   if(game==='limbo'){await p.locator('#limboTarget').fill('2.50');assert.match(await p.locator('#limboPayout').textContent(),/250 points/);}
   if(game==='coinflip'){await p.locator('.coin-options label').nth(1).click();assert.equal(await p.locator('[name=coinSide][value=tails]').isChecked(),true);}
   let navigations=0;
   const navigation=frame=>{if(frame===p.mainFrame())navigations++;};p.on('framenavigated',navigation);
   const watching=p.waitForResponse(r=>r.url().endsWith('/gaming/api/bet'));
   await p.locator('#betButton').click();const response=await watching;
   let result=await response.json();assert.equal(response.status(),200,JSON.stringify(result));
   if(result.receipt){
    await p.waitForFunction(()=>Boolean(document.querySelector('.gaming-page').dataset.animating));
    assert.equal(await p.locator('#betProof').textContent(),'','proof appears after motion');
    if(game==='keno'){
      await p.waitForFunction(()=>document.querySelectorAll('[data-keno].drawn').length>0);
      assert.ok(await p.locator('[data-keno].drawn').count()<10,'numbers reveal in order');
    }
    if(game==='baccarat'){
      await p.waitForFunction(()=>document.querySelectorAll('.baccarat-hand [data-card]').length>0);
      assert.ok(await p.locator('.baccarat-hand [data-card]').count()<result.receipt.result.player.length+result.receipt.result.banker.length,'cards deal in sequence');
    }
   }
   await p.waitForFunction(()=>document.getElementById('betButton').getAttribute('aria-busy')==='false');
   if(result.wallet.blackjack){const wait=p.waitForResponse(r=>r.url().endsWith('/gaming/api/blackjack/action'));await p.locator('[data-blackjack=stand]').click();result=await(await wait).json();}
   await p.locator('#betProof').filter({hasText:'Verified'}).waitFor();
   assert.equal(navigations,0,game+' must not navigate on play');p.off('framenavigated',navigation);
   if(game==='baccarat'){
    const r=result.receipt.result;
    for(const side of ['player','banker']){
     const label=side[0].toUpperCase()+side.slice(1);
     assert.deepEqual(await p.locator('#baccarat'+label+' [data-card]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.card))),r[side]);
     assert.equal(await p.locator('#baccarat'+label+'Total').textContent(),String(r[side+'_total']));
    }
    await p.evaluate(()=>{document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'});});await p.screenshot({path:dir+'/baccarat-mobile.png',fullPage:true});
   }
   if(game==='limbo'){await p.waitForTimeout(1100);assert.equal(await p.locator('#limboResult').textContent(),(result.receipt.result.multiplier/100).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+'×');await p.screenshot({path:dir+'/limbo-mobile.png',fullPage:true});}
   if(game==='coinflip'){await p.waitForTimeout(1100);assert.equal(await p.locator('#redCoin').getAttribute('aria-label'),result.receipt.result.side==='heads'?'Heads':'Tails');await p.screenshot({path:dir+'/coinflip-mobile.png',fullPage:true});}
  }
  // Keep overlapping drops distinct and alive when the canvas is resized.
  await p.goto(base+'/gaming/plinko');let last;
  for(let n=0;n<3;n++)last=await bet();
  await p.setViewportSize({width:430,height:900});
  await p.waitForFunction(n=>document.getElementById('betProof').textContent===`Verified · #${n}`,last.receipt.nonce);
  assert.match(await p.locator('#plinkoResult').textContent(),new RegExp('Slot '+last.receipt.result.slot));
  await p.setViewportSize({width:390,height:844});
  // Hidden-tab completion cannot strand a verified round or keep Play locked.
  await p.goto(base+'/gaming/baccarat');
  const hiddenBet=p.waitForResponse(r=>r.url().endsWith('/gaming/api/bet'));await p.locator('#betButton').click();
  const hiddenResult=await(await hiddenBet).json();
  await p.waitForFunction(()=>document.querySelector('.gaming-page').dataset.animating==='baccarat');
  await p.evaluate(()=>{Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));});
  await p.locator('#betProof').filter({hasText:'Verified'}).waitFor();
  assert.equal(await p.locator('#baccaratBankerTotal').textContent(),String(hiddenResult.receipt.result.banker_total));
  await p.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
  await p.goto(base+'/gaming/poker');let opened=await bet();assert.ok(opened.wallet.poker);const initial=opened.wallet.poker.initial;
  assert.equal(initial.length,2);assert.deepEqual(opened.wallet.poker.computer,[null,null]);
  assert.equal(await p.locator('#holdemComputerCards .is-hidden').count(),2);
  await p.waitForTimeout(5200);assert.deepEqual((await state()).poker.initial,initial);
  const refresh=p.waitForResponse(r=>r.url().endsWith('/gaming/api/refresh'));await p.reload();assert.equal((await(await refresh).json()).wallet.balance,100000);
  assert.deepEqual((await state()).poker.initial,initial);
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Holdem mobile overflow');
  await p.evaluate(()=>{document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'});});await p.screenshot({path:dir+'/holdem-mobile.png',fullPage:true});
  async function pokerMove(action){
    const watching=p.waitForResponse(r=>r.url().endsWith('/gaming/api/poker/action'));
    await p.locator('[data-holdem="'+action+'"]').click();const response=await watching,value=await response.json();assert.equal(response.status(),200,JSON.stringify(value));
    await p.waitForFunction(()=>document.getElementById('betButton').getAttribute('aria-busy')==='false');
    return value;
  }
  let result=opened;
  while(result.wallet.poker)result=await pokerMove(result.wallet.poker.legal.check?'check':'call');
  assert.deepEqual(result.receipt.result.initial,initial);await p.locator('#betProof').filter({hasText:'Verified'}).waitFor();
  if(result.receipt.result.reason==='showdown'){
    assert.equal(await p.locator('#holdemBoard .playing-card').count(),5);
    assert.equal(await p.locator('#holdemComputerCards .is-hidden').count(),0);
    assert.ok(await p.locator('.playing-card.is-winning').count()>=5);
  }
  await p.setViewportSize({width:1280,height:900});await p.evaluate(()=>{document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'});});await p.screenshot({path:dir+'/holdem-desktop-result.png',fullPage:true});
  // Reach the player's button. A folded computer opening hand is still a valid settled round.
  for(let n=0;n<4;n++){
    opened=await bet();
    if(opened.wallet.poker?.button==='player')break;
    while(opened.wallet.poker)opened=await pokerMove(opened.wallet.poker.legal.check?'check':'call');
  }
  assert.equal(opened.wallet.poker.button,'player');const prior=(await state()).stats.poker.bets;let lost=false;
  await p.route('**/gaming/api/poker/action',async route=>{if(!lost){lost=true;await route.fetch();await route.abort('failed');}else await route.continue();});
  await p.locator('[data-holdem=fold]').click();await p.locator('#betProof').filter({hasText:'Verified'}).waitFor({timeout:16000});
  const saved=await state();assert.equal(saved.stats.poker.bets,prior+1);assert.equal(saved.poker,null);assert.equal(saved.receipts[0].actions.at(-1).action,'fold');
  await p.unroute('**/gaming/api/poker/action');
  await p.emulateMedia({reducedMotion:'reduce'});await p.goto(base+'/gaming/baccarat');
  result=await bet();await p.locator('#betProof').filter({hasText:'Verified'}).waitFor();
  assert.equal(await p.locator('#baccaratPlayerTotal').textContent(),String(result.receipt.result.player_total));
  await p.emulateMedia({reducedMotion:'no-preference'});
  const admin=await ctx.newPage();admin.on('pageerror',e=>errors.push(e.message));await admin.goto(base+'/admin/gaming');await admin.locator('#username').fill('fixtureadmin');await admin.locator('#password').fill('fixture-only');await admin.locator('form button[type=submit]').click();await admin.locator('#grantGamingButton').waitFor();await admin.goto(base+'/admin/gaming');
  for(const game of ['dice','keno','plinko','blackjack','limbo','coinflip','poker','baccarat'])assert.match(await admin.locator('#gamingLeaders-'+game).textContent(),/EightGamePlayer/);
  await p.goto(base+'/gaming');await p.screenshot({path:dir+'/dashboard-desktop.png',fullPage:true});
  assert.deepEqual(errors,[]);console.log(JSON.stringify({eight_games_play_and_verify:true,animated_reveals_without_navigation:true,dice_drag_synced:true,overlapping_plinko_survives_resize:true,hidden_tab_exact_completion:true,holdem_cards_and_stack_persist_after_poll_and_reload:true,holdem_lost_action_recovers_once:true,admin_tracks_eight_games:true,exact_limbo_result:true,coin_face_matches_result:true,mobile_no_overflow:true,page_errors:errors}));
 }finally{if(browser)await browser.close();server.kill('SIGTERM');}
})().catch(e=>{console.error(e);process.exitCode=1;});
