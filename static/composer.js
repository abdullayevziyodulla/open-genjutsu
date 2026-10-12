/* Local media selection. No provider uploads or inference in these controls. */
const removedReferences=new Set(), referenceUrls={}, referenceNames={};
let pickerSlot='sirio', pickerView='upload', modelSaving=false;
const modelChoices=[
 {provider:'oxen',engine:'seedance',title:'Seedance 2.5',tag:'OXEN',description:'Prepared video + character identity',quality:'480p draft · 1080p final'},
 {provider:'replicate',engine:'seedance',title:'Seedance 2.5',tag:'REPLICATE',description:'Image identity + prepared motion guidance',quality:'480p preview · new 720p render'},
 {provider:'replicate',engine:'wan',title:'Wan 2.2 Animate',tag:'REPLICATE',description:'Single-photo replacement with original motion',quality:'480p preview · new 720p render'},
 {provider:'lec',engine:'seedance',title:'Seedance 2.5',tag:'LEC',description:'Prepared-video reference editing',quality:'720p generation'}
];
function isWan(){return $('#generation-engine').value==='wan'}
function syncComposerControls(){
 $('#form').classList.toggle('source-ready',Boolean($('#form').elements.video.files.length));
 const choice=modelChoices.find(c=>c.provider===provider()&&c.engine===$('#generation-engine').value);
 const title=$('#selected-model');title.replaceChildren(document.createTextNode(choice?.title||'Saved model'));
 const tag=document.createElement('em');tag.textContent=providerLabel().toUpperCase();title.append(tag);
 $('#selected-quality').textContent=quality()+(lec()?'':' draft');
 $('#open-model').disabled=busy||submissionBusy||generationAttempted||modelSaving;
 $('#open-quality').disabled=submissionBusy;
 $('#character-dialog [data-slot="tein"]').disabled=isWan();
 $('#open-characters small').textContent=isWan()?'One clear character photo':'Photo or identity video · up to 2 characters';
 renderCharacterSelection();
}
function referencePresent(slot){return !removedReferences.has(slot)&&($('#seedance').elements[slot].files.length||saved[slot])}
function renderCharacterSelection(){
 const slots=['sirio','tein'].filter(slot=>referencePresent(slot)&&!(isWan()&&slot==='tein'));
 $('#open-characters').hidden=slots.length>0;$('#character-selection').hidden=slots.length===0;
 const chips=$('#character-chips');chips.replaceChildren();
 for(const slot of slots){
  const input=$('#seedance').elements[slot], file=input.files[0], stored=saved[slot];
  const card=document.createElement('div');card.className='character-chip';
  const edit=document.createElement('button');edit.type='button';edit.className='character-thumbnail';
  edit.setAttribute('aria-label','Replace character '+(slot==='sirio'?'1':'2'));edit.onclick=()=>openCharacterPicker(slot);
  const url=referenceUrls[slot]||(stored?base()+stored:null), video=file?file.type.startsWith('video/'):stored&&/\.(mp4|mov|webm)$/i.test(stored);
  if(url){const media=document.createElement(video?'video':'img');media.src=url;media.alt='Character '+(slot==='sirio'?'1':'2');if(video){media.muted=true;media.preload='metadata'}edit.append(media)}
  const label=document.createElement('span');label.textContent='Character '+(slot==='sirio'?'1':'2');edit.append(label);
  const remove=document.createElement('button');remove.type='button';remove.className='tile-remove';remove.textContent='×';
  remove.setAttribute('aria-label','Remove character '+(slot==='sirio'?'1':'2'));remove.onclick=()=>removeCharacter(slot);
  card.append(edit,remove);chips.append(card);
 }
 if(slots.length&&(slots.length<(isWan()?1:2))){const add=document.createElement('button');add.type='button';add.className='add-character';add.textContent='＋';add.setAttribute('aria-label','Add another character');add.onclick=()=>openCharacterPicker(slots.includes('sirio')?'tein':'sirio');chips.append(add)}
}
function removeCharacter(slot){
 $('#seedance').elements[slot].value='';delete saved[slot];delete referenceNames[slot];removedReferences.add(slot);
 if(referenceUrls[slot])URL.revokeObjectURL(referenceUrls[slot]);delete referenceUrls[slot];
 const img=$('#'+slot+'-img');img.removeAttribute('src');img.hidden=true;resetPlan();renderCharacterSelection();
}
function selectCharacterFile(slot,file){
 const input=$('#seedance').elements[slot], accepted=input.accept.split(',');
 if(!accepted.includes(file.type)){status('Choose a supported '+(slot==='tein'||isWan()?'character photo.':'photo or identity video.'),true);return false}
 const transfer=new DataTransfer();transfer.items.add(file);input.files=transfer.files;
 removedReferences.delete(slot);delete saved[slot];referenceNames[slot]=file.name;
 if(referenceUrls[slot])URL.revokeObjectURL(referenceUrls[slot]);referenceUrls[slot]=URL.createObjectURL(file);
 input.closest('.upload').querySelector('[data-filename]').textContent=file.name;resetPlan();renderCharacterSelection();return true;
}
for(const slot of ['sirio','tein']){
 const input=$('#seedance').elements[slot];input.onchange=()=>{const file=input.files[0];if(file&&selectCharacterFile(slot,file))$('#character-dialog').close()};
}
function openCharacterPicker(slot='sirio'){
 pickerSlot=slot==='tein'&&!isWan()?'tein':'sirio';
 document.querySelectorAll('[data-slot]').forEach(b=>{b.classList.toggle('active',b.dataset.slot===pickerSlot);b.setAttribute('aria-pressed',String(b.dataset.slot===pickerSlot))});
 $('#picker-description').textContent=pickerSlot==='tein'?'Choose a photo of a second, different person. This is not another angle of Character 1.':isWan()?'Use one clear portrait photo. Wan does not accept identity videos.':'Use a clear portrait or identity video for Character 1.';
 if(!$('#character-dialog').open)$('#character-dialog').showModal();if(pickerView==='saved')loadSavedReferences();
}
$('#open-characters').onclick=()=>openCharacterPicker();$('#manage-characters').onclick=()=>openCharacterPicker();
for(const b of document.querySelectorAll('[data-slot]'))b.onclick=()=>openCharacterPicker(b.dataset.slot);
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>$('#'+b.dataset.close).close();
$('#upload-character').onclick=()=>$('#seedance').elements[pickerSlot].click();
for(const b of document.querySelectorAll('[data-assets]'))b.onclick=()=>{
 pickerView=b.dataset.assets;document.querySelectorAll('[data-assets]').forEach(x=>x.classList.toggle('active',x===b));
 $('#asset-upload-view').hidden=pickerView!=='upload';$('#asset-saved-view').hidden=pickerView!=='saved';if(pickerView==='saved')loadSavedReferences();
};
async function loadSavedReferences(){
 const grid=$('#saved-reference-grid');grid.replaceChildren();$('#asset-library-status').textContent='Loading local characters…';
 try{const data=await json('/references');for(const item of data.references){
  const button=document.createElement('button');button.type='button';button.className='asset-item';button.disabled=item.kind==='video'&&(pickerSlot==='tein'||isWan());
  const media=document.createElement(item.kind==='video'?'video':'img');media.src=item.url;if(item.kind==='video'){media.muted=true;media.preload='metadata'}else media.alt=item.label;
  const label=document.createElement('span');label.textContent=item.label;button.append(media,label);button.onclick=async()=>{
   button.disabled=true;try{const r=await fetch(item.url);if(!r.ok)throw Error('That local reference is unavailable.');const blob=await r.blob();const file=new File([blob],item.id.split('/').pop(),{type:blob.type});if(selectCharacterFile(pickerSlot,file))$('#character-dialog').close()}catch(e){$('#asset-library-status').textContent=e.message}finally{button.disabled=false}
  };grid.append(button);
 }$('#asset-library-status').textContent=data.references.length?'Only your local job references appear here.':'No saved characters yet. Upload a reference; it is saved when you prepare or generate.'}
 catch(e){$('#asset-library-status').textContent=e.message}
}
for(const [zone,action] of [[$('#upload-character'),files=>{if(files[0]&&selectCharacterFile(pickerSlot,files[0]))$('#character-dialog').close()}],[$('.source-upload'),files=>{if(!files[0]?.type.startsWith('video/')){status('Choose a video file.',true);return}const transfer=new DataTransfer();transfer.items.add(files[0]);const input=$('#form').elements.video;input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}))}]]){
 zone.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over')});zone.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
 zone.addEventListener('drop',e=>{e.preventDefault();zone.classList.remove('drag-over');action(e.dataTransfer.files)});
}
const sourceInput=$('#form').elements.video, sourceHandler=sourceInput.onchange;
sourceInput.onchange=e=>{sourceHandler(e);$('.source-upload').classList.toggle('has-source',sourceInput.files.length>0);$('#clear-source').hidden=!sourceInput.files.length;syncComposerControls();};
$('#clear-source').onclick=()=>{sourceInput.value='';$('.source-upload').classList.remove('has-source');$('.source-upload [data-filename]').textContent='Video duration: 4 to 30 seconds';$('#clear-source').hidden=true;$('#local-source-info').hidden=true;if(localSourceUrl){URL.revokeObjectURL(localSourceUrl);localSourceUrl=null}if(jobId)refresh();else{$('#input-video').removeAttribute('src');$('#input-ready').hidden=true;$('#input-empty').hidden=false}resetPlan();syncComposerControls()};
function renderModelOptions(){
 const grid=$('#model-options'),query=$('#model-search').value.toLowerCase();grid.replaceChildren();
 for(const c of modelChoices.filter(c=>(c.title+' '+c.tag).toLowerCase().includes(query))){
  const button=document.createElement('button');button.type='button';button.className='model-option';
  const active=c.provider===provider()&&c.engine===$('#generation-engine').value;button.classList.toggle('selected',active);
  button.disabled=busy||submissionBusy||generationAttempted||modelSaving||!!(jobProvider&&jobProvider!==c.provider);
  const icon=document.createElement('span');icon.className='model-mark';icon.textContent=c.engine==='wan'?'W':'S';
  const copy=document.createElement('span'),title=document.createElement('strong'),tag=document.createElement('em');title.textContent=c.title;tag.textContent=c.tag;title.append(tag);
  const sub=document.createElement('small');sub.textContent=c.description;const qualityText=document.createElement('small');qualityText.textContent=c.quality;copy.append(title,sub,qualityText);
  const check=document.createElement('span');check.className='model-check';check.textContent=active?'✓':'›';button.append(icon,copy,check);button.onclick=()=>chooseModel(c);grid.append(button);
 }if(!grid.children.length)grid.textContent='No matching models.';
}
async function chooseModel(choice){
 modelSaving=true;renderModelOptions();$('#model-picker-status').textContent='Selecting model…';
 try{if(choice.provider!==provider()){
  const data=new FormData();data.set('provider',choice.provider);data.set('storage_repo',configuration.oxen_storage_repo||'');
  await json('/configuration/settings',{method:'POST',body:data});configuration=await json('/configuration');
 }$('#generation-engine').value=choice.engine;$('#generation-engine').dataset.loaded='true';resetPlan();showProvider();showEngine();$('#model-dialog').close();status(choice.title+' via '+choice.tag+' selected. No generation was submitted.')}
 catch(e){$('#model-picker-status').textContent=e.message}finally{modelSaving=false;syncComposerControls();renderModelOptions()}
}
$('#open-model').onclick=()=>{$('#model-search').value='';$('#model-picker-status').textContent=jobProvider?'This saved job keeps its provider. Start a new video to use another provider.':'';renderModelOptions();$('#model-dialog').showModal()};
$('#model-search').oninput=renderModelOptions;$('#model-api-settings').onclick=()=>$('#open-settings').click();
$('#open-quality').onclick=()=>{
 $('#current-quality').textContent=quality()+(lec()?' generation':' draft')+'  ✓';$('#future-quality').textContent=lec()?'720p · current output':provider()==='replicate'?'720p · new generation':'1080p · final render';$('.future-quality').hidden=lec();
 $('#quality-description').textContent='This adapter starts at '+quality()+'. '+(lec()?'Lec has no separate HD step.':'Generate and review a draft first. The Results tab offers the supported higher-resolution render with separate billing.');$('#quality-dialog').showModal();
};$('#current-quality').onclick=()=>$('#quality-dialog').close();
