import {$,el,api,notify,button,td,money,lineChart,download,nav} from './common.js';
const colors=['#315e50','#9b7748','#59728b'];let result=null;
function render(r){
 result=r;$('#result-empty').hidden=true;$('#result').hidden=false;$('#export').disabled=false;$('#result-title').textContent=r.config.name;const best=r.strategies[r.best];$('#winner').textContent=r.best+' produced the highest mean simulated profit: '+money(best.profit)+'.';
 const rows=$('#strategies');rows.replaceChildren();Object.entries(r.strategies).forEach(([name,s])=>{const tr=el('tr');tr.append(td(name),td(money(s.profit)),td(s.units.toFixed(1)));rows.append(tr)});
 const strategies=Object.entries(r.strategies);lineChart($('#profit-chart'),strategies.map(([name,s],i)=>({values:s.daily_profit,color:colors[i]})));lineChart($('#stock-chart'),strategies.map(([name,s],i)=>({values:s.daily_stock,color:colors[i]})));
 $('#uncertainty').replaceChildren(el('div','Trial spread','section-label'),...strategies.map(([name,s])=>el('p',name+': '+money(s.profit_p10)+'–'+money(s.profit_p90)+' profit (10th–90th percentile), '+s.remaining.toFixed(1)+' units left.','note')));
}
$('#experiment-form').onsubmit=async e=>{
 e.preventDefault();const b=$('#run');b.disabled=true;notify('Running paired strategy trials…');
 try{const config=Object.fromEntries(new FormData(e.target));Object.keys(config).filter(k=>k!=='name').forEach(k=>config[k]=Number(config[k]));const r=await api('/api/experiments','POST',config);render(r);await history();notify('Experiment saved. Results use the assumptions shown.')}finally{b.disabled=false}
};
async function history(){
 const rows=await api('/api/experiments'),body=$('#history');body.replaceChildren();
 if(!rows.length){const tr=el('tr'),cell=td('No experiments yet.');cell.colSpan=5;tr.append(cell);body.append(tr)}
 for(const r of rows){const tr=el('tr'),open=td('');open.append(button('Open run',()=>{for(const [name,value]of Object.entries(r.config)){const input=$('#experiment-form').elements.namedItem(name);if(input)input.value=value}document.querySelector('[data-view="main"]').click();render(r)},'plain'));tr.append(td(r.config.name,'wrap'),td(new Date(r.created).toLocaleString()),td(r.config.seed),td(money(r.strategies[r.best].profit)),open);body.append(tr)}
}
$('#refresh-history').onclick=history;
$('#export').onclick=()=>{if(!result)return;const rows=['strategy,day,mean_price,mean_profit,mean_stock'];for(const [name,s]of Object.entries(result.strategies))s.daily_profit.forEach((p,i)=>rows.push([name,i+1,s.daily_price[i].toFixed(2),p.toFixed(2),s.daily_stock[i].toFixed(2)].join(',')));download('pricing-experiment-'+result.config.seed+'.csv',rows.join('\n'))};
nav(v=>{if(v==='history')history()});window.addEventListener('resize',()=>{if(result&&$('#view-main').style.display!=='none')render(result)});await history();
