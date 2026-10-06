/* Present only saved server events. Animation never decides cards, chips or wins. */
(() => {
  "use strict";
  function create(root, hooks) {
    const id = name => root.querySelector("#"+name), table=id("holdemTable");
    if (!table) return null;
    const fmt=hooks.number, reduced=()=>document.hidden || matchMedia("(prefers-reduced-motion: reduce)").matches;
    let hand=null, round="", seen=0, initial=true, moving=false, externalLock=true, queue=Promise.resolve();
    function status(text){id("holdemStatus").textContent=text;}
    const name=seat=>seat==="player"?"You":"RedBot";
    function describe(event) {
      if(event.kind==="deal")return "Blinds posted. Cards dealt.";
      if(event.kind==="street")return event.action[0].toUpperCase()+event.action.slice(1)+" dealt.";
      if(event.kind==="settle")return event.seat==="split"?"Split pot.":`${name(event.seat)} won ${fmt(event.amount)}.`;
      const action={fold:"folded",check:"checked",call:"called",bet:"bet",raise:"raised",all_in:"went all-in"}[event.action];
      return `${name(event.seat)} ${action}${event.amount?" · "+fmt(event.amount):""}.`;
    }
    async function cards(target, values, count, animate, offset=0, spacing=85) {
      const jobs=[];
      for(let i=0;i<count;i++){
        const value=i<values.length?values[i]:undefined, key=value===undefined?"slot":String(value), old=target.children[i];
        if(old?.dataset.card===key)continue;
        const node=value===undefined?Object.assign(document.createElement("span"),{className:"holdem-card-slot"}):hooks.playingCard(value);
        node.dataset.card=key;
        if(old)old.replaceWith(node);else target.append(node);
        if(animate && value!==undefined){
          const flip=old?.dataset.card==="null" && value!==null;
          jobs.push((async()=>{
            await hooks.tween(offset+i*spacing,()=>{});
            await hooks.animateElement(node,flip?[{transform:"rotateY(90deg)",opacity:.3},{transform:"rotateY(0)",opacity:1}]:[{transform:"translateY(-14px) scale(.94)",opacity:0},{transform:"translateY(0) scale(1)",opacity:1}],240);
          })());
        }
      }
      await Promise.all(jobs);
    }
    async function paint(state, animate, event=null) {
      id("holdemComputerStack").textContent=fmt(state.stacks[1])+" RP";
      id("holdemPlayerStack").textContent=fmt(state.stacks[0])+" RP";
      id("holdemPot").textContent=fmt(state.pot);
      id("holdemComputerBet").textContent=state.ended?" ":state.bets[1]?fmt(state.bets[1])+" in this round":" ";
      id("holdemPlayerBet").textContent=state.ended?" ":state.bets[0]?fmt(state.bets[0])+" in this round":" ";
      id("holdemStreet").textContent=state.ended?state.reason==="showdown"?"Showdown":"Hand complete":state.street;
      const dealing=event?.kind==="deal";
      // Opening deal follows the two alternating seats; later streets reveal in order.
      await Promise.all([
        cards(id("holdemComputerCards"),state.computer,2,animate,dealing && hand.button==="computer"?85:0,dealing?170:85),
        cards(id("holdemPlayerCards"),state.player,2,animate,dealing && hand.button==="player"?85:0,dealing?170:85),
        cards(id("holdemBoard"),state.board,5,animate),
      ]);
      if(animate && event?.amount && ["action","settle"].includes(event.kind)){
        const direction=event.seat==="player"?1:-1;
        await hooks.animateElement(id("holdemChip"),[{transform:`translateY(${direction*24}px) scale(.8)`,opacity:.2},{transform:"translateY(0) scale(1)",opacity:1}],200);
      }
    }
    function cost() {
      if(!hand?.legal)return;
      const value=Number(id("holdemRaise").value),valid=Number.isSafeInteger(value) && value>=hand.legal.min_raise_to && value<=hand.legal.max_raise_to;
      id("holdemRaiseCost").textContent=valid?`${fmt(value-hand.bets[0])} more`:"Choose a legal raise.";
      id("holdemRaiseButton").disabled=externalLock||moving||!valid||!hand.legal.can_raise;
    }
    function controls(locked=externalLock) {
      externalLock=locked;
      const active=hand && !hand.ended;
      id("holdemControls").hidden=!active;
      if(!active)return;
      const legal=hand.legal;
      root.querySelectorAll("[data-holdem]").forEach(button=>{
        const action=button.dataset.holdem;
        button.hidden=action==="check"?!legal.check:action==="call"?!legal.call:action==="fold"?legal.check:!legal.all_in;
        button.disabled=locked||moving;
        if(action==="call")button.textContent=`Call ${fmt(legal.call)}`;
        if(action==="all_in")button.textContent=`All-in ${fmt(hand.stacks[0])}`;
      });
      id("holdemRaiseControls").hidden=!legal.can_raise || legal.max_raise_to<legal.min_raise_to;
      root.querySelectorAll("[data-holdem-size],#holdemRaise").forEach(el=>el.disabled=locked||moving);
      cost();
    }
    function tiebreak(winner) {
      const a=hand.best[winner].rank,b=hand.best[1-winner].rank;
      if(a[0]!==b[0])return "";
      const index=a.findIndex((value,i)=>i>0 && value!==b[i]);
      if(index<0)return "";
      const rank=({14:"A",13:"K",12:"Q",11:"J"})[a[index]]||String(a[index]);
      const primary={0:"high card",1:"higher pair",2:"higher pair",3:"higher trips",4:"higher straight",5:"flush high card",6:"higher trips",7:"higher quads",8:"higher straight flush"};
      const label=index===1?primary[a[0]]:a[0]===2 && index===2?"higher second pair":a[0]===6?"higher pair":"kicker";
      return ` · ${rank} ${label}`;
    }
    function finishView() {
      const legal=hand.legal;
      if(!hand.ended){
        id("holdemRaise").min=legal.min_raise_to;id("holdemRaise").max=legal.max_raise_to;
        id("holdemRaise").value=String(Math.min(legal.min_raise_to,legal.max_raise_to));
        const betting=Math.max(...hand.bets)===0;
        id("holdemRaiseButton").textContent=betting?"Bet":"Raise";
        root.querySelector('label[for="holdemRaise"]').textContent=betting?"Bet · RedPoints":"Raise to · RedPoints";
        status(legal.check?"Your turn · check or bet.":`Your turn · ${fmt(legal.call)} to call.`);
      }else{
        const winner=hand.winner,net=hand.payout-hand.buy_in;
        let text=winner==="split"?"Split pot":winner==="player"?"You win":"RedBot wins";
        if(hand.reason==="fold")text+=winner==="player"?" · opponent folded":" · you folded";
        else if(winner==="split")text+=" · "+hand.best[0].label;
        else {const seat=winner==="player"?0:1;text+=" · "+hand.best[seat].label+tiebreak(seat);}
        status(`${text}. ${net>0?"+":""}${fmt(net)} RP net.`);
        const winning=winner==="split"?[0,1]:[winner==="player"?0:1];
        const highlights=new Set(winning.flatMap(i=>hand.best[i]?.cards||[]));
        table.querySelectorAll(".playing-card[data-card]").forEach(node=>node.classList.toggle("is-winning",highlights.has(Number(node.dataset.card))));
      }
      controls();
    }
    function render(next) {
      if(!next){initial=false;return queue;}
      const newRound=round!==next.round_id;
      if(!newRound && next.events.length<=seen){controls();return queue;}
      const animate=!initial;initial=false;
      const start=newRound?0:seen;seen=next.events.length;round=next.round_id;
      moving=true;controls();
      queue=queue.then(async()=>{
        hand=next;
        if(newRound){
          for(const name of ["holdemPlayerCards","holdemComputerCards","holdemBoard"])id(name).replaceChildren();
          table.querySelectorAll(".is-winning").forEach(n=>n.classList.remove("is-winning"));
        }
        id("holdemBlinds").textContent=`Blinds ${fmt(next.small_blind)} / ${fmt(next.big_blind)}`;
        id("holdemPlayerButton").hidden=next.button!=="player";id("holdemComputerButton").hidden=next.button!=="computer";
        const events=next.events.slice(start);
        if(animate){
          for(const event of events){
            if(event.kind==="action" && event.seat==="computer" && !reduced()){
              status("RedBot is thinking…");await hooks.tween(360,()=>{});
            }
            status(describe(event));await paint(event.state,true,event);
            if(!reduced() && event.kind==="street")await hooks.tween(160,()=>{});
          }
        }else await paint(next.events.at(-1).state,false);
        id("holdemLog").replaceChildren(...next.events.map(event=>Object.assign(document.createElement("li"),{textContent:describe(event)})));
        finishView();
      }).catch(error=>{hooks.error(error.message);}).finally(()=>{moving=false;controls();hooks.changed();});
      return queue;
    }
    root.querySelectorAll("[data-holdem]").forEach(button=>button.addEventListener("click",()=>{
      if(externalLock||moving||!hand||hand.ended)return;
      hooks.move({action:button.dataset.holdem,amount:0});
    }));
    id("holdemRaise").addEventListener("input",cost);
    id("holdemRaiseButton").addEventListener("click",()=>{
      if(externalLock||moving||id("holdemRaiseButton").disabled)return;
      hooks.move({action:Math.max(...hand.bets)===0?"bet":"raise",amount:Number(id("holdemRaise").value)});
    });
    root.querySelectorAll("[data-holdem-size]").forEach(button=>button.addEventListener("click",()=>{
      if(!hand||externalLock||moving)return;
      const high=Math.max(...hand.bets),size=button.dataset.holdemSize;
      const desired=size==="min"?hand.legal.min_raise_to:high+Math.max(hand.big_blind,Math.floor((hand.pot+hand.legal.call)/(size==="half"?2:1)));
      id("holdemRaise").value=String(Math.max(hand.legal.min_raise_to,Math.min(hand.legal.max_raise_to,desired)));cost();
    }));
    return {render,controls,isMoving:()=>moving};
  }
  globalThis.RedHoldemUI={create};
})();
