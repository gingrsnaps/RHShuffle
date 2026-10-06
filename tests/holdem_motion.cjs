/* Focused native-browser checks for new controls and an actual v4 migration. */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
(async()=>{
 const server=spawn(process.env.RH_TEST_PYTHON||'python3',[path.join(__dirname,'serve_gaming_motion_fixture.py'),'--legacy']);
 let output='',browser;server.stdout.on('data',b=>output+=b);server.stderr.on('data',b=>process.stderr.write(b));
 try{
  for(let n=0;n<100&&!output.includes('\n');n++)await new Promise(r=>setTimeout(r,50));
  const fixture=JSON.parse(output.split('\n')[0]),base='http://127.0.0.1:'+fixture.port;
  browser=await chromium.launch({executablePath:process.env.RH_CHROMIUM||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'],headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
  await page.goto(base+'/gaming/poker');await page.locator('#gamingUsername').fill('Control Player');await page.locator('#gamingNameForm button').click();await page.locator('#gamingIdentity').waitFor();
  async function ready(){await page.waitForFunction(()=>document.querySelector('#betButton').getAttribute('aria-busy')==='false');}
  async function bet(){const waiting=page.waitForResponse(r=>r.url().endsWith('/gaming/api/bet'));await page.locator('#betButton').click();const value=await(await waiting).json();assert.ok(value.ok,JSON.stringify(value));await ready();return value;}
  async function move(selector){const waiting=page.waitForResponse(r=>r.url().endsWith('/gaming/api/poker/action'));await page.locator(selector).click();const value=await(await waiting).json();assert.ok(value.ok,JSON.stringify(value));await ready();return value;}
  async function complete(value){while(value.wallet.poker)value=await move('[data-holdem='+ (value.wallet.poker.legal.check?'check':'call')+']');await page.locator('#betProof').filter({hasText:'Verified'}).waitFor();return value;}
  let value=await bet(),hand=value.wallet.poker;
  assert.equal(hand.legal.min_raise_to,40);
  await page.locator('#holdemRaise').fill('30');assert.equal(await page.locator('#holdemRaiseButton').isDisabled(),true);
  await page.locator('[data-holdem-size=min]').click();assert.equal(await page.locator('#holdemRaise').inputValue(),'40');
  assert.match(await page.locator('#holdemRaiseCost').textContent(),/30 more/);
  value=await move('#holdemRaiseButton');
  const actions=value.receipt?.actions || value.wallet.poker.actions;assert.deepEqual(actions[0],{action:'raise',amount:40});
  await complete(value);
  // Find the player's button so the initial move always waits for this browser.
  for(let n=0;n<4;n++){value=await bet();if(value.wallet.poker?.button==='player')break;await complete(value);}
  assert.equal(value.wallet.poker.button,'player');
  let lost=false;await page.route('**/gaming/api/poker/action',async route=>{if(!lost){lost=true;await route.fetch();await route.abort('failed');}else await route.continue();});
  await page.locator('[data-holdem=call]').click();
  await page.waitForFunction(()=>!sessionStorage.getItem('rh.gaming.action'),{},{timeout:18000});
  const state=await(await context.request.get(base+'/gaming/api/state')).json();assert.equal(state.wallet.poker.step,1);
  assert.deepEqual(state.wallet.poker.actions[0],{action:'call',amount:0});await page.unroute('**/gaming/api/poker/action');
  await complete({wallet:state.wallet});
  for(let n=0;n<4;n++){value=await bet();if(value.wallet.poker?.button==='player')break;await complete(value);}
  let posts=0;page.on('request',r=>{if(r.url().endsWith('/gaming/api/poker/action'))posts++;});
  const allIn=page.waitForResponse(r=>r.url().endsWith('/gaming/api/poker/action'));
  await page.locator('[data-holdem=all_in]').evaluate(button=>{button.click();button.click();});
  value=await(await allIn).json();assert.ok(value.receipt,JSON.stringify(value));await ready();assert.equal(posts,1);assert.equal(value.receipt.actions[0].action,'all_in');
  await page.locator('#betProof').filter({hasText:'Verified'}).waitFor();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const directory=process.env.RH_SCREENSHOTS;
  if(directory){fs.mkdirSync(directory,{recursive:true});await page.evaluate(()=>{document.activeElement?.blur();scrollTo({top:0,behavior:'instant'});});await page.screenshot({path:path.join(directory,'holdem-mobile-final.png'),fullPage:true});await page.setViewportSize({width:1280,height:900});await page.screenshot({path:path.join(directory,'holdem-desktop-final.png'),fullPage:true});}
  const legacy=await browser.newContext({viewport:{width:390,height:844}});await legacy.addCookies([{name:'rh_raider',value:fixture.legacy_cookie,url:base}]);
  const old=await legacy.newPage();old.on('pageerror',e=>errors.push(e.message));
  await old.goto(base+'/gaming/poker');await old.locator('#legacyPokerTable').waitFor();assert.equal(await old.locator('[data-poker-hold]').count(),5);assert.equal(await old.locator('#holdemTable').isHidden(),true);
  await old.locator('#pokerHoldAll').click();const draw=old.waitForResponse(r=>r.url().endsWith('/gaming/api/poker/action'));await old.locator('#pokerDraw').click();
  const drawn=await(await draw).json();assert.ok(drawn.ok,JSON.stringify(drawn));assert.equal(drawn.receipt.rules_version,'redpoints-v4');assert.equal(drawn.wallet.stats.poker.bets,0);assert.equal(drawn.wallet.legacy_poker.bets,1);await old.locator('#betProof').filter({hasText:'Verified'}).waitFor();
  assert.match(await old.locator('#betHistory').textContent(),/Video Poker · legacy/);
  const deal=old.waitForResponse(r=>r.url().endsWith('/gaming/api/bet'));await old.locator('#betButton').click();const newHand=await(await deal).json();assert.ok(newHand.ok,JSON.stringify(newHand));assert.equal(newHand.wallet.poker.variant,'texas_holdem');await old.locator('#holdemTable').waitFor();assert.equal(await old.locator('#legacyPokerTable').isHidden(),true);
  await page.goto(base+'/gaming/fairness');assert.equal(await page.locator('#holdem').count(),1);assert.equal(await page.evaluate(()=>typeof RedHoldemFair.replay),'function');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({raises_and_costs:true,all_in_double_click_commits_once:true,lost_nonterminal_response_recovers:true,legacy_draw_then_holdem:true,mobile_no_overflow:true,page_errors:errors}));
 }finally{if(browser)await browser.close();server.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
