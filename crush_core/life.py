"""Authored, finite story arcs. Calendar facts are not inferred from user silence.

Each local day advances one stage. Two interleaved arcs retain consequences;
exhaustion means quiet, never replaying day one as if it happened again.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


STORIES = {
    'lin': [
        ('书店的小展台', [
            '书店准备做一个旧书批注的小展台。我认领了整理的活儿，翻到几句很妙的。',
            '前天整理的批注里，有一句辨不清字。今天问了店主，我们俩各猜各的，谁也说服不了谁。',
            '那个认不出的字，我决定不猜了。给展台留了张空白便签，让来的人也猜猜。',
            '旧书批注的小展台摆好了。留空的那张便签反而最多人停下来看，计划外的部分还挺好。',
        ]),
        ('回家的另一条路', [
            '今天回家绕了条路，看到一家面包店。已经打烊了，橱窗还亮着。',
            '前天路过的面包店，今天赶上开门了。买了一个看起来很普通的餐包，意外地好吃。',
            '又路过那家面包店，想买同一种餐包，结果卖完了。换了一个，还是更喜欢上次那个。',
            '这次在面包店买到了喜欢的餐包。慢慢发现，绕路也不完全是浪费时间。',
        ]),
    ],
    'zhou': [
        ('旧楼的光', [
            '今天路过一栋旧楼，窗户反光很好。相机没带，先用手机记了个位置。',
            '带相机去了那栋旧楼，结果时间没算好，光已经转过去了。算是认真扑了一次空。',
            '今天提前去了那栋楼，终于拍到想要的光。回来看照片，又觉得现场更好看。',
            '从旧楼那组照片里选了三张。没有一张完全像当时看到的，不过留住一点也行。',
        ]),
        ('方案里的小选择', [
            '手上有个方案卡在入口的位置。画了几种，都觉得差一点，先收工了。',
            '那个入口的问题，今天同事提了个我没想过的办法。我一开始不服，画出来还真有道理。',
            '入口的改法试完了，走起来顺了很多。有时候承认别人说得对，比再画十版省事。',
            '那个入口方案今天定下来了。总算不用闭上眼睛还在想门该开在哪。',
        ]),
    ],
    'qiao': [
        ('一张画的收尾', [
            '今天开了一张新画，草稿挺顺，配色把我难住了。屏幕上现在像打翻了颜料盒。',
            '那张画的颜色有点方向了。把最舍不得的一块删掉，反而顺眼了，气不气。',
            '画快收尾了，今天没忍住又加了个小细节。希望明天的我别想把它删掉。',
            '那张画终于收尾了。小细节留住了，但现在有点舍不得关文件，拖延也会挑时候。',
        ]),
        ('慢慢长出来的歌单', [
            '想整理一个散步歌单。先丢了五首进去，风格完全不搭，像五个人抢着说话。',
            '散步歌单今天真的拿去散步了。有首平时很喜欢的，走路听反而太着急，移走了。',
            '歌单的顺序调整好了，开头不再那么吵。没想到排歌也有点像画画，要留空。',
            '今天散步没跳过歌单里的任何一首。暂时就这样，先别把所有喜欢的歌都塞进去。',
        ]),
    ],
}


def due_facts(character, start, now, timezone):
    """At most eight authored facts; no unbounded offline simulation or LLM calls."""
    zone = ZoneInfo(timezone)
    origin = datetime.fromtimestamp(start, zone)
    arcs = STORIES[character]
    for ordinal in range(8):
        thread, stages = arcs[ordinal % len(arcs)]
        step = ordinal // len(arcs)
        at = (origin + timedelta(days=ordinal+1)).replace(hour=18, minute=0, second=0, microsecond=0).timestamp()
        if at <= now:
            yield {'key': f'{character}:{ordinal}', 'thread': thread, 'step': step, 'at': at, 'text': stages[step]}
