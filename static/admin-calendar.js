(() => {
  "use strict";
  if (document.body.dataset.page !== "admin") return;
  const fmt = new Intl.DateTimeFormat("en-US", {timeZone:"America/New_York", month:"short", day:"numeric", year:"numeric", hour:"numeric", minute:"2-digit", timeZoneName:"short"});
  const utcFmt = new Intl.DateTimeFormat("en-CA", {timeZone:"UTC", year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", hourCycle:"h23"});
  function partsAt(date) {
    return Object.fromEntries(new Intl.DateTimeFormat("en-US", {timeZone:"America/New_York", year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", second:"2-digit", hourCycle:"h23"}).formatToParts(date).filter(p=>p.type!=="literal").map(p=>[p.type,p.value]));
  }
  function easternToDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return null;
    const [d,t]=value.split("T"), [y,m,day]=d.split("-").map(Number), [h,min]=t.split(":").map(Number);
    let guess=new Date(Date.UTC(y,m-1,day,h,min));
    for(let i=0;i<3;i++){
      const p=partsAt(guess); const represented=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute);
      const wanted=Date.UTC(y,m-1,day,h,min); guess=new Date(guess.getTime()+(wanted-represented));
    }
    return guess;
  }
  function localValue(date) {
    const p=partsAt(date); return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
  }
  function initialize(form) {
    const prefix=form.dataset.calendarForm === "empiredrop" ? "empire" : "shuffle";
    const hiddenStart=document.getElementById(prefix === "empire" ? "empireStart" : "start_et");
    const hiddenEnd=document.getElementById(prefix === "empire" ? "empireEnd" : "end_et");
    const dateStart=form.querySelector('[data-calendar-date="start"]'), timeStart=form.querySelector('[data-calendar-time="start"]');
    const dateEnd=form.querySelector('[data-calendar-date="end"]'), timeEnd=form.querySelector('[data-calendar-time="end"]');
    const preview=form.querySelector('[data-calendar-preview]'), utc=form.querySelector('[data-calendar-utc]');
    const mismatch=document.getElementById("empireScheduleMismatch");
    function sync() {
      const start=`${dateStart.value}T${timeStart.value}`, end=`${dateEnd.value}T${timeEnd.value}`;
      hiddenStart.value=start; hiddenEnd.value=end;
      const a=easternToDate(start), b=easternToDate(end), valid=a&&b&&b>a;
      preview.textContent=valid ? `${fmt.format(a)} → ${fmt.format(b)}` : "Choose an end after the start.";
      utc.textContent=valid ? `UTC: ${utcFmt.format(a)} → ${utcFmt.format(b)}` : "";
      preview.closest('.calendar-preview')?.classList.toggle('is-invalid', !valid);
      if (mismatch && form.dataset.calendarForm === "empiredrop") {
        const official=form.closest('.empire-schedule')?.querySelector('.official-schedule-card');
        const oa=official?.dataset.officialStart ? (/^\d+$/.test(official.dataset.officialStart) ? new Date(Number(official.dataset.officialStart)*1000) : new Date(official.dataset.officialStart)) : null;
        const ob=official?.dataset.officialEnd ? (/^\d+$/.test(official.dataset.officialEnd) ? new Date(Number(official.dataset.officialEnd)*1000) : new Date(official.dataset.officialEnd)) : null;
        mismatch.hidden=!(valid&&oa&&!Number.isNaN(oa.getTime())&&ob&&!Number.isNaN(ob.getTime()) && (Math.abs(a-oa)>60000 || Math.abs(b-ob)>60000));
      }
      return valid;
    }
    for (const node of [dateStart,timeStart,dateEnd,timeEnd]) node?.addEventListener('input',sync);
    form.addEventListener('submit', event => { if(!sync()){event.preventDefault(); preview.focus?.();} });
    form.addEventListener('reset', () => queueMicrotask(sync));
    form.querySelectorAll('[data-calendar-preset]').forEach(button=>button.addEventListener('click',()=>{
      const now=new Date(), p=partsAt(now);
      const weekday={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6}[new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short'}).format(now)];
      const delta=(weekday-2+7)%7;
      const dayDate=new Date(Date.UTC(+p.year,+p.month-1,+p.day-delta));
      const y=dayDate.getUTCFullYear(), m=String(dayDate.getUTCMonth()+1).padStart(2,'0'), d=String(dayDate.getUTCDate()).padStart(2,'0');
      let start=easternToDate(`${y}-${m}-${d}T18:00`);
      if(button.dataset.calendarPreset==='next') start=new Date(start.getTime()+7*86400000);
      if(button.dataset.calendarPreset==='today') start=now;
      const end=new Date(start.getTime()+7*86400000);
      const sv=localValue(start), ev=localValue(end); dateStart.value=sv.slice(0,10);timeStart.value=sv.slice(11,16);dateEnd.value=ev.slice(0,10);timeEnd.value=ev.slice(11,16);sync();
    }));
    sync();
  }
  document.querySelectorAll('form[data-calendar-form]').forEach(initialize);
  document.getElementById('syncEmpireSchedule')?.addEventListener('click',()=>{
    const card=document.querySelector('.official-schedule-card'); const form=document.querySelector('form[data-calendar-form="empiredrop"]');
    if(!card||!form||!card.dataset.officialStart||!card.dataset.officialEnd) return;
    const startRaw=card.dataset.officialStart, endRaw=card.dataset.officialEnd;
    const a=/^\d+$/.test(startRaw) ? new Date(Number(startRaw)*1000) : new Date(startRaw);
    const b=/^\d+$/.test(endRaw) ? new Date(Number(endRaw)*1000) : new Date(endRaw);
    if(Number.isNaN(a.getTime())||Number.isNaN(b.getTime())) return;
    const av=localValue(a), bv=localValue(b); form.querySelector('[data-calendar-date="start"]').value=av.slice(0,10);form.querySelector('[data-calendar-time="start"]').value=av.slice(11,16);form.querySelector('[data-calendar-date="end"]').value=bv.slice(0,10);form.querySelector('[data-calendar-time="end"]').value=bv.slice(11,16);form.querySelector('[data-calendar-date="start"]').dispatchEvent(new Event('input',{bubbles:true}));
  });
})();
