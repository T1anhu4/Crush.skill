"""Conservative local safeguards, not a semantic truth or hallucination detector."""
import re
from .provider import ProviderError

DRINK=r'(?:乌龙茶|红茶|绿茶|奶茶|咖啡|普洱|白茶|花茶)'
PREFERENCE=re.compile(rf'我(?:现在)?(?:不喝{DRINK}了[，,]?|不再喝{DRINK}[，,]?)?(?:喜欢|爱喝|改喝){DRINK}[。.!！]?')


def preference_topic(text):
    # Only unambiguous first-person assertions; no questions, quotes or guesses.
    return 'explicit:drink_preference' if PREFERENCE.fullmatch(text.strip()) else None


class GroundingError(ProviderError):
    def __init__(self,message):
        super().__init__(message,'grounding')


def validate_grounding(result,context):
    if context['session']['mode']!='live':
        return
    update=result.get('life_update')
    if update is not None:
        if not context.get('allow_life_update') or not isinstance(update,dict):
            raise GroundingError('生活事实更新不符合当前时间条件，请重试。')
        if not isinstance(update.get('text'),str) or not 1<=len(update['text'].strip())<=240 or not isinstance(update.get('thread'),str) or not 1<=len(update['thread'].strip())<=60:
            raise GroundingError('生活事实格式无效，请重试。')
    facts=[row['text'] for row in context.get('world',[])]
    facts+=context['character'].get('opening',[])
    if update:
        facts.append(update['text'])
    # Do not use previous generated replies as evidence: a hallucination must
    # not certify itself on the following turn. These checks deliberately cover
    # only explicit past-experience constructions seen in regression fixtures.
    for message in result['messages']:
        evidence='\n'.join([r['content'] for r in context.get('recent',[]) if r['role']=='user']+[m['text'] for m in context.get('memories',[])])
        recalling=bool(re.search(r'记得|记忆|你(?:说|喜欢|爱喝|自己改)',message))
        for name in re.findall(r'正山小种|金骏眉|祁门红茶|大吉岭|伯爵茶|铁观音|龙井|碧螺春',message):
            if recalling and name not in evidence and not re.search(r'你.*(?:试试|尝尝)|推荐|我喜欢',message):
                raise GroundingError('不能把角色推荐的品种当成用户明确表达的偏好。仅依据用户原话回答。')
        for sentence in re.split(r'[。！？!?\n]',message):
            if re.search(r'(?:现在|这会儿|已经|正是).{0,5}(?:春天|夏天|秋天|冬天)|(?:春天|夏天|秋天|冬天).{0,4}(?:快|正|到了|收尾)',sentence):
                if not re.search(r'去年|前年|那年|如果|假如|到时候',sentence) and not any(sentence.strip() in fact for fact in facts):
                    raise GroundingError('没有当前季节或天气的事实来源，不要从叶子、云或月份推断季节。')
        if context['session'].get('relationship_day',1)>=14 and re.search(r'认识(?:才|只有|就)几天',message):
            raise GroundingError('回复中的相识时间与记录不一致，请重试。')
        for sentence in re.split(r'[。！？!?\n]',message):
            if not re.search(r'我(?:以前|后来|今天|昨天|下午|上午|早上|晚上)[^。！？!?]{0,50}(?:捡到|捡了|夹过|买了|去了|喝完|辞职了)',sentence):
                continue
            if re.search(r'如果|假如|要是|没|并非|不是|打算|准备|想要',sentence):
                continue
            if not any(sentence.strip() in fact for fact in facts):
                raise GroundingError('回复包含未登记的生活经历，请重试。')
