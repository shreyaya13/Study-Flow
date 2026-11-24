document.addEventListener("DOMContentLoaded", () => {
  // Focus timer
  const display=document.getElementById("timerDisplay");
  if(display){
    let mode="focus", remaining=25*60, interval=null, completed=false;
    const start=document.getElementById("timerStart"), reset=document.getElementById("timerReset");
    const state=document.getElementById("timerState"), save=document.getElementById("sessionForm");
    const tabs=document.querySelectorAll(".timer-tab");
    const render=()=>{display.textContent=String(Math.floor(remaining/60)).padStart(2,"0")+":"+String(remaining%60).padStart(2,"0");};
    const stop=()=>{if(interval){clearInterval(interval);interval=null;}};
    const setMode=(next)=>{stop();mode=next;remaining=(mode==="focus"?25:5)*60;completed=false;save.classList.add("hidden");start.textContent="Start "+(mode==="focus"?"focus":"break");state.textContent=mode==="focus"?"READY TO FOCUS":"TIME TO RESET";tabs.forEach(t=>t.classList.toggle("selected",t.dataset.mode===mode));render();};
    tabs.forEach(t=>t.addEventListener("click",()=>setMode(t.dataset.mode)));
    start.addEventListener("click",()=>{
      if(interval){stop();start.textContent="Resume";state.textContent="PAUSED";return;}
      if(remaining===0)return;
      state.textContent=mode==="focus"?"YOU'RE IN THE ZONE":"TAKE A BREATHER";start.textContent="Pause";
      interval=setInterval(()=>{remaining--;render();if(remaining<=0){stop();state.textContent="SESSION COMPLETE";start.textContent="Completed";if(mode==="focus"){document.getElementById("sessionMinutes").value=25;save.classList.remove("hidden");}else{start.textContent="Start break";}completed=true;}},1000);
    });
    reset.addEventListener("click",()=>setMode(mode));
    render();
  }
  // Practice reveal
  const practice=document.getElementById("practiceCards");
  if(practice){
    const cards=[...practice.querySelectorAll(".practice-card")];
    const count=document.getElementById("practiceCount");
    cards.forEach((card,i)=>card.querySelector(".reveal-btn").addEventListener("click",()=>{
      card.querySelector(".answer-area").classList.remove("hidden");
      card.querySelector(".reveal-btn").classList.add("hidden");
    }));
    if(count) count.textContent=`${cards.length} CARD${cards.length===1?"":"S"} DUE`;
  }
});
