import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';

const source=readFileSync(new URL('../src/waiting.ts',import.meta.url),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {waitingText}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));

test('technical activity is not presented as character thinking',()=>{
  assert.match(waitingText({status:'generating'},'live',0),/模型请求中/);
  assert.match(waitingText({status:'error'},'live',0),/失败/);
});
test('waiting preserves reason without a countdown',()=>{
  for(const [reason,expected] of [['first_contact','首次'],['busy','忙碌'],['sleep','休息'],['character_delay','稍后'],['paused','暂停']]){
    const text=waitingText({status:'queued',reason,due:180},'live',0);
    assert.ok(text.includes(expected));
    assert.doesNotMatch(text,/180|秒|倒计时/);
  }
});
test('overdue queue is not represented as intentional silence',()=>{
  assert.match(waitingText({status:'queued',reason:'busy',due:10},'live',101),/超出预期/);
  assert.match(waitingText({status:'queued',reason:'paused',due:10},'live',101),/暂停/);
});
test('demo generation never says it is requesting a model',()=>{
  assert.doesNotMatch(waitingText({status:'generating'},'demo',0),/模型请求中/);
});
