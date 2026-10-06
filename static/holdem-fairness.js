/* Independent redpoints-v5 Hold'em replay. No network or wallet access.
   redbot-v1 receives only its own cards and the public betting observation.
   Keep this policy/version immutable so old receipts remain independently checkable. */
(() => {
  "use strict";
  const VARIANT = "texas_holdem", POLICY = "redbot-v1";
  const labels = ["High card", "One pair", "Two pair", "Three of a kind", "Straight", "Flush", "Full house", "Four of a kind", "Straight flush"];
  const streets = ["preflop", "flop", "turn", "river"], seats = ["player", "computer"];
  const copy = value => JSON.parse(JSON.stringify(value));
  function compare(a, b) {
    for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] > b[i] ? 1 : -1;
    return a.length - b.length;
  }
  function rankFive(cards) {
    const ranks = cards.map(c => c % 13 === 0 ? 14 : c % 13 + 1).sort((a,b) => b-a);
    const counts = new Map(); for (const rank of ranks) counts.set(rank, (counts.get(rank)||0)+1);
    const groups = [...counts].map(([rank,count]) => [count,rank]).sort((a,b) => compare(b,a));
    const unique = [...counts.keys()].sort((a,b) => a-b);
    const straight = String(unique) === "2,3,4,5,14" ? 5 : unique.length === 5 && unique[4]-unique[0] === 4 ? unique[4] : 0;
    const flush = new Set(cards.map(c => Math.floor(c/13))).size === 1;
    if (straight && flush) return [8,straight];
    if (groups[0][0] === 4) return [7,groups[0][1],groups[1][1]];
    if (String(groups.map(g=>g[0])) === "3,2") return [6,groups[0][1],groups[1][1]];
    if (flush) return [5,...ranks];
    if (straight) return [4,straight];
    const singles = groups.filter(g=>g[0]===1).map(g=>g[1]).sort((a,b)=>b-a);
    if (groups[0][0] === 3) return [3,groups[0][1],...singles];
    const pairs = groups.filter(g=>g[0]===2).map(g=>g[1]).sort((a,b)=>b-a);
    if (pairs.length === 2) return [2,...pairs,...singles];
    if (pairs.length) return [1,pairs[0],...singles];
    return [0,...ranks];
  }
  function bestHand(cards) {
    if (!Array.isArray(cards) || cards.length < 5 || cards.length > 7 || new Set(cards).size !== cards.length || cards.some(c=>!Number.isInteger(c)||c<0||c>=52)) throw Error("Invalid Hold'em cards");
    const sorted = [...cards].sort((a,b)=>a-b);
    let best = null, rank = null;
    function combinations(start, chosen) {
      if (chosen.length === 5) {
        const value = rankFive(chosen);
        if (!rank || compare(value, rank) > 0) { best = [...chosen]; rank = value; }
        return;
      }
      for (let i=start; i<=sorted.length-(5-chosen.length); i++) combinations(i+1, [...chosen, sorted[i]]);
    }
    combinations(0, []);
    return {rank, cards:best, label:labels[rank[0]]};
  }
  function validateAction(value) {
    if (!value || Array.isArray(value) || Object.keys(value).sort().join() !== "action,amount" ||
        !["fold","check","call","bet","raise","all_in"].includes(value.action) || !Number.isSafeInteger(value.amount) ||
        value.amount < 0 || value.amount > Math.floor(Number.MAX_SAFE_INTEGER/2) ||
        (!["bet","raise"].includes(value.action) && value.amount !== 0)) throw Error("Invalid Hold'em action");
    return {action:value.action, amount:value.amount};
  }
  function botAction(o) {
    const {hole:cards, board, legal} = o;
    const ranks = cards.map(c=>c%13===0?14:c%13+1).sort((a,b)=>b-a);
    let strength;
    if (!board.length) strength = ranks[0]===ranks[1] ? 65+ranks[0]*2 : ranks[0]*3+ranks[1]+(Math.floor(cards[0]/13)===Math.floor(cards[1]/13)?8:0)+(ranks[0]-ranks[1]===1?5:0);
    else {
      const rank = bestHand([...cards,...board]).rank;
      strength = rank[0]===0 ? rank[1]*2 : rank[0]===1 ? 40+rank[1]*2 : rank[0]===2 ? 75 : rank[0]===3 ? 90 : 110;
    }
    const sum = [...cards,...board].reduce((a,b)=>a+BigInt(b),BigInt(o.pot)+BigInt(o.street_index));
    const bluff = sum % 13n === 0n;
    if (legal.can_raise && o.raises === 0 && (strength>=80 || (bluff && !legal.call))) {
      const target = Math.min(legal.max_raise_to, Math.max(legal.min_raise_to, o.highest+Math.max(o.big_blind,Math.floor(o.pot/2))));
      if (target >= legal.min_raise_to) return {action:o.highest===0?"bet":"raise",amount:target};
    }
    if (legal.check) return {action:"check",amount:0};
    const cheap = BigInt(legal.call)*4n <= BigInt(o.pot), medium = BigInt(legal.call)*2n <= BigInt(o.pot);
    return {action:strength>=90 || (strength>=65 && medium) || (strength>=40 && cheap)?"call":"fold",amount:0};
  }
  class Hand {
    constructor(deck, buyIn, button) {
      if (!Number.isSafeInteger(buyIn) || buyIn<20 || buyIn>Math.floor(Number.MAX_SAFE_INTEGER/2) || !seats.includes(button) || deck.length!==52 || new Set(deck).size!==52) throw Error("Invalid Hold'em table");
      this.buyIn=buyIn; this.button=seats.indexOf(button);
      this.big=Math.max(2,Math.floor(buyIn/50)); this.small=Math.max(1,Math.floor(this.big/2));
      this.holes=[[],[]]; const first=1-this.button;
      for(let i=0;i<4;i++) this.holes[(first+i)%2].push(deck[i]);
      this.boards=[[],deck.slice(5,8),[...deck.slice(5,8),deck[9]],[...deck.slice(5,8),deck[9],deck[11]]];
      this.stacks=[buyIn,buyIn];this.committed=[0,0];this.bets=[0,0];this.acted=[false,false];this.raises=[0,0];
      this.street=0;this.actor=this.button;this.lastRaise=this.big;this.ended=false;this.winner=null;this.reason=null;
      this.refunds=[0,0];this.awards=[0,0];this.hands=[null,null];this.potAtEnd=0;this.events=[];
      this.pay(this.button,this.small);this.pay(1-this.button,this.big);
      this.event("deal",{seat:null,action:"blinds",amount:this.small+this.big});
    }
    pay(seat,amount) {this.stacks[seat]-=amount;this.committed[seat]+=amount;this.bets[seat]+=amount;}
    legal(seat) {
      if(this.ended)return {};
      const high=Math.max(...this.bets),call=Math.min(this.stacks[seat],high-this.bets[seat]),maximum=this.bets[seat]+this.stacks[seat];
      const canRaise=maximum>high && this.stacks[1-seat]>0;
      return {fold:true,check:call===0,call,can_raise:canRaise,min_raise_to:high+this.lastRaise,max_raise_to:maximum,all_in:this.stacks[seat]>0 && (canRaise || this.stacks[seat]<=call)};
    }
    snapshot() {
      return {player:[...this.holes[0]],computer:this.ended && this.reason==="showdown"?[...this.holes[1]]:[null,null],
        board:[...this.boards[this.street]],stacks:[...this.stacks],bets:[...this.bets],pot:this.ended?this.potAtEnd:this.committed[0]+this.committed[1],
        street:streets[this.street],turn:this.ended?null:seats[this.actor],ended:this.ended,winner:this.winner,reason:this.reason};
    }
    event(kind, extra) {this.events.push({kind,...extra,state:this.snapshot()});}
    observation() { const seat=this.actor;return {hole:[...this.holes[seat]],board:[...this.boards[this.street]],legal:this.legal(seat),pot:this.committed[0]+this.committed[1],highest:Math.max(...this.bets),big_blind:this.big,street_index:this.street,raises:this.raises[seat]}; }
    finish(winner=null) {
      const matched=Math.min(...this.committed);
      this.refunds=this.committed.map(v=>v-matched);
      for(let i=0;i<2;i++){this.stacks[i]+=this.refunds[i];this.committed[i]-=this.refunds[i];}
      this.potAtEnd=this.committed[0]+this.committed[1];this.reason=winner!==null?"fold":"showdown";
      if(winner===null){this.hands=this.holes.map(h=>bestHand([...h,...this.boards[3]]));const comparison=compare(this.hands[0].rank,this.hands[1].rank);winner=comparison>0?0:comparison<0?1:-1;}
      this.winner=winner===-1?"split":seats[winner];
      if(winner===-1){this.awards=[Math.floor(this.potAtEnd/2),Math.floor(this.potAtEnd/2)];this.awards[1-this.button]+=this.potAtEnd%2;}
      else this.awards[winner]=this.potAtEnd;
      for(let i=0;i<2;i++)this.stacks[i]+=this.awards[i];
      this.ended=true;this.event("settle",{seat:this.winner,action:this.reason,amount:this.potAtEnd});
      if(this.stacks[0]+this.stacks[1]!==this.buyIn*2 || Math.min(...this.stacks)<0)throw Error("Hold'em chips did not balance");
    }
    advance() {
      if(this.street===3){this.finish();return;}
      this.street++;this.bets=[0,0];this.acted=[false,false];this.raises=[0,0];this.lastRaise=this.big;this.actor=1-this.button;
      this.event("street",{seat:null,action:streets[this.street],amount:0});
      if(this.stacks.includes(0))this.advance();
    }
    move(value) {
      value=validateAction(value);if(this.ended)throw Error("Action after hand ended");
      const seat=this.actor,other=1-seat,legal=this.legal(seat),action=value.action;
      let amount=value.amount,paid;
      if(action==="fold"){this.event("action",{seat:seats[seat],action,amount:0});this.finish(other);return;}
      if(action==="check"){if(!legal.check)throw Error("Cannot check facing a bet");paid=0;}
      else if(action==="call"){if(!legal.call)throw Error("There is no bet to call");paid=legal.call;}
      else {
        const high=Math.max(...this.bets);
        if(action==="all_in"){if(!legal.all_in)throw Error("All-in unavailable");amount=legal.max_raise_to;}
        else if((action==="bet")!==(high===0))throw Error("Wrong bet/raise action");
        if(amount<=high){if(action!=="all_in" || this.stacks[seat]>legal.call)throw Error("A raise must increase the bet");}
        else {
          if(!legal.can_raise || amount>legal.max_raise_to || (amount<legal.min_raise_to && amount!==legal.max_raise_to))throw Error("Invalid raise size");
          const increase=amount-high;if(increase>=this.lastRaise)this.lastRaise=increase;
          this.raises[seat]++;this.acted[other]=false;
        }
        paid=amount-this.bets[seat];
      }
      if(paid<0 || paid>this.stacks[seat])throw Error("Not enough table chips");
      this.pay(seat,paid);this.acted[seat]=true;this.actor=other;
      this.event("action",{seat:seats[seat],action,amount:paid});
      if(this.bets[0]===this.bets[1] && (this.acted.every(Boolean)||this.stacks.includes(0)))this.advance();
      else if(this.stacks[other]===0 && this.bets[seat]>=this.bets[other]){
        while(this.street<3){this.street++;this.event("street",{seat:null,action:streets[this.street],amount:0});}this.finish();
      }
    }
    auto() {while(!this.ended && this.actor===1)this.move(botAction(this.observation()));}
    result(actions) {
      const value={...this.snapshot(),variant:VARIANT,policy:POLICY,initial:[...this.holes[0]],button:seats[this.button],small_blind:this.small,big_blind:this.big,buy_in:this.buyIn,
        legal:this.ended?{}:this.legal(0),actions:copy(actions),events:copy(this.events),total_wager:this.committed[0],returned:this.awards[0],refunds:[...this.refunds],best:copy(this.hands),payout:this.ended?this.stacks[0]:0};
      if(this.ended)value.computer=[...this.holes[1]];
      return value;
    }
  }
  async function replay(pick,buyIn,options,actions,ending) {
    if(!options || options.variant!==VARIANT || Object.keys(options).sort().join()!=="button,variant" || !Array.isArray(actions) || actions.length>4096)throw Error("Invalid Hold'em history");
    const deck=Array.from({length:52},(_,i)=>i);
    for(let i=0;i<51;i++){const j=i+await pick(52-i);[deck[i],deck[j]]=[deck[j],deck[i]];}
    const hand=new Hand(deck,buyIn,options.button),moves=[];hand.auto();
    for(const action of actions){const move=validateAction(action);if(hand.ended||hand.actor!==0)throw Error("Unexpected player action");hand.move(move);moves.push(move);hand.auto();}
    if(ending!==undefined && ending!==null){if(ending!=="weekly_reset"||hand.ended)throw Error("Invalid automatic settlement");hand.move({action:"fold",amount:0});}
    return hand.result(moves);
  }
  globalThis.RedHoldemFair={VARIANT,POLICY,labels,rankFive,bestHand,validateAction,botAction,Hand,replay};
  if(typeof module!=="undefined")module.exports=globalThis.RedHoldemFair;
})();
